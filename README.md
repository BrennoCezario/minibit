# Minibit

Implementação de um Sistema de Compartilhamento Cooperativo de Arquivos com Estratégias Distribuídas.

## Diagrama da arquitetura

## Protocolo de comunicação

A comunicação entre peers e o tracker no sistema ocorre através de sockets.

O tracker inicia e aguarda a entrada dos peers na rede. Todos os peers antes de entrar na rede iniciam o servidor para aceitar conexões do tipo cliente e cada um deles, inclusive o tracker, se conectam entre si, formando assim uma rede com diversos servidores e clientes.

Ao iniciar o servidor, algumas threads são iniciadas:

1. Uma thread para iniciar o processador das mensagens  que verifica a "caixa postal" do peer e processa cada mensagem que recebeu;

2. Uma thread que ativa o ativo de estoque de blocos de forma constante e atualizada;

3. Uma thread que ativa o recebimento e o enpacotamento de novas mensagens na caixa postal do peer até que a conexão seja encerrada.

As mensagens trocadas entre os peers seguem o padrão JSON e possuem um atributo "tipo" que define como a mensagem será tratada. Os tipos que são reconhecidos no sistema:

1. REGISTRO -> Solicitação de registro de um cliente em um servidor;

2. ESTOQUE -> Mensagem de envio de estoque de um peer para o outro;

3. PEDIDO -> Mensagem de pedido de bloco, um peer solicita um bloco para o outro;

4. NOVO_PEER -> Mensagem que mostra um novo peer que entrou na rede;

5. LISTA_PEERS -> Mensagem que mostra a um peer novo na rede todos os outros que já estão lá para ele se conectar com eles;

6. BLOCO -> Mensagem que possui o bloco que um peer está enviando para o outro.

## Estratégia para rarest first e tit-for-tat

## Resultados de testes

**• Exemplo de Execução:**
![alt text](img/image-13.png)

![alt text](img/image-15.png)

**• Resultado com imagem (PNG):**

![alt text](img/image-22.png)

![alt text](img/image-23.png)

![alt text](img/image-24.png)

![alt text](img/image-25.png)

![alt text](img/image-26.png)

![alt text](img/image-27.png)

**• Resultado com documento (PDF):**

![alt text](img/image.png)

![alt text](img/image-1.png)

![alt text](img/image-2.png)

![alt text](img/image-3.png)

![alt text](img/image-4.png)

![alt text](img/image-34.png)

**• Resultado com música (MP3):**

![alt text](img/image-28.png)

![alt text](img/image-29.png)

![alt text](img/image-30.png)

![alt text](img/image-31.png)

![alt text](img/image-32.png)

![alt text](img/image-33.png)

**• Resultado com vídeo (MP4):**`

![alt text](img/image-16.png)

![alt text](img/image-17.png)

![alt text](img/image-18.png)

![alt text](img/image-19.png)

![alt text](img/image-20.png)

![alt text](img/image-21.png)

## Dificuldades Enfrentadas

## Reflexão Individual

**• Artur:**

**• Brenno:** 
A tarefa de implementar um sistema que simula o BitTorrent foi muito interessante e ensinou bastante sobre o funcionamento de uma rede P2P. Também foi ótimo poder aperfeiçoar e entender melhor as comunicações por socket, que foram muito utilizadas em nosso sistema. O algoritmo foi desafiador, mas foi gratificante conseguir superar as diversas dificuldades da implementação. Para o aprendizado foi ótimo. A maior dificuldade foi conseguir alinhar cada etapa com a equipe, pois houve desafios relacionados à forma como o trabalho foi dividido entre os participantes. Cada integrante tem seu próprio estilo de codificação e organização, o que acabou tornando o entendimento do código dos colegas um pouco mais complexo. Além disso, foi necessário aguardar atualizações ou correções de partes específicas para que outras pudessem avançar, o que impactou no ritmo de desenvolvimento. Apesar disso, a experiência foi valiosa para compreender melhor a importância da comunicação e da coordenação em projetos colaborativos.

**• Paulo José:**

**• Pedro Paulo:**
