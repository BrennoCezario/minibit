# Construção do arquivo - Trabalho 2 Sistemas Distribuidos

import json
import os
import hashlib
import base64

class ConstruirArquivo:
    def __init__(self, blocos_peer):
        self.blocos_arquivo = blocos_peer
        self.metadata_arquivo = "metadata.json"
        self.data_blocos = blocos_peer
        self.metadata = {}

    def carregar_dados(self):
        # Carrega a informação em byte dos blocos e o seu metadata
        # f = open(self.blocos_arquivo, 'r')
        # self.data_blocos = json.load(f)
        # f.close()

        f = open(self.metadata_arquivo, 'r')
        self.metadata = json.load(f)
        f.close()

    # funcao para reconstruir os arquivos, recebe como parametro os dados dos blocos em base64 e o nome do arquivo de saída
    def construir_arquivo(self, peer_id):
        
        blocos_ordenados_b64 = self.ordenar_blocos_por_hash(self.data_blocos)
        
        nomeEsboco = self.metadata["nome_arquivo"]
        nomeArquivo, extensaoArquivo = os.path.splitext(nomeEsboco)
        output = f"{nomeArquivo}_{peer_id}{extensaoArquivo}"
        # abre o arquivo de saída recém criado como wb (write binary), decodifica base64 em bytes e escreve os bytes, montando o arquivo
        f = open(output, 'wb')
        try:
            for bloco_b64 in blocos_ordenados_b64:
                bloco = base64.b64decode(bloco_b64)
                # bloco sao os blocos reconstruidos
                f.write(bloco)
        finally:
            f.close()
        print("Arquivo reconstruido como:", output)
        return output
    
    # com verifica_construcao, verificamos o hash de cada bloco reconstruido com o hash que criamos quando estávamos dividindo o arquivo original em blocos
    def verifica_construcao(self):
        algoritmo_hash = 'sha256'
        # zip emparelha cada bloco reconstruido com o hash original, para assim podermos comparar.
        for idx, (bloco_b64, original_hash) in enumerate(zip(self.data_blocos, self.metadata["hash_blocos"])):
            bloco = base64.b64decode(bloco_b64)
            hasher = hashlib.new(algoritmo_hash)
            # hasher é atualizado com o hash do bloco reconstruido, para assim comparar com o hash original.
            hasher.update(bloco)
            # aqui fazemos uma validação, comparando o hash do bloco reconstruido com o hash original para aquele bloco. Se não bater, retorna false
            # Estando tudo certo, retorna true e temos certeza que o arquivo reconstruído é idêntico ao original
            if hasher.hexdigest() != original_hash:
                print("Bloco de índice:",idx,"não bateu com o original.")
                return False
        return True
    
    def ordenar_blocos_por_hash(self, blocos_desordenados_b64):
        """
        Esta é a nova função principal. Ela reordena os blocos de dados
        baseado na sequência de hashes do arquivo de metadados.
        """
        print("Mapeando hashes dos blocos recebidos...")
        algoritmo_hash = self.metadata.get("algoritmo_hash", "sha256")
        
        # 1. Cria um mapa de hash -> dado_do_bloco
        mapa_hash_para_bloco = {}
        for bloco_b64 in blocos_desordenados_b64:
            dados_binarios = base64.b64decode(bloco_b64)
            hash_calculado = hashlib.new(algoritmo_hash, dados_binarios).hexdigest()
            mapa_hash_para_bloco[hash_calculado] = bloco_b64

        # 2. Monta a lista ordenada usando o metadata como guia
        print("Ordenando blocos de acordo com os hashes do metadata...")
        blocos_ordenados = []
        hashes_originais = self.metadata["hash_blocos"]
        
        for hash_correto in hashes_originais:
            bloco_encontrado = mapa_hash_para_bloco.get(hash_correto)
            if bloco_encontrado:
                blocos_ordenados.append(bloco_encontrado)
            else:
                # Se um hash do metadata não for encontrado nos blocos do peer, o download está incompleto.
                print(f"FALHA: Bloco com hash {hash_correto[:10]}... não foi encontrado. Download incompleto.")
                return None # Retorna None para indicar falha

        # 3. Verificação final de segurança
        if len(blocos_ordenados) != len(hashes_originais):
            print("FALHA: O número de blocos encontrados não corresponde ao metadata.")
            return None
            
        print("Blocos ordenados com sucesso!")
        return blocos_ordenados

    def rodar(self, peer_id):
        self.carregar_dados()
        self.construir_arquivo(peer_id)
        # validação dos blocos, hash_blocos são os hashes originais, e 'blocos' contem os hashes dos 
        if self.verifica_construcao():
            print("Sucesso, verificação hash bem sucedida.")
        else:
            print("Falha, alguns blocos falharam a verificação hash.")

