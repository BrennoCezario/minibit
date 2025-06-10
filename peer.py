import random
import time
import os
import logging
from threading import Lock

class Peer:
    def __init__(self, id):
        self.id = id # Variável que armazena um valor de identificação para o peer
        self.blocos = [] # Lista que armazena os blocos que o peer possui
        self.conexoes = [] # Lista que mostra as conexões atuais do peer
        self.pedidos = [] # Pedidos que foram solicitados, mas ainda não foram respondidos, para que não haja mais pedidos do mesmo bloco
        self.correio = [] # Correio de mensagens recebidas
        self.arquivo_incompleto = True # Variável que diz se arquivo está ou não completo
        self.receptor_ativo = True # Variável que diz se o receptor de mensagens continua ou não ativo
        self.lock = Lock() # Lock para evitar acessos simultâneos em variáveis compartilhadas
        
        # Configurando Logger que irá gerar os logs
        self.logger = logging.getLogger(f"Peer_{self.id}")
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.FileHandler(os.path.join("logs", f"peer_{self.id}.log"), mode='w')
            formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    # Função que gera os logs do peer      
    def log(self, mensagem):
        self.logger.info(mensagem)
    
    # Função que analisa a matriz de conexões e define quais são os outros peers que estão conectados com a instância atual
    def definir_conexoes(self, conexoes):
        self.conexoes = []
        for i in range(len(conexoes)):
            no_rede = conexoes[self.id-1][i] # Verifica cada elemento da linha correspondente ao peer
            if no_rede == 1:
                self.conexoes.append(i+1)
        self.log(f"Conexoes Atualizadas: {self.conexoes}")

    # Função que alimenta o conjunto de estoques com o estoque do peer em questão
    def envia_estoque(self, estoque):
        with self.lock:
            estoque[f'{self.id}'] = self.blocos

    #Função que recebe os estoques de outros peers e retorna os blocos que eles possuem e estão faltando para completar o arquivo
    def recebe_estoques(self, estoques):
        blocos_faltando = [] # Lista que guarda os blocos que restam para completar o arquivo

        with self.lock:
            blocos_pendentes = [p[1] for p in self.pedidos]
            for peer_id, blocos in list(estoques.items()):
                if peer_id != self.id and int(peer_id) in self.conexoes:
                    for bloco in blocos:
                        if bloco not in self.blocos and bloco not in blocos_pendentes: # Verifica se já possui o bloco ou se já solicitou o bloco
                            blocos_faltando.append((peer_id, bloco))

        if blocos_faltando:
            return random.choice(blocos_faltando) # Retorna um bloco aleatório que está faltando para completar o arquivo
        return None
    
    # Verifica se os pedidos estão expirados, caso uma conexão tenha sido desfeita
    def verifica_pedidos_expirados(self):
        with self.lock:
            self.pedidos = [
                (peer_id, bloco) for peer_id, bloco in self.pedidos
                if peer_id in self.conexoes
            ]
    
    # Função que solicita um bloco específico que pertence a um peer específico
    def solicita_bloco(self, peer_alvo, bloco_solicitado):
        self.log(f"Solicitando bloco ao peer {peer_alvo.id}")
        with self.lock:
            self.pedidos.append((peer_alvo.id, bloco_solicitado)) # Registra o bloco solicitado em pedidos
        self.enviar_mensagem(peer_alvo, f"PEDIDO|{bloco_solicitado}") # Chama a função que envia a mensagem do tipo 'PEDIDO'
    
    # Função que realiza o envio de uma mensagem de um peer para o outro
    def enviar_mensagem(self, receptor, mensagem):
        self.log(f"Enviando 'mensagem' para o peer {receptor.id}")

        with receptor.lock:
            receptor.correio.append((self, mensagem))
    
    # Função que executa a recepção de mensagens que estão no correio do peer
    def receber_mensagem(self):
        while self.receptor_ativo: # Aguarda o receptor ser desativado
            time.sleep(0.01)
            
            mensagens_para_processar = []
            with self.lock:
                if self.correio:
                    mensagens_para_processar = list(self.correio)
                    self.correio.clear()

            if mensagens_para_processar:
                self.log(f"Verificando suas mensagens: ")
                
                for peer, mensagem in mensagens_para_processar: # Realiza a leitura de todas as mensagens que estão no correio naquela ocasião
                    
                    if "PEDIDO" in mensagem: # Mensagens de pedido de bloco
                        pedido = mensagem.split("PEDIDO|")[1] # O bloco que foi solicitado
                        if pedido in self.blocos and peer.id in self.conexoes: # Verifica se possui o bloco e se faz parte das conexões
                            self.log(f"Atendendo pedido do bloco  para o peer {peer.id}")
                            self.enviar_mensagem(peer, f"ENVIO|{pedido}") # Envia o bloco
                    
                    elif "ENVIO" in mensagem: # Mensagens de envio de bloco
                        envio = mensagem.split("ENVIO|")[1] # O bloco que foi enviado
                        with self.lock:
                            if envio not in self.blocos:
                                self.blocos.append(envio) # Adquire o bloco
                            self.pedidos = [p for p in self.pedidos if p[1] != envio] # Remove o bloco da lista de pedidos
                        self.log(f"Recebeu o bloco do peer {peer.id}.")