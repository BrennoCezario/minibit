# Construção do arquivo - Trabalho 2 Sistemas Distribuidos

import json
import os
import hashlib
import base64

# funcao para reconstruir os arquivos, recebe como parametro os dados dos blocos em base64 e o nome do arquivo de saída
def construir_arquivo(data_blocos, output):
    # abre o arquivo de saída recém criado como wb (write binary), decodifica base64 em bytes e escreve os bytes, montando o arquivo
    f = open(output, 'wb')
    try:
        for bloco_b64 in data_blocos:
            bloco = base64.b64decode(bloco_b64)
            # bloco sao os blocos reconstruidos
            f.write(bloco)
    finally:
        f.close()

    print("Arquivo reconstruido como:", output)

# com verifica_construcao, verificamos o hash de cada bloco reconstruido com o hash que criamos quando estávamos dividindo o arquivo original em blocos
def verifica_construcao(hashes_originais, data_blocos):
    algoritmo_hash = 'sha256'
    # zip emparelha cada bloco reconstruido com o hash original, para assim podermos comparar.
    for idx, (bloco_b64, original_hash) in enumerate(zip(data_blocos, hashes_originais)):
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

if __name__ == "__main__":
    # Carrega a informação em byte dos blocos e o seu metadata
    f = open("blocos.json", 'r')
    blocos = json.load(f)
    f.close()

    f = open("metadata.json", 'r')
    metadata = json.load(f)
    f.close()

    # nome do arquivo a ser construido
    output = f"arquivo_reconstruido{metadata['extensao']}"
    construir_arquivo(blocos, output)

    # validação dos blocos, hash_blocos são os hashes originais, e 'blocos' contem os hashes dos 
    if verifica_construcao(metadata["hash_blocos"], blocos):
        print("Sucesso, verificação hash bem sucedida.")
    else:
        print("Falha, alguns blocos falharam a verificação hash.")