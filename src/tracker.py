import os
import socket
import threading
import time
import random
import json
import base64
from .divisao_blocos import DivisaoBlocos
from .peer import Peer

TRACKER_PORTA = 8000

class Tracker(Peer):
    def __init__(self):
        super().__init__(id=0)
        
    def fornecer_blocos(self, conexao, peer_id):
        blocos_por_peer = (len(self.blocos) // 4) + 1
        blocos_fornecidos = random.sample(self.indices, blocos_por_peer)
        
        for indice in blocos_fornecidos:
            mensagem = {
            "tipo": "PEDIDO",
            "id": peer_id,
            "bloco": indice
            }
            self.correio.append((conexao, json.dumps(mensagem)))
                
            
        print(f"{len(blocos_fornecidos)} Blocos enviados para o peer {peer_id} ")
    
    def dividir_arquivo(self, arquivo):
        dividir_arquivo = DivisaoBlocos(arquivo)
        dividir_arquivo.rodar()

        with open("blocos.json", 'r', encoding='utf-8') as f:
            self.blocos = json.load(f)
        
        for indice in range(len(self.blocos)):
            self.blocos[indice] = (indice+1, self.blocos[indice])
            self.indices.append(indice+1)
        
        print(f"\n{len(tracker.blocos)} Blocos: {[bloco[1][:5] + '...' for bloco in tracker.blocos]}\n")

if __name__ == "__main__":
    os.system("cls" if os.name == "nt" else "clear")
    
    arquivo = "video.mp4"
    
    tracker = Tracker()

    tracker.dividir_arquivo(arquivo)

    threading.Thread(target=tracker.processar_mensagens).start()
    
    tracker.iniciar_servidor(TRACKER_PORTA)