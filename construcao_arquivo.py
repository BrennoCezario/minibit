# Construção do arquivo - Trabalho 2 Sistemas Distribuidos

import json
import os
import hashlib
import base64

class ConstuirArquivo:
    def __init__(self):
        self.blocos_arquivo = "blocos.json"
        self.metadata_arquivo = "metadata.json"
        self.data_blocos = []
        self.metadata = {}

    def carregar_dados(self):
        # Carrega a informação em byte dos blocos e o seu metadata
        f = open(self.blocos_arquivo, 'r')
        self.data_blocos = json.load(f)
        f.close()

        f = open(self.metadata_arquivo, 'r')
        self.metadata = json.load(f)
        f.close()

    # funcao para reconstruir os arquivos, recebe como parametro os dados dos blocos em base64 e o nome do arquivo de saída
    def construir_arquivo(self):
        nomeEsboco = self.metadata["nome_arquivo"]
        nomeArquivo, extensaoArquivo = os.path.splitext(nomeEsboco)
        output = f"{nomeArquivo}_reconstruido{extensaoArquivo}"
        # abre o arquivo de saída recém criado como wb (write binary), decodifica base64 em bytes e escreve os bytes, montando o arquivo
        f = open(output, 'wb')
        try:
            for bloco_b64 in self.data_blocos:
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

    def rodar(self):
        self.carregar_dados()
        self.construir_arquivo()
        # validação dos blocos, hash_blocos são os hashes originais, e 'blocos' contem os hashes dos 
        if self.verifica_construcao():
            print("Sucesso, verificação hash bem sucedida.")
        else:
            print("Falha, alguns blocos falharam a verificação hash.")

if __name__ == "__main__":
    construtor = ConstuirArquivo()
    construtor.rodar()
