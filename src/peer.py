import socket
import threading
import time
import logging
import os
import json
import random
from collections import Counter

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
        self.fornecedor_ativo = False
        self.pedidos = [] # Pedidos que o peer já fez e ainda não foram recebidos
        self.correio = [] # Fila de mensagens recebidas de outros peers
        self.top4 = [] # Peers com quem há troca de blocos
        self.estoques = {} # Estoque de blocos de todos os peers da rede
        self.lock = threading.Lock()
        self.tracker_conexao = 0
        self.peers = {} # Lista de todos os peers da rede
        self.arquivo_completo = False
        self.mensagens_enviadas = 0
        
        # Configurando Logger que irá gerar os logs
        self.logger = logging.getLogger(f"Peer_{self.id}")
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.FileHandler(os.path.join("logs", f"peer_{self.id}.log"), mode='w')
            formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def short(self, value, length=8):
        """
        funcao para encurtar o log dos blocos, já que ao printar os bytes dos blocos, eles sao GIGANTES
        """
        if isinstance(value, str) and len(value) > length:
            return value[:length] + "..."
        return value
   
    def log(self, mensagem):
        """
        Função que gera os logs do peer   
        """        
        if isinstance(mensagem, dict):
            msg = {}
            for k, v in mensagem.items():
                if k in ("bloco", "blocos", "estoque"):
                    if isinstance(v, list):
                        msg[k] = [self.short(b) for b in v]
                    else:
                        msg[k] = self.short(v)
                else:
                    msg[k] = v
            self.logger.info(json.dumps(msg, ensure_ascii=False))
        else:
            self.logger.info(mensagem)
    
    def iniciar_servidor(self, porta):
        servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        servidor.bind((IP, porta))
        servidor.listen()
        
        self.receptor_ativo = True # Inicia receptor de conexões e mensagens
        threading.Thread(target=self.processar_mensagens).start()
        
        self.fornecedor_ativo = True
        threading.Thread(target=self.enviar_estoque).start()
        
        self.porta = servidor.getsockname()[1]
        print(f"{'Tracker' if self.id == 0 else 'Peer ' + str(self.id)} está ativo em {IP}:{self.porta}\n")
        
        while True:
            conexao, endereco = servidor.accept()
            threading.Thread(target=self.tratar_peer, args=(conexao,)).start()
            
    def tratar_peer(self, conexao):
        buffer = ""
        while True:
            time.sleep(0.2)
            mensagem = conexao.recv(4096)
            if not mensagem:
                print("not mensagem teste tratar peer")
                break
            buffer += mensagem.decode()
            # print("conteudo buffer:", buffer)
            while '\n' in buffer:
                mensagem, buffer = buffer.split('\n', 1)
                if mensagem.strip():
                    self.correio.append((conexao, mensagem))
                
    def conectar_servidor(self, porta):
        servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        servidor.connect((IP, porta))
        
        self.conectados.append(porta) if porta != TRACKER_PORTA else None
        
        mensagem_inicial = {
            "tipo": "REGISTRO",
            "id": self.id
        }
    
        servidor.send((json.dumps(mensagem_inicial) + "\n").encode())
        self.mensagens_enviadas += 1
        
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
                self.log(f"Verificando suas mensagens: {[str(mensagem[:28]) + '...' for conn, mensagem in mensagens_para_processar]}")
                
                curtas_msgs = []

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
                                
                                self.log(f"Peer {peer_id} registrado! Endereço: {peer_ip}:{peer_porta}")
                                
                                if self.id == 0:
                                    for pid, info in self.peers.items():
                                        if pid != peer_id:
                                            try:
                                                info["conexao"].send(
                                                    (json.dumps({"tipo": "NOVO_PEER", "peer": {
                                                        "id": peer_id, "ip": peer_ip, "porta": peer_porta
                                                    }}) + "\n").encode()
                                                )
                                                self.mensagens_enviadas += 1
                                            except:
                                                self.log("Erro ao notificar peer", pid)
                                    lista_peers = [
                                        {"id": pid, "ip": info["endereco"][0], "porta": info["endereco"][1]}
                                        for pid, info in self.peers.items() if pid != peer_id
                                    ]
                                    conexao.send((json.dumps({"tipo": "LISTA_PEERS", "peers": lista_peers}) + '\n').encode())
                                    self.mensagens_enviadas += 1
                                
                                # self.fornecer_blocos(conexao, peer_id) if self.id == 0 else None
                                
                                self.conectar_servidor(peer_porta) if peer_porta not in self.conectados else None
                                
                            case "ESTOQUE":
                                peer_id = mensagem.get("id")
                                peer_estoque = mensagem.get("estoque")

                                with self.lock:
                                    self.estoques[peer_id] = list(peer_estoque)

                                        
                                self.log(f"Estoque do peer {peer_id} recebido") 
                                
                            case "PEDIDO":
                                peer_id = mensagem.get("id")
                                bloco_solicitado = mensagem.get("bloco")
                                
                                if bloco_solicitado in self.indices:
                                    for indice, bloco in self.blocos:
                                        if indice == bloco_solicitado:
                                            self.enviar_bloco(peer_id, indice, bloco)
                                    
                            case "NOVO_PEER":
                                peer = mensagem.get("peer")
                                pid = peer["id"]
                                porta = peer["porta"]
                                if pid != self.id and pid not in self.peers:
                                    try:
                                        self.conectar_servidor(porta)
                                    except:
                                        print("Erro ao tentar se conectar com peer", pid)
                                
                            case "LISTA_PEERS":
                                for peer in mensagem.get("peers", []):
                                    pid = peer["id"]
                                    ip = peer["ip"]
                                    porta = peer["porta"]
                                    if pid != self.id and pid not in self.peers:
                                        try:
                                            self.conectar_servidor(porta)
                                        except:
                                            print("Erro ao tentar se conectar com peer", pid)

                            case "BLOCO":
                                peer_id = mensagem.get("id")
                                indice_bloco = mensagem.get("indice")
                                bloco_recebido = mensagem.get("bloco")
                                
                                self.log(f"Bloco {indice_bloco} recebido do peer {peer_id} ({self.short(bloco_recebido)})")
                                if indice_bloco not in self.indices:
                                    self.blocos.append((indice_bloco, bloco_recebido))
                                    self.indices.append(indice_bloco)
                                with self.lock:
                                    self.pedidos = [p for p in self.pedidos if p[1] != indice_bloco]
                            case "DESLIGAMENTO":
                                peer_id = mensagem.get("id")
                                self.log(f"Peer {peer_id} comunicou seu desligamento.")
                                print(f"Peer {peer_id} desligou após completar o arquivo.")

                                
                    except Exception as e:
                        print(f"Erro ao processar mensagem: {e}")
                        
    def enviar_estoque(self):
        while self.fornecedor_ativo:
            time.sleep(3)
            with self.lock:
                peers = list(self.peers.items())
            for peer_id, dados in peers:
                if peer_id == 0: # id = 0 é o tracker, então pulamos
                    continue
                conexao = dados["conexao"]
                mensagem = {
                    "tipo": "ESTOQUE",
                    "id": self.id,
                    "estoque": self.indices
                }
                try:
                    conexao.send((json.dumps(mensagem) + '\n').encode())
                    self.mensagens_enviadas += 1
                except:
                    print("Erro ao tentar enviar estoque para o peer", peer_id)
            
    def receber_estoques(self):
        blocos_faltando = [] # Lista que guarda os blocos que restam para completar o arquivo
        bloco_peers = {}
        with self.lock:
            blocos_pendentes = [p[1] for p in self.pedidos]
            for peer_id, blocos in self.estoques.items():
                if peer_id in self.peers:
                    for bloco in blocos:
                        if bloco not in self.indices and bloco not in blocos_pendentes: # Verifica se já possui o bloco ou se já solicitou o bloco
                            blocos_faltando.append(bloco)
                            if bloco not in bloco_peers:
                                bloco_peers[bloco] = []
                            bloco_peers[bloco].append(peer_id)

        # if blocos_faltando:
        #     return random.choice(blocos_faltando) # Retorna um bloco aleatório que está faltando para completar o arquivo
        if not blocos_faltando:
            self.arquivo_completo = True
            return None
        frequencia = Counter(blocos_faltando)
        minima_frequencia = min(frequencia.values())
        # aqui criamos uma lista com os blocos com a menor frequencia, os mais raros
        raros_blocos = []
        # frequencia.items() retorna pares chave e valor, em que a chave é o indice do bloco (bloco) e o valor é o count, sendo este count contando quantos peers tem aquele bloco
        for bloco, count in frequencia.items():
            if count == minima_frequencia:
                raros_blocos.append(bloco)

        r_bloco_escolhido = random.choice(raros_blocos)

        r_peer_id = bloco_peers[r_bloco_escolhido]
        r_peer_id_escolhido = random.choice(r_peer_id)
        
        self.log(f"Frequencia blocos raros: {frequencia}, blocos de menor frequencia: {raros_blocos}")

        return (r_peer_id_escolhido, r_bloco_escolhido)
        
    
    
    def solicitar_bloco(self, peer_alvo, bloco):
        self.log(f"Solicitando o bloco {bloco} ao peer {peer_alvo}")
        with self.lock:
            self.pedidos.append((peer_alvo, bloco)) # Registra o bloco solicitado em pedidos
        mensagem = {
            "tipo": "PEDIDO",
            "id": self.id,
            "bloco": bloco
        }
        conexao = self.peers[peer_alvo]["conexao"]
        conexao.send((json.dumps(mensagem) + '\n').encode())
        self.mensagens_enviadas += 1
        self.log(f"Peer {self.id} solicitou o bloco {bloco} ao peer {peer_alvo} ")
        
    def enviar_bloco(self, peer_alvo, indice, bloco):
        mensagem = {
            "tipo": "BLOCO",
            "id": self.id,
            "indice": indice,
            "bloco": bloco
        }
        
        conexao = self.peers[peer_alvo]["conexao"]
        conexao.send((json.dumps(mensagem) + '\n').encode())
        self.mensagens_enviadas += 1
        self.log(f"Bloco {indice} enviado para o peer {peer_alvo} ({self.short(bloco)})")

    def set_top_4(self):

        blocos_faltando = []  # Blocos que o peer ainda precisa
        bloco_peers = {}  # bloco → lista de peers que possuem esse bloco

        with self.lock:
            blocos_pendentes = [p[1] for p in self.pedidos]
            for peer_id, blocos in self.estoques:
                if peer_id in self.peers:
                    for bloco in blocos:
                        if bloco not in self.indices and bloco not in blocos_pendentes:
                            blocos_faltando.append(bloco)
                            bloco_peers.setdefault(bloco, []).append(peer_id)

        if not blocos_faltando:
            self.arquivo_completo = True
            return None

        # Contar frequência de cada bloco nos estoques recebidos
        frequencia = Counter(blocos_faltando)
        minima_frequencia = min(frequencia.values())

        # Selecionar os blocos mais raros
        raros_blocos = [bloco for bloco, count in frequencia.items() if count == minima_frequencia]

        # Construir peer → lista de blocos raros que ele possui
        peer_raros = {}
        for bloco in raros_blocos:
            for peer in bloco_peers[bloco]:
                peer_raros.setdefault(peer, set()).add(bloco)

        # Ordenar os peers que têm mais blocos raros
        peers_ordenados = sorted(
            peer_raros.items(),
            key=lambda item: len(item[1]),
            reverse=True
        )

        self.top4 = peers_ordenados[:4]  # Pega os 4 primeiros peers com mais blocos raros

    def encerrar_peer(self):
        self.receptor_ativo = False
        self.fornecedor_ativo = False

        # Envia mensagem de desligamento ao tracker
        if self.tracker_conexao:
            mensagem = {
                "tipo": "DESLIGAMENTO",
                "id": self.id
            }
            try:
                self.tracker_conexao.send((json.dumps(mensagem) + '\n').encode())
                self.mensagens_enviadas += 1
                self.log(f"Peer {self.id} enviou mensagem de desligamento ao tracker.")
            except:
                self.log(f"Peer {self.id} falhou ao comunicar desligamento ao tracker.")

        print(f"Peer {self.id} desligado com segurança após completar o arquivo.")
