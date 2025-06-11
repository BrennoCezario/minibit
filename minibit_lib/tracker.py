import os
import json
import socket
import threading
import random
from .divisao_blocos import DivisaoBlocos
from.peer import Peer

TRACKER_IP = "localhost"
TRACKER_PORTA = 8000

BLOCOS_INICIAIS = 4

class Tracker(Peer(0)):
    def __init__(self):
        self.peers = {}
        self.lock = threading.Lock()
        
    def fornecer_blocos(self, conexao):
        blocos_fornecidos = random.sample(self.blocos, BLOCOS_INICIAIS)
        tamanho = {
            "tipo": "TAMANHO",
            "tamanho": len(str(blocos_fornecidos)),
        }
        
        conexao.send(json.dumps(tamanho).encode())
        
        blocos = {
            "tipo": "BLOCOS",
            "blocos": blocos_fornecidos,
        }
        
        conexao.send(json.dumps(blocos).encode())
        
    def tratar_peer(self, conexao, endereco):
        try:
            mensagem_recebida = conexao.recv(1024).decode()
            dados_mensagem = json.loads(mensagem_recebida)

            if dados_mensagem['tipo'] == "REGISTRO" :
                
                with self.lock:
                    self.peers[dados_mensagem['peer_id']] = {
                        "id": dados_mensagem['peer_id'],
                        "conexoes": dados_mensagem['conexoes'],
                        "ip": endereco[0],
                        "porta": endereco[1],
                        "receptor_ativo": dados_mensagem['receptor_ativo'],
                        "arquivo_completo": dados_mensagem['arquivo_completo']
                    }
                    
            # peer_adicionado = list(self.peers.values())[-1]
            
            self.fornecer_blocos(conexao)

        finally:
            conexao.close()
    
    def iniciar_tracker(self):
        servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        servidor.bind((TRACKER_IP, TRACKER_PORTA))
        servidor.listen()
        print(f'Tracker está ativo em {TRACKER_IP}:{TRACKER_PORTA}\n')

        while True:
            conexao, endereco = servidor.accept()
            threading.Thread(target=self.tratar_peer, args=(conexao,endereco)).start()

if __name__ == "__main__":
    os.system("cls" if os.name == "nt" else "clear")
    
    arquivo = "logo_uerj.png"
    
    dividir_arquivo = DivisaoBlocos(arquivo)
    dividir_arquivo.rodar()
    
    tracker = Tracker()

    with open("blocos.json", 'r', encoding='utf-8') as f:
        tracker.blocos = json.load(f)
    
    print(f"\nBlocos: {[bloco[:10] + '...' for bloco in tracker.blocos]}\n")
    
    tracker.iniciar_tracker()