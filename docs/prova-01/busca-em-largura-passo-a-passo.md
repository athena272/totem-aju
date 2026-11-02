# Busca em largura, passo a passo

A busca em largura é **mais simples que o A***: ela **não usa g, h nem f**. Só usa uma **fila**, como a de um banco: quem chegou primeiro sai primeiro.

---

## A regra, repetida em todo passo

1. **Tire o primeiro** da fila (o da esquerda).
2. Se ele for o **objetivo, pare**.
3. Se não for, coloque os **filhos dele no fim** da fila (à direita). Pule os que **já apareceram** antes.
4. Anote **quem trouxe** cada filho (o "pai"). É assim que você descobre o caminho no fim.

Ela anda em **camadas**: primeiro tudo que fica a 1 passo da saída, depois tudo que fica a 2 passos, e assim por diante.

---

## Exemplo: o grafo do simulado

Ligações: S–B, S–C, B–D, B–G, C–G e D–G. Os filhos entram em ordem alfabética, e os custos **não importam** aqui.

| Passo | Tira da fila | É o objetivo? | Filhos novos (e quem trouxe) | Fila depois do passo |
| --- | --- | --- | --- | --- |
| início | | | | [S] |
| 1 | S | Não | B e C (vieram de S) | [B, C] |
| 2 | B | Não | D e G (vieram de B); S já apareceu | [C, D, G] |
| 3 | C | Não | Nenhum: G já está na fila | [D, G] |
| 4 | D | Não | Nenhum: G já está na fila | [G] |
| 5 | G | **Sim: fim** | | |

### Montando o caminho: volte pelos pais

- G veio de **B**.
- B veio de **S**.

Lendo de trás para frente: **S → B → G**, com **2 passos**. Se a questão pedir o custo, some as estradas: 3 + 6 = **9**.

---

## Comparação com o A* (o que a questão 4 da prova pede)

| Algoritmo | O que ele procura | Caminho | Passos | Custo |
| --- | --- | --- | --- | --- |
| Largura | O caminho com **menos passos**, ignorando custos | S → B → G | 2 | 9 |
| A* | O caminho **mais barato** (f = g + h) | S → B → D → G | 3 | 7 |

O mesmo acontece na Romênia. A largura encontra **Arad → Sibiu → Fagaras → Bucareste**, com só 3 estradas, mas custo 140 + 99 + 211 = **450**. O A* encontra o caminho de **418** (Arad → Sibiu → Rimnicu Vilcea → Pitesti → Bucareste), que tem 4 estradas, mas é mais barato.

A largura também gasta muita memória, porque guarda na fila todos os nós de cada camada.

---

## Dois cuidados

- **Quando parar:** neste material, a largura para quando o objetivo **sai da fila**, igual ao A*. Algumas versões, inclusive a do livro, param assim que o objetivo **entra na fila**, o que economiza passos. O caminho encontrado é o mesmo. Na prova, siga a convenção do enunciado ou a dos slides do professor.
- **Fila versus pilha:** a busca em profundidade faz exatamente o mesmo processo, mas com uma **pilha**, em que o último a entrar é o primeiro a sair. Se a questão pedir as duas, só muda de onde você tira o próximo.
