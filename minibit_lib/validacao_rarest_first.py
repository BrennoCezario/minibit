from collections import Counter # Usado para contar ocorrencias de forma mais simples

# Classe RarestFirst para validar os pedaços mais raros para escolher.
# Assume que serão passados os peers com os pedaços possuidos, além de passar os pedaços que o usuario possui.
# Realiza a verificação dos pedaços totais validando se o usuario possui algum deles e conta os mesmos para descobrir o mais raro.
# Sabendo o mais raro retorna na função retorna_pedaco_raro

class RarestFirst:
    def __init__(self, peers_e_pedacos, pedacos_possuidos):
        self.peers_e_pedacos = peers_e_pedacos # DICIONARIO, do modo 'STRING':'LISTA' -> Exemplo: 'Peer_1':[1,2,3,4]
        self.pedacos_possuidos = pedacos_possuidos # LISTA, do modo [1,2,3]

    def retorna_pedaco_raro(self):

        # Todos os pedaços dos peers exceto o usuario
        todos_pedacos = []

        # Utilizando extend para ampliar a lista incluindo os novos valores em uma unica lista
        for pedacos in self.peers_e_pedacos.values():
            todos_pedacos.extend(pedacos)

        # Filtragem para validar apenas os pedaços que o usuário ainda não tem
        pedacos_necessarios = [pedaco for pedaco in todos_pedacos if pedaco not in self.pedacos_possuidos]

        # Como most_common ordena pela frequencia, aqui eu pego o ultimo elemento que é o mais raro, no caso (ELEMENTO, FREQUENCIA) então pego o indice [0] também
        return Counter(pedacos_necessarios).most_common()[-1][0]

# Main para testes locais
if __name__ == "__main__":

    Rarest_First_1 = RarestFirst({
    'peer1': [1, 2, 3, 4],
    'peer2': [2, 3, 5],
    'peer4': [3, 4, 5, 6],
    'peer5': [2, 6],
},[2, 3])

    print(Rarest_First_1.retorna_pedaco_raro())