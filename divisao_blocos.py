# Divisão do arquivo em blocos - Trabalho 2 Sistemas Distribuidos

# No torrent original, temos a divisão de pedaços e estes pedaços são divididos em blocos, que são ainda menores.
# são os blocos que vão ter os dados do arquivo propriamente dito, os pedaços são usados para validação e outras coisas
# como é um trabalho mais simples, juntei os pedaços e blocos em um só, que são chamados de blocos.

import hashlib
import os
import json
import base64

# funcao para dividir o arquivo em blocos e criação de hash para os respectivos blocos:
# o hash serve para validação, verificar se o arquivo a ser criado é "igual" ao original
# recebe como parâmetro o nome do arquivo e tamanho em bytes dos blocos
# base64.b64encode está codificando os bytes em base64, para poder colocar no json, e decode('utf-8') converte o base64 em string normal
# retorna data_blocos que contêm base64 em string do json, isto vem da codificação dos bytes dos blocos;
# e também retorna o hash vinculado ao bloco
# digamos que temos um arquivo de 22 blocos, então data_blocos[0] guardará, em bytes, o primeiro bloco, e 
# hash_blocos[0] guardará o código hash vinculado a este bloco.
def divide_arquivo_gera_hash(arquivo, bloco_tamanho_bytes):
    data_blocos = []
    hash_blocos = []
    algoritmo_hash = 'sha256'

    f = open(arquivo, 'rb')
    try:
        while (True):
            # aqui ele vai ler o arquivo até chegar no tamanho dado, e então processar. Vai loopar até ler todo o arquivo
            bloco = f.read(bloco_tamanho_bytes)
            if not bloco:
                break
            data_blocos.append(base64.b64encode(bloco).decode('utf-8'))
            hasher = hashlib.new(algoritmo_hash)
            # esse update é para atualizar o hash com a string recebida
            hasher.update(bloco)
            hash_blocos.append(hasher.hexdigest())
    finally:
        f.close()
        
    return data_blocos, hash_blocos


if __name__ == "__main__":
    arquivo = input("Digite o nome do arquivo a ser dividido, incluindo a extensão: ")
    # Tamanho em bytes
    tamanho_bloco = 32 * 1024 # 32 KB

    blocos, hashes = divide_arquivo_gera_hash(arquivo, tamanho_bloco)
    if blocos and hashes:
        print("Tamanho do arquivo original em bytes:", os.path.getsize(arquivo))

        # criação de metadata json e blocos json
        metadata = {
            "nome_arquivo": os.path.basename(arquivo),
            "bloco_tamanho_bytes": tamanho_bloco,
            "hash_blocos": hashes,
            "numero_blocos": len(hashes),
            "extensao": os.path.splitext(arquivo)[1]
        }
        f = open("blocos.json", 'w')
        json.dump(blocos, f)
        f.close()
        f = open("metadata.json", 'w')
        json.dump(metadata, f)
        f.close()

        print("Arquivo dividido em", len(blocos), "blocos, bytes dos blocos em 'blocos.json' e metadata em 'metadata.json'.")