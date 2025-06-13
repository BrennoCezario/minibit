import os
import random
import time
import logging
import json
from .peer import Peer
from src.divisao_blocos import DivisaoBlocos
from src.construcao_arquivo import ConstruirArquivo
from threading import Thread

NUMERO_DE_PEERS = 10 # Constante que define o número de peers na rede

# Função que retorna uma instância da classe Peer 
def adicionar_peer(id):
    peer = Peer(id)
    return peer

# Função que realiza a distribuição de um subconjunto aleatório de blocos para cada peer
def distribuir_blocos(arquivo, lista_peers, blocos_por_peer):
    escolhidos = [] # Lista que mostra os blocos que já foram selecionados e por um momento não podem ser selecionados
    
    for _ in range(blocos_por_peer):
        for peer in lista_peers:     
            bloco_escolhido = random.choice(arquivo) # Bloco aleatório que é escolhido do arquivo

            while bloco_escolhido in escolhidos or bloco_escolhido in peer.blocos: # Garante que o peer não possui o bloco e que o bloco pode ser escolhido
                bloco_escolhido = random.choice(arquivo)

            peer.blocos.append(bloco_escolhido) # Insere o bloco no conjunto de blocos que o peer possui

            escolhidos.append(bloco_escolhido) # Insere o bloco na lista de blocos que não podem ser escolhidos
            
            if len(escolhidos) == len(arquivo): # 'Zera' a lista de blocos escolhidos, pois todos os blocos do arquivo já foram distribuidos, agora podem ser repetidos
                escolhidos = []

# Função que implementa a lógica para conectar os peers           
def realizar_conexoes(matriz_conexoes):
    
    while True:
        peers_indisponiveis = [] # Lista que mostra peers que já esgotaram seu máximo de conexões
        
        peer_1 = random.choice(range(len(matriz_conexoes)))
        while sum(matriz_conexoes[peer_1]) >= 4:
            
            peers_indisponiveis.append(peer_1 if peer_1 not in peers_indisponiveis else None)
            
            if len(peers_indisponiveis) == len(matriz_conexoes):
                break
            
            peer_1 = random.choice(range(len(matriz_conexoes)))
        
        peers_indisponiveis = []
        
        peer_2 = random.choice(range(len(matriz_conexoes)))
        while sum(matriz_conexoes[peer_2]) >= 4 or peer_2 == peer_1:
            
            if sum(matriz_conexoes[peer_2]) >= 4:
                peers_indisponiveis.append(peer_2 if peer_2 not in peers_indisponiveis else None)
                
            if len(peers_indisponiveis) >= len(matriz_conexoes)-1:
                break
        
            peer_2 = random.choice(range(len(matriz_conexoes)))
            
        if len(peers_indisponiveis) >= len(matriz_conexoes)-1:
                break
            
        matriz_conexoes[peer_1][peer_2] = 1
        matriz_conexoes[peer_2][peer_1] = 1
    
# Função que inicia a 'conexão' meramente visual entre peers, retornando a matriz de adjacências correspondente
def iniciar_conexoes(lista_peers):
    matriz_conexoes = [[0 for _ in range(len(lista_peers))] for _ in range(len(lista_peers))] # Gera matriz n_peers x n_peers que inicialmente recebe o número 4
    
    realizar_conexoes(matriz_conexoes)
    
    for peer in lista_peers:
        peer.definir_conexoes(matriz_conexoes)
        
    print("Conexões Iniciais:")
    imprime_conexoes(matriz_conexoes) # Função que imprime a matriz de conexões
        
    return matriz_conexoes

# Função que atualiza a cada 10 segundos as conexões que foram estabelecidas entre os peers
def atualizar_conexoes(peers, conexoes):
    
    logger = logging.getLogger(f"Conexoes")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.FileHandler(os.path.join("logs", f"conexoes.log"), mode='w')
        formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
            
    def log_conexoes():
        logger.info("Conexoes atualizadas:")
        for conexao in conexoes:
            logger.info(f"".join(str(conexao)))
    
    while True:
        time.sleep(10)
        
        for conexao in conexoes:
            desconectar = random.choice(range(len(conexoes)))
            while conexao[desconectar] == 0:
                desconectar = random.choice(range(len(conexoes)))
            conexao[desconectar] = 0
        
        realizar_conexoes(conexoes)
        
        for peer in peers:
            peer.definir_conexoes(conexoes)
            
        log_conexoes()
        
# Função que imprime a matriz de conexões esteticamente melhor
def imprime_conexoes(conexoes):
    for conexao in conexoes:
        print("".join(str(conexao)))

# Função que inicia uma thread para cada peer da rede se prontificar para iniciar as trocas de blocos e completarem seus arquivos
def iniciar_trocas(peers, arquivo):
    estoques = {} # Variável compartilhada que armazena os blocos de cada peer para ser utilizada na função independente de cada thread
    for peer in peers:
        peer_thread = Thread(target=completar_arquivo, args=(peer, arquivo, estoques, peers)) # Thread de cada peer para trocar blocos e completar o arquivo
        peer_thread.start()
        
