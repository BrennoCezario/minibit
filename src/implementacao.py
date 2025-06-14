import argparse
import threading
import time
import json
import random
import base64
from .peer import Peer
from .construcao_arquivo import ConstruirArquivo

TRACKER_PORTA = 8000

PORTA_BASE = 9000

def obter_blocos_iniciais(peer, tracker):
    
    blocos = []
    
    with open("blocos.json", 'r', encoding='utf-8') as f:
            blocos = json.load(f)
            
    for indice in range(len(blocos)):
            blocos[indice] = (indice+1, blocos[indice])
            peer.indices.append(indice+1)

    blocos_totais = len(blocos)
    
    peer.blocos = random.sample(blocos, (len(blocos) // 4) + 1)
    
    print(f"\n{len(peer.blocos)} Blocos: {[bloco[1][:5] + '...' for bloco in peer.blocos]}\n")
                 
def completar_arquivo(peer):
    peer.receptor_ativo = True
    processador_mensagens = threading.Thread(target=peer.processar_mensagens).start()
    blocos_totais = 72
    while len(peer.blocos) < blocos_totais:
        try:
            id_alvo, bloco_desejado = peer.receber_estoques() # Verifica os estoques e tenta solicitar um bloco e o id do peer que possui o bloco
        except TypeError:
            continue
        
        peer.solicitar_bloco(id_alvo, bloco_desejado)
        time.sleep(1)
        
    peer.arquivo_completo = True # Mostra que completou o arquivo
    print(f"[Peer {peer.id}] Obteve todos os blocos")
    

    blocos = []
    for bloco in peer.blocos:
        blocos.append(bloco[1])
    
    blocos_arquivo = "peer_1.json"
    f = open(blocos_arquivo, 'w')
    json.dump(blocos, f)
    f.close()
    construtor = ConstruirArquivo(blocos)
    construtor.rodar(peer.id)
    
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
    
    peer.tracker_conexao = tracker
    
    obter_blocos_iniciais(peer, tracker)

    completar_arquivo(peer)