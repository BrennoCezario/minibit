import socket
import threading
import time
import logging
import os
import json
import random

IP = '127.0.0.1'

TRACKER_PORTA = 8000

PORTA_BASE = 9000

class Peer:
    
    def __init__(self, id):
        self.id = id # ID do peer (int)
        self.blocos = []  # Lista que armazena os blocos que o peer possui ((indice, bloco))
        self.indices = [] # Lista que mostra os indices dos blocos possuídos
        self.conectados = [PORTA_BASE]
        self.receptor_ativo = False # Indica se o processamento de mensagens continua ou é encerrado
        self.pedidos = [] # Pedidos que o peer já fez e ainda não foram recebidos
        self.correio = [] # Fila de mensagens recebidas de outros peers
        self.top4 = [] # Peers com quem há troca de blocos
        self.estoques = [] # Estoque de blocos de todos os peers da rede
        self.lock = threading.Lock()
        self.tracker_conexao = 0
        self.peers = {} # Lista de todos os peers da rede
        self.arquivo_completo = False
        
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
        
        self.receptor_ativo = True # Inicia receptor de conexões e mensagens
        threading.Thread(target=self.processar_mensagens).start()
        
        threading.Thread(target=self.enviar_estoque).start()
        
        self.porta = servidor.getsockname()[1]
        print(f"{'Tracker' if self.id == 0 else 'Peer ' + str(self.id)} está ativo em {IP}:{self.porta}\n")
        
        while True:
            conexao, endereco = servidor.accept()
            threading.Thread(target=self.tratar_peer, args=(conexao,)).start()
            
    def tratar_peer(self, conexao):
        while True:
            time.sleep(0.2)
            mensagem = conexao.recv(4096)
            if mensagem:
                self.correio.append((conexao, mensagem.decode()))
                
    def conectar_servidor(self, porta):
        servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        servidor.connect((IP, porta))
        
        self.conectados.append(porta) if porta != TRACKER_PORTA else None
        
        mensagem_inicial = {
            "tipo": "REGISTRO",
            "id": self.id
        }
    
        servidor.send(json.dumps(mensagem_inicial).encode())
        
        threading.Thread(target=self.tratar_peer, args=(servidor,)).start()
        
        return servidor

    def processar_mensagens(self):
        while self.receptor_ativo: # Aguarda o receptor ser desativado
            time.sleep(0.2)
            
            mensagens_para_processar = []
            with self.lock:
                if self.correio:
                    mensagens_para_processar = list(self.correio)
                    self.correio.clear()

            if mensagens_para_processar:
                self.log(f"Verificando suas mensagens: {[str(mensagem) + '...' for conn, mensagem in mensagens_para_processar]}")
                
                for conexao, mensagem in mensagens_para_processar:
                    try:
                        mensagem = json.loads(mensagem)
                        match mensagem.get("tipo"):
                            
                            case "REGISTRO":
                                peer_id = mensagem.get("id")
                                peer_ip = conexao.getpeername()[0]
                                peer_porta = PORTA_BASE + peer_id
                                peer_conexao = conexao
                                
                                if peer_porta == PORTA_BASE:
                                    peer_conexao = self.tracker_conexao
                                
                                with self.lock:
                                    self.peers[peer_id] = {
                                        "endereco": (peer_ip, peer_porta),
                                        "conexao": peer_conexao
                                    }
                                
                                print(f"Peer {peer_id} registrado! Endereço: {peer_ip}:{peer_porta}")
                                
                                # self.fornecer_blocos(conexao, peer_id) if self.id == 0 else None
                                
                                self.conectar_servidor(peer_porta) if peer_porta not in self.conectados else None
                                
                            case "ESTOQUE":
                                peer_id = mensagem.get("id")
                                peer_estoque = mensagem.get("estoque")
                                
                                if not (peer_id, peer_estoque) in self.estoques:
                                    with self.lock:
                                        self.estoques.append((peer_id, list(peer_estoque)))
                                else:
                                    for estoque in self.estoques:
                                        if estoque[0] == peer_id:
                                            with self.lock:
                                                estoque = (peer_id, peer_estoque)
                                                break
                                        
                                self.log(f"Estoque do peer {peer_id} recebido") 
                                
                            case "PEDIDO":
                                peer_id = mensagem.get("id")
                                bloco_solicitado = mensagem.get("bloco")
                                
                                if bloco_solicitado in self.indices:
                                    for indice, bloco in self.blocos:
                                        if indice == bloco_solicitado:
                                            self.enviar_bloco(peer_id, indice, bloco)
                                    
                            case "BLOCO":
                                peer_id = mensagem.get("id")
                                indice_bloco = mensagem.get("indice")
                                bloco_recebido = mensagem.get("bloco")
                                
                                self.log(f"Bloco {indice_bloco} recebido do peer {peer_id}")
                                self.blocos.append((indice_bloco, bloco_recebido))
                                self.indices.append(indice_bloco)
                                                              
                            case "ATUALIZAR":
                                return
                                
                    except Exception as e:
                        print(f"Erro ao processar mensagem: {e}")
                        
    def enviar_estoque(self):
        while True:
            time.sleep(3)
            for peer_id, dados in self.peers.items():
                conexao = dados["conexao"]
                mensagem = {
                    "tipo": "ESTOQUE",
                    "id": self.id,
                    "estoque": self.indices
                }
                conexao.send(json.dumps(mensagem).encode())
            
    def receber_estoques(self):
        blocos_faltando = [] # Lista que guarda os blocos que restam para completar o arquivo

        with self.lock:
            blocos_pendentes = [p[1] for p in self.pedidos]
            for peer_id, blocos in self.estoques:
                if  peer_id in self.peers:
                    for bloco in blocos:
                        if bloco not in self.blocos and bloco not in blocos_pendentes: # Verifica se já possui o bloco ou se já solicitou o bloco
                            blocos_faltando.append((peer_id, bloco))

        if blocos_faltando:
            return random.choice(blocos_faltando) # Retorna um bloco aleatório que está faltando para completar o arquivo
        self.arquivo_completo = True
        return None
    
    
    def solicitar_bloco(self, peer_alvo, bloco):
        self.log(f"Solicitando bloco ao peer {peer_alvo}")
        with self.lock:
            self.pedidos.append((peer_alvo, bloco)) # Registra o bloco solicitado em pedidos
        mensagem = {
            "tipo": "PEDIDO",
            "id": self.id,
            "bloco": bloco
        }
        conexao = self.peers[peer_alvo]["conexao"]
        conexao.send(json.dumps(mensagem).encode())
        self.log(f"Peer {self.id} solicitou o bloco {bloco} ao peer {peer_alvo} ")
        
    def enviar_bloco(self, peer_alvo, indice, bloco):
        mensagem = {
            "tipo": "BLOCO",
            "id": self.id,
            "indice": indice,
            "bloco": bloco
        }
        
        conexao = self.peers[peer_alvo]["conexao"]
        conexao.send(json.dumps(mensagem).encode())
        self.log(f"Bloco {indice} enviado para o peer {peer_alvo}")
        