import argparse
import threading
import time
import json
import random
import base64
from .peer import Peer

TRACKER_PORTA = 8000

PORTA_BASE = 9000

blocos_totais = 0

def obter_blocos_iniciais(peer, tracker):
    
    blocos = []
    
    with open("blocos.json", 'r', encoding='utf-8') as f:
            blocos = json.load(f)
            
    for indice in range(len(blocos)):
            blocos[indice] = (indice+1, blocos[indice])
            peer.indices.append(indice+1)
    
    global blocos_totais
    blocos_totais = len(blocos)
    
    peer.blocos = random.sample(blocos, (len(blocos) // 4) + 1)
    
    print(f"\n{len(peer.blocos)} Blocos: {[bloco[1][:5] + '...' for bloco in peer.blocos]}\n")
                 
def completar_arquivo(peer):
    peer.receptor_ativo = True
    processador_mensagens = threading.Thread(target=peer.processar_mensagens()).start()
    
    global blocos_totais
    
    while len(peer.blocos) < blocos_totais:
        peer.enviar_estoque()
        
        try:
            id_alvo, bloco_desejado = peer.receber_estoques() # Verifica os estoques e tenta solicitar um bloco e o id do peer que possui o bloco
        except TypeError:
            continue
        
        time.sleep(0.1)
        
        peer.solicitar_bloco(peer.peers[id_alvo], bloco_desejado)
        
    peer.arquivo_completo = True # Mostra que completou o arquivo
    print(f"[Peer {peer.id}] Obteve todos os blocos")
    
    processador_mensagens.join()
    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', type=int, required=True)
    args = parser.parse_args()

    peer_id = args.id
    peer = Peer(peer_id)
    
    thread_servidor = threading.Thread(target=peer.iniciar_servidor, args=(PORTA_BASE+peer.id, )).start()
    
    tracker = peer.conectar_servidor(TRACKER_PORTA)
    
    obter_blocos_iniciais(peer, tracker)

    completar_arquivo(peer)