import os
import random
from peer import Peer
from threading import Thread

NUMERO_DE_PEERS = 4 # Constante que define o número de peers na rede (Por enquanto só funciona com 4 peers)

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

# Função que inicia a 'conexão' meramente visual entre peers, retornando a matriz de adjacências correspondente
def iniciar_conexoes(lista_peers):
    matriz_conexoes = [[4 for _ in range(len(lista_peers))] for _ in range(len(lista_peers))] # Gera matriz n_peers x n_peers que inicialmente recebe o número 4

    # Sub Função que garante que dois peers podem se conectar entre si verificando a quantidade de conexões atuais, que não pode ultrapassar o valor 4
    def pode_conectar(peer_1, peer_2):
        contador_1 = 0 # Conta o número de funções do peer_1
        contador_2 = 0 # Conta o número de funções do peer_2

        # Valida cada linha da matriz
        for i in range(len(matriz_conexoes)):
            if matriz_conexoes[peer_1][i] == 1: # Se o valor da posição for igual 1, então é uma conexão 
                contador_1 += 1
            if matriz_conexoes[peer_2][i] == 1:
                contador_2 += 1

        if contador_1 >= 4 or contador_2 >= 4: # Caso o número de conexões de um dos peers for maior ou igual a 4, então função retorna falso, não permitindo a conexão
            return False
        return True # Caso o número de conexões dos dois peers for menor que 4, então função retorna verdadeiro, permitindo a conexão 
    
    # Loop que vai definir as conexões entre os peers
    for i in range(len(lista_peers)):
        for j in range(len(lista_peers)):
    
            if i == j: # Peer não se conecta, nem se bloqueia consigo mesmo
                matriz_conexoes[i][j] = 0
            
            # Verifica se o valor já não é 1 (conectado), se pode se conectar, segundo a sub função pode_conectar e verifica se o valor de jxi já está assinalado como 1 (já estão conectados)
            elif matriz_conexoes[i][j] != 1 and pode_conectar(i, j) or matriz_conexoes[j][i] == 1: 
                matriz_conexoes[i][j] = 1

            else: # Caso nenhuma condição seja satisfeita os peers ficam bloqueados entre si (Poderão se desbloqueados no futuro, mas falta implementar)
                matriz_conexoes[i][j] = 2

    for peer in lista_peers:
        peer.definir_conexoes(matriz_conexoes) # Define para cada peer os outros peers com quem está conectado

    return matriz_conexoes # Retorna a matriz de adjacências das conexões

# Função que imprime a matriz de conexões esteticamente melhor
def imprime_conexoes(conexoes):
    for conexao in conexoes:
        print("".join(str(conexao)))

# Função que inicia uma thread para cada peer da rede se prontificar para iniciar as trocas de blocos e completarem seus arquivos
def iniciar_trocas(peers, arquivo):
    estoques = {} # Variável compartilhada que armazena os blocos de cada peer para ser utilizada na função independente de cada thread
    for peer in peers:
        thread = Thread(target=completar_arquivo, args=(peer, arquivo, estoques, peers)) # Thread de cada peer para trocar blocos e completar o arquivo
        thread.start()
        
# Função que possui o objetivo de completar o arquivo de cada peer
def completar_arquivo(peer, arquivo, estoques, lista_peers):
    thread = Thread(target=peer.receber_mensagem) # Thread que cada peer inicia para ouvir novas mensagens enquanto realiza outras tarefas de envio
    thread.start()
    
    while len(peer.blocos) < len(arquivo): # Loop que só termina quando o peer consegue todos os blocos do arquivo
        peer.envia_estoque(estoques) # Peer envia o seu estoque para armazenar na variável compartilhada de estoques dos peers
        
        while len(estoques) < len(lista_peers): # Aguarda todos os estoques estarem disponíveis
            continue
        try:
            id_alvo, bloco_desejado = peer.recebe_estoques(estoques) # Verifica os estoques e tenta solicitar um bloco e o id do peer que possui o bloco
        except TypeError:
            continue

        for peers in lista_peers:
            if peers.id == int(id_alvo): 
                peer.solicita_bloco(peers, bloco_desejado) # Solicita o bloco para o peer que o possui
                break

    peer.arquivo_incompleto = False # Mostra que completou o arquivo
    
    # Lógica para verificar se os outros peers já completaram seus arquivos
    arquivos_incompletos = 3
    while arquivos_incompletos > 0: # Enquanto houver peers com arquivo incompleto, a thread que recebe pedidos continuará ligada
        if lista_peers[arquivos_incompletos-1].arquivo_incompleto == False:
            arquivos_incompletos-=1    
    
    print(f"\nPeer {peer.id} completou o arquivo!")  
    peer.receptor_ativo = False # Desliga a thread receptora de mensagens
    thread.join()
    return
    

if __name__ == "__main__":
    os.system("cls" if os.name == "nt" else "clear") # Chamada de sistema para limpar o terminal para os 'prints'

    arquivo =  [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] # Simulação de um arquivo com 10 blocos

    lista_peers = [] # Lista para inserir os objetos da classe peer

    # Inserindo 'peers' na lista
    for i in range(NUMERO_DE_PEERS):
        lista_peers.append(adicionar_peer(i+1))
    print("\nNúmero de peers que estão disponíveis na rede: ", len(lista_peers)) 
    
    # Cálculo que determina o número de blocos que cada peer iniciará. 
    # A divisão do tamanho de arquivos pelo número de peers garante que todos os blocos serão distribuídos, e somando +1, garantimos que teremos alguns blocos mais raros do que outros 
    blocos_por_peer = (len(arquivo) // len(lista_peers)) + 1
    print("\nNúmero de blocos para cada peer: ", blocos_por_peer, "\n")

    distribuir_blocos(arquivo, lista_peers, blocos_por_peer) # Chamada da função que distribui um subconjunto de blocos para cada peer

    matriz_conexoes = iniciar_conexoes(lista_peers) # Função que gera uma matriz de adjacência entre os peers para ilustrar e definir as conexões dos mesmos
    print("Conexões:")
    imprime_conexoes(matriz_conexoes) # Função que imprime a matriz de conexões

    for peer in lista_peers:
        print(f"\nBlocos do peer {peer.id}: {peer.blocos}")
        print(f"Conexões do peer {peer.id}: {peer.conexoes}" if lista_peers.index(peer) < len(lista_peers)-1  else f"Conexões do peer {peer.id}: {peer.conexoes}\n")

    # Função que inicia as trocas entre os peers 
    iniciar_trocas(lista_peers, arquivo)
    
    # Verificação do fim das trocas de blocos e se todos os peers já completaram os seus respectivos arquivos
    arquivos_completos = 0
    while arquivos_completos < NUMERO_DE_PEERS:
        if lista_peers[arquivos_completos].receptor_ativo == False:
            arquivos_completos+=1
    
    # Resultado das trocas
    for peer in lista_peers:
        print(f"\nBlocos do peer {peer.id}: {peer.blocos}")