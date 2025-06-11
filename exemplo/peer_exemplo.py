import socket
import argparse
import json
import threading
from minibit_lib.peer import Peer

TRACKER_IP = "localhost"
TRACKER_PORTA = 8000

def obter_blocos(conexao_tracker, peer):
    tamanho_mensagem = 1024
    while True:
        mensagem_recebida = conexao_tracker.recv(tamanho_mensagem).decode()
        if mensagem_recebida:
            dados_mensagem = json.loads(mensagem_recebida)
            
            if dados_mensagem["tipo"] == "TAMANHO":
                tamanho_mensagem = dados_mensagem["tamanho"]
            
            elif dados_mensagem["tipo"] == "BLOCOS":
                peer.blocos = dados_mensagem["blocos"]
                
                print(f"Blocos iniciais do peer {peer.id}: {[bloco[:5]+'...' for bloco in peer.blocos]}")
                break

def conectar_tracker(peer):
    servidor_tracker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor_tracker.connect((TRACKER_IP, TRACKER_PORTA))
    
    mensagem_inicial = {
        "tipo": "REGISTRO",
        "peer_id": peer.id,
        "conexoes": peer.conexoes,
        "receptor_ativo": peer.receptor_ativo,
        "arquivo_completo": peer.arquivo_completo
    }
    
    servidor_tracker.send(json.dumps(mensagem_inicial).encode())
    
    return servidor_tracker


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', type=int, required=True)
    args = parser.parse_args()

    peer_id = args.id
    peer = Peer(peer_id)
    
    thread_receptora = threading.Thread(target=peer.receber_mensagem)

    conexao_tracker = conectar_tracker(peer)
    obter_blocos(conexao_tracker, peer)
    