# Função que possui o objetivo de completar o arquivo de cada peer
def completar_arquivo(peer, arquivo, estoques, lista_peers):
    peer.receptor_ativo = True
    receptor_thread = Thread(target=peer.receber_mensagem) # Thread que cada peer inicia para ouvir novas mensagens enquanto realiza outras tarefas de envio
    receptor_thread.start()
    
    while len(peer.blocos) < len(arquivo): # Loop que só termina quando o peer consegue todos os blocos do 
        
        peer.verifica_pedidos_expirados() # Verifica se há pedidos de conexões que foram desfeitas
        
        peer.envia_estoque(estoques) # Peer envia o seu estoque para armazenar na variável compartilhada de estoques dos peers

        while len(estoques) < len(peer.conexoes): # Aguarda todos os estoques estarem disponíveis
            continue
        try:
            id_alvo, bloco_desejado = peer.recebe_estoques(estoques) # Verifica os estoques e tenta solicitar um bloco e o id do peer que possui o bloco
        except TypeError:
            continue
        time.sleep(0.1)

        for peers in lista_peers:
            if peers.id == int(id_alvo): 
                peer.solicita_bloco(peers, bloco_desejado) # Solicita o bloco para o peer que o possui
                break

    peer.arquivo_completo = True # Mostra que completou o arquivo
    print(f"[Peer {peer.id}] Obteve todos os blocos")
    
    # Lógica para verificar se os outros peers já completaram seus arquivos
    arquivos_incompletos = len(lista_peers)
    while arquivos_incompletos > 0: # Enquanto houver peers com arquivo incompleto, a thread que recebe pedidos continuará ligada
        if lista_peers[arquivos_incompletos-1].arquivo_completo == True:
            arquivos_incompletos-=1    
            
    peer.receptor_ativo = False # Desliga a thread receptora de mensagens
    receptor_thread.join()
    return

if __name__ == "__main__":
    os.system("cls" if os.name == "nt" else "clear") # Chamada de sistema para limpar o terminal para os 'prints'

    arquivo = "trabalho_final.pdf"
    
    dividir_arquivo = DivisaoBlocos(arquivo)
    dividir_arquivo.rodar()
    
    blocos_arquivo = []
    with open("blocos.json", 'r', encoding='utf-8') as f:
        blocos_arquivo = json.load(f)

    lista_peers = [] # Lista para inserir os objetos da classe peer

    # Inserindo 'peers' na lista
    for i in range(NUMERO_DE_PEERS):
        lista_peers.append(adicionar_peer(i+1))
    print("\nNúmero de peers que estão disponíveis na rede: ", len(lista_peers)) 
    
    '''' Cálculo que determina o número de blocos que cada peer iniciará. 
    A divisão do tamanho de arquivos pelo número de peers garante que todos os blocos serão distribuídos, 
    e somando +1, garantimos que teremos alguns blocos mais raros do que outros '''
    blocos_por_peer = (len(blocos_arquivo) // len(lista_peers)) + 1
    print("\nNúmero de blocos para cada peer: ", blocos_por_peer, "\n")

    distribuir_blocos(blocos_arquivo, lista_peers, blocos_por_peer) # Chamada da função que distribui um subconjunto de blocos para cada peer

    matriz_conexoes = iniciar_conexoes(lista_peers) # Função que gera uma matriz de adjacência entre os peers para ilustrar e definir as conexões dos mesmos
    
    for peer in lista_peers:
        # print(f"\nBlocos do peer {peer.id}: {peer.blocos}")
        print(f"Conexões do peer {peer.id}: {peer.conexoes}" if lista_peers.index(peer) < len(lista_peers)-1  else f"Conexões do peer {peer.id}: {peer.conexoes}\n")

    # Função que inicia as trocas entre os peers 
    print("\n--- INICIANDO TROCAS ---\n")
    iniciar_trocas(lista_peers, blocos_arquivo)

    novas_conexoes_thread = Thread(target=atualizar_conexoes, args=(lista_peers, matriz_conexoes), daemon=True) # Thread que atualiza as conexões entre peers a cada 10 segundos
    novas_conexoes_thread.start()
    
    # Verificação do fim das trocas de blocos e se todos os peers já completaram os seus respectivos arquivos
    arquivos_completos = 0
    while arquivos_completos < NUMERO_DE_PEERS:
        if lista_peers[arquivos_completos].receptor_ativo == False:
            arquivos_completos+=1
    print("\n--- TROCAS FINALIZADAS ---\n")
    
    # Resultado das trocas
    for peer in lista_peers:
        peer.blocos.sort()
        construtor = ConstruirArquivo(peer.blocos)
        construtor.rodar(peer.id)
        print(f"\nArquivo do peer {peer.id}")