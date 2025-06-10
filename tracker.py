import socket
import threading
import pickle
import json
import random

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

    def start_tracker(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((TRACKER_HOST, TRACKER_PORT))
        server.listen()
        print(f'Tracker running in {TRACKER_HOST}:{TRACKER_PORT}')

        while True:
            connection, address = server.accept()
            threading.Thread(target=self.handle_peer, args=(connection,address)).start()
    

if __name__ == "__main__":
    tracker = Tracker()
    tracker.start_tracker()