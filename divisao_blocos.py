# Divisão do arquivo em blocos - Trabalho 2 Sistemas Distribuidos

# No torrent original, temos a divisão de pedaços e estes pedaços são divididos em blocos, que são ainda menores.
# são os blocos que vão ter os dados do arquivo propriamente dito, os pedaços são usados para validação e outras coisas
# como é um trabalho mais simples, juntei os pedaços e blocos em um só, que são chamados de blocos.

import hashlib
import os
import json
import base64

CAMINHO_ARQUIVO = os.path.abspath(os.path.join(os.path.abspath(__file__), "..", "arquivos"))

# funcao para dividir o arquivo em blocos e criação de hash para os respectivos blocos:
# o hash serve para validação, verificar se o arquivo a ser criado é "igual" ao original
# recebe como parâmetro o nome do arquivo e tamanho em bytes dos blocos
# base64.b64encode está codificando os bytes em base64, para poder colocar no json, e decode('utf-8') converte o base64 em string normal
# retorna data_blocos que contêm base64 em string do json, isto vem da codificação dos bytes dos blocos;
# e também retorna o hash vinculado ao bloco
# digamos que temos um arquivo de 22 blocos, então data_blocos[0] guardará, em bytes, o primeiro bloco, e 
# hash_blocos[0] guardará o código hash vinculado a este bloco.
class DivisaoBlocos:
    def __init__(self, arquivo):
        self.arquivo = os.path.abspath(os.path.join(CAMINHO_ARQUIVO, arquivo))
        self.tamanho_bloco = 32 * 1024 # Tamanho em bytes, 32 KB
        self.algoritmo_hash = 'sha256'
        self.data_blocos = []
        self.hash_blocos = []
        self.metadata = {}

    def divide_e_hash(self):
        self.data_blocos = []
        self.hash_blocos = []
        
        f = open(self.arquivo, 'rb')
        try:
            while(True):
                # aqui ele vai ler o arquivo até chegar no tamanho dado, e então processar. Vai loopar até ler todo o arquivo
                bloco = f.read(self.tamanho_bloco)
                if not bloco:
                    break
                self.data_blocos.append(base64.b64encode(bloco).decode('utf-8'))
                hasher = hashlib.new(self.algoritmo_hash)
                # esse update é para atualizar o hash com a string recebida
                hasher.update(bloco)
                self.hash_blocos.append(hasher.hexdigest())
        finally:
            f.close()
        self.metadata = {
            "nome_arquivo": os.path.basename(self.arquivo),
            "bloco_tamanho_bytes": self.tamanho_bloco,
            "hash_blocos": self.hash_blocos,
            "numero_blocos": len(self.hash_blocos),
            "extensao": os.path.splitext(self.arquivo)[1]
        }

    def gravar_dados(self):
        # criação de metadata json e blocos json
        blocos_arquivo = "blocos.json"
        metadata_arquivo = "metadata.json"
        f = open(blocos_arquivo, 'w')
        json.dump(self.data_blocos, f)
        f.close()
        f = open(metadata_arquivo, 'w')
        json.dump(self.metadata, f)
        f.close()

    def rodar(self):
        self.divide_e_hash()
        self.gravar_dados()
        print("Arquivo", self.arquivo, "dividido em", len(self.data_blocos), "blocos, bytes dos blocos em 'blocos.json' e metadata em 'metadata.json'.")

if __name__ == "__main__":
    arquivo = input("Digite o nome do arquivo a ser dividido, incluindo a extensão: ")

    dividir = DivisaoBlocos(arquivo)
    dividir.rodar()
