import os
import random
from threading import Thread

NUMERO_DE_PEERS = 4

class Peer:
    def __init__(self, id):
        self.id = id
        self.blocos = []
        self.conexoes = []
    
    def definir_conexoes(self, conexoes):
        for i in range(len(conexoes)):
            no_rede = conexoes[self.id-1][i]
            if no_rede == 1:
                self.conexoes.append(i+1)

    def envia_estoque(self):
        pass

    def recebe_estoques(self):
        pass

    def troca_blocos(self, blocos_desejados):
        pass

def adicionar_peer(id):
    peer = Peer(id)
    return peer

def distribuir_blocos(blocos_unidos, lista_peers, blocos_por_peer):
    escolhidos = []
    iteracoes = blocos_por_peer
    
    for _ in range(iteracoes):
        for peer in lista_peers:     
            numero_escolhido = random.choice(blocos_unidos)

            while numero_escolhido in escolhidos or numero_escolhido in peer.blocos:
                numero_escolhido = random.choice(blocos_unidos)

            peer.blocos.append(numero_escolhido)

            escolhidos.append(numero_escolhido)
            
            if len(escolhidos) == len(blocos_unidos):
                escolhidos = []

def iniciar_conexoes(lista_peers):
    matriz_conexoes = [[4 for _ in range(len(lista_peers))] for _ in range(len(lista_peers))]

    def pode_conectar(peer_1, peer_2):
        contador_1 = 0
        contador_2 = 0

        for i in range(len(matriz_conexoes)):
            if matriz_conexoes[peer_1][i] == 1:
                contador_1 += 1
            if matriz_conexoes[peer_2][i] == 1:
                contador_2 += 1

        if contador_1 >= 4 or contador_2 >= 4:
            return False
        return True
    
    for i in range(len(lista_peers)):
        for j in range(len(lista_peers)):
    
            if i == j:
                matriz_conexoes[i][j] = 0
            
            elif matriz_conexoes[i][j] != 1 and pode_conectar(i, j) or matriz_conexoes[j][i] == 1:
                matriz_conexoes[i][j] = 1

            else:
                matriz_conexoes[i][j] = 2
    for peer in lista_peers:
        peer.definir_conexoes(matriz_conexoes)

    return matriz_conexoes

def imprime_conexoes(conexoes):
    for conexao in conexoes:
        print("".join(str(conexao)))

def iniciar_trocas(peers, arquivo):
    for peer in peers:
        thread = Thread(target=completar_arquivo, args=(peer, arquivo))
        thread.start()

def completar_arquivo(peer, arquivo):
    while len(peer.blocos) < len(arquivo):
        peer.envia_estoque()
        blocos_desejados = peer.recebe_estoques()
        peer.troca_blocos(blocos_desejados)
        return

if __name__ == "__main__":
    os.system("cls" if os.name == "nt" else "clear")

    arquivo =  [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    lista_peers = []

    for i in range(NUMERO_DE_PEERS):
        lista_peers.append(adicionar_peer(i+1))
    print("\nNúmero de peers que estão disponíveis na rede: ", len(lista_peers))
    
    blocos_por_peer = (len(arquivo) // len(lista_peers)) + 1
    print("\nNúmero de blocos para cada peer: ", blocos_por_peer, "\n")

    distribuir_blocos(arquivo, lista_peers, blocos_por_peer)

    matriz_conexoes = iniciar_conexoes(lista_peers)
    print("Conexões:")
    imprime_conexoes(matriz_conexoes)

    for peer in lista_peers:
        print(f"\nBlocos do peer {peer.id}: {peer.blocos}")
        print(f"Conexões do peer {peer.id}: {peer.conexoes}" if lista_peers.index(peer) < len(lista_peers)-1  else f"Conexões do peer {peer.id}: {peer.conexoes}\n")

    iniciar_trocas(lista_peers, arquivo)