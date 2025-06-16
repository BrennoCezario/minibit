import argparse
import threading
import time
import json
import random
import base64
from .peer import Peer
from .construcao_arquivo import ConstruirArquivo

TRACKER_PORTA = 8001

PORTA_BASE = 9000

def obter_blocos_iniciais(peer, tracker):
    blocos = []
    with open("blocos.json", 'r', encoding='utf-8') as f:
            blocos = json.load(f)
    for indice in range(len(blocos)):
            blocos[indice] = (indice+1, blocos[indice])
    
    peer.blocos = random.sample(blocos, (len(blocos) // 10) + 1)
    peer.indices = [indice for indice, _ in peer.blocos] # os indices do peer sao somente os indices dos blocos que possui
    
    print(f"\nPeer {peer.id} inicio com {len(peer.blocos)} blocos: {[bloco[1][:5] + '...' for bloco in peer.blocos]}\n")

def obter_blocos_totais():
    f = open("metadata.json", 'r', encoding="utf-8")
    metadata = json.load(f)
    f.close()
    return metadata["numero_blocos"]

def completar_arquivo(peer):
    peer.receptor_ativo = True

    blocos_totais = obter_blocos_totais()
    
    inicio = time.time()
    while len(set(indice for indice, _ in peer.blocos)) < blocos_totais:
        try:
            id_alvo, bloco_desejado = peer.receber_estoques() # Verifica os estoques e tenta solicitar um bloco e o id do peer que possui o bloco
        except TypeError:
            continue
        peer.solicitar_bloco(id_alvo, bloco_desejado)
        time.sleep(1)
        
    peer.arquivo_completo = True # Mostra que completou o arquivo
    print(f"\n[Peer {peer.id}] Obteve todos os blocos")
    
    blocos_dicio = {}
    for indice, bloco in peer.blocos:
         blocos_dicio[indice] = bloco
    blocos = [blocos_dicio[i] for i in range(1, blocos_totais + 1)]
    
    blocos_arquivo = f"peer_{peer.id}.json"
    f = open(blocos_arquivo, 'w')
    json.dump(blocos, f)
    f.close()
    construtor = ConstruirArquivo(blocos)

    print(f"[Peer {peer.id}] tem blocos: {sorted(blocos_dicio.keys())}")
    for i in range(1, blocos_totais + 1):
        if i not in blocos_dicio:
            print(f"Peer {peer.id} está faltando o bloco {i}")

    construtor.rodar(peer.id)

    fim = time.time()
    print(f"[Peer {peer.id}] realizou o download em {fim-inicio:.2f} segundos")
    print(f"[Peer {peer.id}] realizou o envio de {peer.mensagens_enviadas} mensagens\n")
    
    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', type=int, required=True)
    args = parser.parse_args()

    peer_id = args.id
    peer = Peer(peer_id)
    
    thread_servidor = threading.Thread(target=peer.iniciar_servidor, args=(PORTA_BASE+peer.id, ))
    thread_servidor.start()
    time.sleep(0.5)
    
    tracker = peer.conectar_servidor(TRACKER_PORTA)
    
    peer.tracker_conexao = tracker
    
    obter_blocos_iniciais(peer, tracker)

    completar_arquivo(peer)