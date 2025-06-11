import socket
import threading
import pickle
import json
import random
import os
from .divisao_blocos import DivisaoBlocos

TOTAL_BLOCOS = 10
BLOCOS_INICIAIS = 2
TRACKER_HOST = 'localhost'
TRACKER_PORT = 8000
peers = {}

class Tracker:
    def __init__(self, host=TRACKER_HOST, port=TRACKER_PORT):
        self.host = host
        self.port = port
        self.peers = {}  # { (ip, port) : [blocos] }
        self.lock = threading.Lock()
        self.numero_blocos = 0

    def handle_peer(self, connection, address):
        try:
            data = connection.recv(1024).decode()
            request = json.loads(data)

            if request['type'] == 'register':
                with self.lock:
                    self.peers[(request['host'], request['port'])] = request['blocks']

            peer_id = request['peer_id']
            peer_port = request['port']
            blocos = random.sample(range(TOTAL_BLOCOS), BLOCOS_INICIAIS)

            peers[peer_id] = {
            'peer_id': peer_id,
            'port': peer_port,
            'blocos': set(blocos)
            }
        
            outros_peers = [
            {'peer_id': pid, 'port': info['port']}
            for pid, info in peers.items() if pid != peer_id
            ]

            if len(outros_peers) > 5:
                outros_peers = random.sample(outros_peers, 5)

                response = {
                    'blocos_iniciais': blocos,
                    'peers_disponiveis': outros_peers
                }

            connection.send(json.dumps(response).encode())

        finally:
            connection.close()

    def iniciar_tracker(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((TRACKER_HOST, TRACKER_PORT))
        server.listen()
        print(f'Tracker está ativo em {TRACKER_HOST}:{TRACKER_PORT}')

        while True:
            connection, address = server.accept()
            threading.Thread(target=self.handle_peer, args=(connection,address)).start()
    

if __name__ == "__main__":
    os.system("cls" if os.name == "nt" else "clear")
    
    arquivo = "logo_uerj.png"
    
    dividir_arquivo = DivisaoBlocos(arquivo)
    dividir_arquivo.rodar()
    
    tracker = Tracker()

    with open("metadata.json", 'r', encoding='utf-8') as f:
        metadata = json.load(f)
        tracker.numero_blocos = len(metadata['hash_blocos'])
    
    print(f"Número de Blocos: {tracker.numero_blocos}")
    
    tracker.iniciar_tracker()