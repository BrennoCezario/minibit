import os
import random
import time
import logging
from threading import Thread, Lock

NUMERO_DE_PEERS = 10

# --- Configuração da pasta de logs ---
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

class Peer:
    def __init__(self, id):
        self.id = id
        self.blocos = []
        self.conexoes = []
        self.correio = {'mensagem': []}
        self.receptor_ativo = True
        self.lock = Lock()  # Lock para proteger o acesso ao correio e blocos

        # --- Configuração do logger para este peer ---
        self.logger = logging.getLogger(f"Peer_{self.id}")
        self.logger.setLevel(logging.INFO)
        # Evita que handlers sejam adicionados múltiplas vezes
        if not self.logger.handlers:
            handler = logging.FileHandler(os.path.join(LOG_DIR, f"peer_{self.id}.log"), mode='w')
            formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def log(self, mensagem):
        """Registra uma mensagem no log e a imprime no console."""
        self.logger.info(mensagem)
        print(f"[Peer {self.id}] {mensagem}")

    def definir_conexoes(self, conexoes):
        for i in range(len(conexoes)):
            no_rede = conexoes[self.id - 1][i]
            if no_rede == 1:
                self.conexoes.append(i + 1)

    def envia_estoque(self, estoque):
        with self.lock:
            estoque[f'{self.id}'] = list(self.blocos)

    def recebe_estoques(self, estoques):
        blocos_faltando = []
        with self.lock:
            meus_blocos = set(self.blocos)
            for peer_id, blocos in estoques.items():
                if int(peer_id) == self.id:
                    continue
                
                for bloco in blocos:
                    if bloco not in meus_blocos:
                        blocos_faltando.append((int(peer_id), bloco))
        
        if blocos_faltando:
            return random.choice(blocos_faltando)
        return None, None

    def solicita_bloco(self, peer_alvo, bloco_solicitado):
        self.log(f"Solicitando Bloco '{bloco_solicitado}' do peer {peer_alvo.id}")
        self.enviar_mensagem(peer_alvo, f"PEDIDO|{bloco_solicitado}")

    def enviar_mensagem(self, receptor, mensagem):
        self.log(f"Enviando para o peer {receptor.id}: {mensagem}")
        with receptor.lock:
            receptor.correio["mensagem"].append((self, mensagem))

    def receber_mensagem(self):
        while self.receptor_ativo:
            time.sleep(0.01) # Evita uso excessivo de CPU
            
            with self.lock:
                if not self.correio["mensagem"]:
                    continue
                
                mensagens_para_processar = list(self.correio["mensagem"])
                self.correio["mensagem"].clear()

            for peer, mensagem in mensagens_para_processar:
                self.log(f"Processando de {peer.id}: {mensagem}")
                partes = mensagem.split('|')
                comando = partes[0]
                valor = int(partes[1])

                if comando == "PEDIDO":
                    if valor in self.blocos:
                        self.enviar_mensagem(peer, f"ENVIO|{valor}")
                elif comando == "ENVIO":
                    if valor not in self.blocos:
                        with self.lock:
                            self.blocos.append(valor)
                            self.blocos.sort()
                        self.log(f"Bloco {valor} recebido. Blocos atuais: {self.blocos}")


def adicionar_peer(id):
    return Peer(id)

def distribuir_blocos(blocos_unidos, lista_peers, blocos_por_peer):
    escolhidos = []
    for _ in range(blocos_por_peer):
        for peer in lista_peers:
            if len(peer.blocos) >= blocos_por_peer:
                continue
            
            disponiveis = [b for b in blocos_unidos if b not in peer.blocos and b not in escolhidos]
            if not disponiveis:
                escolhidos = [] # Reseta se todos já foram escolhidos nesta rodada
                disponiveis = [b for b in blocos_unidos if b not in peer.blocos and b not in escolhidos]

            if disponiveis:
                numero_escolhido = random.choice(disponiveis)
                peer.blocos.append(numero_escolhido)
                escolhidos.append(numero_escolhido)

def iniciar_conexoes(lista_peers):
    matriz_conexoes = [[0 for _ in range(len(lista_peers))] for _ in range(len(lista_peers))]
    for i, peer1 in enumerate(lista_peers):
        for j, peer2 in enumerate(lista_peers):
            if i != j:
                matriz_conexoes[i][j] = 1 # Simplificando para uma rede totalmente conectada
    
    for peer in lista_peers:
        peer.definir_conexoes(matriz_conexoes)
    return matriz_conexoes

def imprime_conexoes(conexoes):
    for conexao in conexoes:
        print("".join(str(conexao)))

def iniciar_trocas(peers, arquivo):
    threads = []
    estoques = {}
    for peer in peers:
        thread = Thread(target=completar_arquivo, args=(peer, arquivo, estoques, peers))
        threads.append(thread)
        thread.start()
    
    for t in threads:
        t.join() # Espera todas as threads de completar_arquivo terminarem

def completar_arquivo(peer, arquivo, estoques, lista_peers):
    thread_receptora = Thread(target=peer.receber_mensagem)
    thread_receptora.start()
    
    while len(peer.blocos) < len(arquivo):
        peer.envia_estoque(estoques)
        
        # Espera um pouco para os estoques serem preenchidos
        if len(estoques) < NUMERO_DE_PEERS:
            time.sleep(0.1)
            continue
        
        id_alvo, bloco_desejado = peer.recebe_estoques(estoques)
        
        if id_alvo and bloco_desejado:
            peer_alvo = next((p for p in lista_peers if p.id == id_alvo), None)
            if peer_alvo:
                peer.solicita_bloco(peer_alvo, bloco_desejado)

        time.sleep(0.1) # Pausa para evitar pedidos excessivos e dar tempo para recebimento
            
    peer.receptor_ativo = False
    thread_receptora.join()
    peer.log("Download completo. Finalizando.")

if __name__ == "__main__":
    os.system("cls" if os.name == "nt" else "clear")

    arquivo = list(range(1, 1001))
    lista_peers = [adicionar_peer(i + 1) for i in range(NUMERO_DE_PEERS)]
    
    print(f"\nNúmero de peers na rede: {len(lista_peers)}")
    
    blocos_por_peer = len(arquivo) // len(lista_peers) + 1
    print(f"\nNúmero de blocos por peer: {blocos_por_peer}\n")
    distribuir_blocos(arquivo, lista_peers, blocos_por_peer)

    matriz_conexoes = iniciar_conexoes(lista_peers)
    print("Conexões:")
    imprime_conexoes(matriz_conexoes)

    for peer in lista_peers:
        peer.blocos.sort()
        print(f"\nBlocos iniciais do peer {peer.id}: {peer.blocos}")
        print(f"Conexões do peer {peer.id}: {peer.conexoes}")

    print("\n--- INICIANDO TROCAS ---\n")
    iniciar_trocas(lista_peers, arquivo)
    print("\n--- TROCAS FINALIZADAS ---\n")
    
    for peer in lista_peers:
        peer.blocos.sort()
        print(f"\nBlocos finais do peer {peer.id}: {peer.blocos}")