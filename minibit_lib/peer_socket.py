import random
import socket
import json
import threading
import time
import struct
import os
from .divisao_blocos import DivisaoBlocos
from .construcao_arquivo import ConstruirArquivo


TRACKER_HOST = 'localhost'
TRACKER_PORT = 8000

class Peer:
    def __init__(self, host, port, tracker_host, tracker_port, metadata, blocos):
        self.host = host
        self.port = port
        self.tracker_host = tracker_host
        self.tracker_port = tracker_port
        self.metadata = metadata
        self.total_blocos = metadata['numero_blocos']
        self.hashes = metadata['hash_blocos']
        self.blocos = {}

        blocos_indices = random.sample(range(self.total_blocos), k=max(1, self.total_blocos // 2))
        for indice in blocos_indices:
            self.blocos[indice] = blocos[indice]
        self.peers = []
        # Garante que o server vai rodar até completar
        self.server_running = True 
    def start(self):
        server_thread = threading.Thread(target=self.peer_server)
        server_thread.start()
        # Espera o server subir
        time.sleep(1)
        self.conect_to_tracker()
        self.start_download()

    def conect_to_tracker(self):
        tracker_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tracker_server.connect((self.tracker_host, self.tracker_port))

        msg = {
            'type': 'register',
            'host': self.host,
            'port': self.port,
            'blocos': list(self.blocos.keys())
        }
        tracker_server.send(json.dumps(msg).encode())

        response = json.loads(tracker_server.recv(4096).decode())
        if response['type'] == 'peers_list':
            self.peers = response['peers']
            print(f"Recebido peers: {self.peers}")

        tracker_server.close()

    def peer_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.host, self.port))
        # Checa a flag de encerramento
        server.settimeout(2)
        server.listen()

        while self.server_running:
            try:
                conn, address = server.accept()
                threading.Thread(target=self.handle_solicitacao, args=(conn,address)).start()
            except socket.timeout:
                continue

        server.close()


    def handle_solicitacao(self, conn):
        try:
            data = conn.recv(1024).decode()
            request = json.loads(data)

            if request['type'] == 'request_block':
                indice = request['indice']
                bloco = self.blocos.get(indice)
                response = {'type': 'block_data', 'indice': indice, 'data': bloco} if bloco else {'type': 'block_data', 'indice': indice, 'data': None}

                conn.send(json.dumps(response).encode())
        finally:
            conn.close()

    def request_block(self, peer_host, peer_port, indice):
    
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.connect((peer_host, peer_port))
            request = {'type': 'request_block', 'indice': indice}
            server.send(json.dumps(request).encode())

            data = server.recv(1024).decode()
            response = json.loads(data)
            server.close()
            
            return response.get('data')
        
        except:
            return None
    
    def start_download(self):
        while len(self.blocos) < self.total_blocos:
            faltando = [i for i in range(self.total_blocos) if i not in self.blocos]
            random.shuffle(faltando)

            for index in faltando:
                for peer in self.peers:
                    bloco = self.solicitar_bloco(peer['host'], peer['port'], index)
                    if bloco:
                        self.blocos[index] = bloco
                        print(f"Recebeu bloco {index} de {peer['host']}:{peer['port']}")
                        break
                else:
                    print(f"Bloco {index} não encontrado em nenhum peer.")
            
            # Aguarda antes de tentar novamente
            time.sleep(2)  

        # Reconstruir o arquivo
        blocos_ordenados = [self.blocos[i] for i in range(self.total_blocos)]
        output = f"arquivo_reconstruido_{self.port}{self.metadata['extensao']}"
        construtor = ConstruirArquivo()
        construtor.construir_arquivo(blocos_ordenados, output)

        if construtor.verifica_construcao(self.hashes, blocos_ordenados):
            print(f"Peer {self.port}: Arquivo reconstruído com sucesso!")
        else:
            print(f"Peer {self.port}: Erro na verificação do arquivo.")

if __name__ == '__main__':
    with open('metadata.json', 'r') as f:
        metadata = json.load(f)

    with open('blocos.json', 'r') as f:
        blocos = json.load(f)

    peer = Peer(
        host='localhost',
        port=random.randint(6000, 7000),
        tracker_host='localhost',
        tracker_port=8000,
        metadata=metadata,
        blocos=blocos
    )

    peer.start()
