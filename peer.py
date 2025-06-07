import random
import time

class Peer:
    def __init__(self, id):
        self.id = id # Variável que armazena um valor de identificação para o peer
        self.blocos = [] # Lista que armazena os blocos que o peer possui
        self.conexoes = [] # Lista que mostra as conexões atuais do peer
        self.pedidos = [] # Pedidos que foram solicitados, mas ainda não foram respondidos, para que não haja mais pedidos do mesmo bloco
        self.correio = {'mensagem': []} # Correio de mensagens recebidas
        self.arquivo_incompleto = True # Variável que diz se arquivo está ou não completo
        self.receptor_ativo = True # Variável que diz se o receptor de mensagens continua ou não ativo
    
    # Função que analisa a matriz de conexões e define quais são os outros peers que estão conectados com a instância atual
    def definir_conexoes(self, conexoes):
        for i in range(len(conexoes)):
            no_rede = conexoes[self.id-1][i] # Verifica cada elemento da linha correspondente ao peer
            if no_rede == 1:
                self.conexoes.append(i+1)

    # Função que alimenta o conjunto de estoques com o estoque do peer em questão
    def envia_estoque(self, estoque):
        estoque[f'{self.id}'] = self.blocos

    #Função que recebe os estoques de outros peers e retorna os blocos que eles possuem e estão faltando para completar o arquivo
    def recebe_estoques(self, estoques):
        blocos_faltando = [] # Lista que guarda os blocos que restam para completar o arquivo

        for peer_id, blocos in estoques.items():
            if peer_id == self.id:
                continue

            for bloco in blocos:
                if bloco not in self.blocos and bloco not in self.pedidos: # Verifica se já possui o bloco ou se já solicitou o bloco
                    blocos_faltando.append((peer_id, bloco))

        if blocos_faltando:
            return random.choice(blocos_faltando) # Retorna um bloco aleatório que está faltando para completar o arquivo
        return None
    
    # Função que solicita um bloco específico que pertence a um peer específico
    def solicita_bloco(self, peer_alvo, bloco_solicitado):
        print(f"Bloco desejado pelo peer {self.id}: Bloco '{bloco_solicitado}' do peer {peer_alvo.id}\n")
        self.pedidos.append(bloco_solicitado) # Registra o bloco solicitado em pedidos
        self.enviar_mensagem(peer_alvo, f"PEDIDO|{str(bloco_solicitado)}") # Chama a função que envia a mensagem do tipo 'PEDIDO'
    
    # Função que realiza o envio de uma mensagem de um peer para o outro
    def enviar_mensagem(self, receptor, mensagem):
        print(f"Mensagem do peer {self.id} para o peer {receptor.id}: {mensagem}")
        receptor.correio["mensagem"].append((self, mensagem)) # Insere mensagem no correio do receptor da mensagem
        print(f"Correio do peer {receptor.id}: {[mensagens[1] for mensagens in receptor.correio['mensagem']]}\n")
    
    # Função que executa a recepção de mensagens que estão no correio do peer
    def receber_mensagem(self):
        while self.receptor_ativo: # Aguarda o receptor ser desativado
            time.sleep(0.01)

            if self.correio["mensagem"]:
                print(f"Peer {self.id} está verificando suas mensagens\n")
                
                for peer, mensagem in self.correio["mensagem"]: # Realiza a leitura de todas as mensagens que estão no correio naquela ocasião
                    
                    if "PEDIDO" in mensagem: # Mensagens de pedido de bloco
                        pedido = mensagem.split("PEDIDO|")[1] # O bloco que foi solicitado
                        if int(pedido) in self.blocos: # Verifica se possui o bloco
                            print(f"Peer {self.id} recebeu o pedido do bloco {pedido} pelo peer {peer.id}")
                            self.enviar_mensagem(peer, f"ENVIO|{pedido}") # Envia o bloco
                    
                    elif "ENVIO" in mensagem: # Mensagens de envio de bloco
                        envio = mensagem.split("ENVIO|")[1] # O bloco que foi enviado
                        self.blocos.append(int(envio)) # Adquire o bloco
                        self.pedidos.remove(int(envio)) # Remove o bloco da lista de pedidos
                        print(f"Peer {self.id} recebeu o bloco {envio} do peer {peer.id}")
                        print(f"Blocos atuais do peer {self.id}: {self.blocos}\n")
                    
                    self.correio["mensagem"].remove((peer,mensagem)) # Remove a mensagem lida do correio