import random

NUMERO_DE_PEERS = 10

class Peer:
    def __init__(self, id):
        self.id = id
        self.blocos = []

    def selecionar_arquivo_desejado(self, arquivo):
        self.arquivo = arquivo

def adicionar_peer(id):
    peer = Peer(id)
    return peer

def unir_blocos(arquivos):
    blocos = []

    for arquivo in arquivos.values():
        for bloco in arquivo:
            blocos.append(bloco)
    
    return blocos

def distribuir_blocos(blocos_unidos, lista_de_peers, blocos_por_peer):
    escolhidos = []
    iteracoes = blocos_por_peer
    
    for _ in range(iteracoes):
        for peer in lista_de_peers:     
            numero_escolhido = random.choice(blocos_unidos)

            while numero_escolhido in escolhidos or numero_escolhido in peer.blocos:
                numero_escolhido = random.choice(blocos_unidos)

            peer.blocos.append(numero_escolhido)

            escolhidos.append(numero_escolhido)
            
            if len(escolhidos) == len(blocos_unidos):
                escolhidos = []

if __name__ == "__main__":
    arquivos = {
        "arquivo1": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "arquivo2": [11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
        "arquivo3": [21, 22, 23, 24, 25, 26, 27, 28, 29, 30]
    }
    print("Lista de arquivos disponíveis para download",arquivos)

    lista_de_peers = []

    for i in range(NUMERO_DE_PEERS):
        lista_de_peers.append(adicionar_peer(i+1))
    print("\nNúmero de peers que estão disponíveis na rede: ", len(lista_de_peers))
    
    blocos_unidos = unir_blocos(arquivos)
    print("Todos os blocos de arquivos", blocos_unidos)

    blocos_por_peer = (len(blocos_unidos) // len(lista_de_peers)) + 1
    print("\nNúmero de blocos para cada peer: ", blocos_por_peer, "\n")

    distribuir_blocos(blocos_unidos, lista_de_peers, blocos_por_peer)
    for peer in lista_de_peers:
        arquivo_selecionado = random.choice(list(arquivos.keys()))
        peer.selecionar_arquivo_desejado = arquivo_selecionado
        print(f"Blocos do peer {peer.id}: {peer.blocos}")
        print(f"Arquivo selecionado pelo peer {peer.id}: {arquivo_selecionado}\n")