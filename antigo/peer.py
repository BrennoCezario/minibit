import random
import time
import os
import logging
import socket
from collections import Counter
from threading import Thread, Lock

IP = '127.0.0.1'

class Peer:
    def __init__(self, id):
        self.id = id # Variável que armazena um valor de identificação para o peer
        self.blocos = [] # Lista que armazena os blocos que o peer possui
        self.conexoes = [] # Lista que mostra as conexões atuais do peer
        self.pedidos = [] # Pedidos que foram solicitados, mas ainda não foram respondidos, para que não haja mais pedidos do mesmo bloco
        self.correio = [] # Correio de mensagens recebidas
        self.arquivo_completo = False # Variável que diz se arquivo está ou não completo
        self.receptor_ativo = False # Variável que diz se o receptor de mensagens continua ou não ativo
        self.tamanho_mensagem = 4096
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
        
    def iniciar_servidor(self, porta):
        servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        servidor.bind((IP, porta))
        servidor.listen()
        print(f'Peer {self.id} está ativo em {IP}:{servidor.getsockname()[1]}\n')
        
        while True:
            conexao, endereco = servidor.accept()
            Thread(target=self.tratar_peer, args=(conexao,endereco)).start()

    def tratar_peer(self, conexao, endereco):
        try:
            while True:
                mensagem_recebida = conexao.recv(self.tamanho_mensagem).decode().split("|")
                if mensagem_recebida:
                    self.correio.append((conexao, endereco, mensagem_recebida))
        finally:
            conexao.close()
    
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
    
    # Função baseada na função RECEBE_ESTOQUES mas aqui ela retorna o bloco mais raro
    def recebe_estoques_mais_raro(self, estoques):
        blocos_faltando = []  # Lista que guarda os blocos que restam para completar o arquivo

        with self.lock:
            blocos_pendentes = [p[1] for p in self.pedidos]
            for peer_id, blocos in list(estoques.items()):
                if peer_id != self.id and int(peer_id) in self.conexoes:
                    for bloco in blocos:
                        if bloco not in self.blocos and bloco not in blocos_pendentes:  # Verifica se já possui o bloco ou se já solicitou o bloco
                            blocos_faltando.append((peer_id, bloco))

        # Logica rarest first
        frequencia = Counter(bloco for _, bloco in blocos_faltando) # Conta as ocorrencias de cada bloco

        bloco_mais_raro = min(frequencia, key=frequencia.get) # Encontra o primeiro bloco com menor frequencia, pode dar empate com outros

        if blocos_faltando:

            for bloco_faltante in blocos_faltando:
                if bloco_faltante[1] == bloco_mais_raro:
                    return bloco_faltante  # Retorna o bloco mais raro dentre os blocos do estoque e que está faltando para completar o arquivo

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
                
                for conexao, endereco, mensagem in mensagens_para_processar: # Realiza a leitura de todas as mensagens que estão no correio naquela ocasião
                    mensagem = mensagem.split("|")
                    match mensagem[0]:
                        case "REGISTRO":
                            with self.lock:
                                self.peers[endereco] = {
                                    "id": int(mensagem[1]),
                                    "conexoes": eval(mensagem[2]),
                                    "receptor_ativo": mensagem[3],
                                    "arquivo_completo": mensagem[4] 
                                }
                                    
                            peer_adicionado = self.peers[endereco]
                            
                            print(f"Peer {peer_adicionado['id']} adicionado na rede: {peer_adicionado}")

                            if peer_adicionado["receptor_ativo"]:
                                self.fornecer_blocos(conexao)

                        case "TAMANHO":
                            self.tamanho_mensagem = (int(mensagem[1]) // 1024 + 2) * 1024
                        
                        case "BLOCOS":
                            self.blocos = eval(mensagem[1])
                            print(f"Blocos iniciais do peer {self.id}: {[bloco[:5]+'...' for bloco in self.blocos]}")
                            break
                        
                        # case "PEDIDO": # Mensagens de pedido de bloco
                        #     pedido = mensagem.split("PEDIDO|")[1] # O bloco que foi solicitado
                        #     if pedido in self.blocos and peer.id in self.conexoes: # Verifica se possui o bloco e se faz parte das conexões
                        #         self.log(f"Atendendo pedido do bloco  para o peer {peer.id}")
                        #         self.enviar_mensagem(peer, f"ENVIO|{pedido}") # Envia o bloco
                        
                        # case "ENVIO": # Mensagens de envio de bloco
                        #     envio = mensagem.split("ENVIO|")[1] # O bloco que foi enviado
                        #     with self.lock:
                        #         if envio not in self.blocos:
                        #             self.blocos.append(envio) # Adquire o bloco
                        #         self.pedidos = [p for p in self.pedidos if p[1] != envio] # Remove o bloco da lista de pedidos
                        #     self.log(f"Recebeu o bloco do peer {peer.id}.")
                        
