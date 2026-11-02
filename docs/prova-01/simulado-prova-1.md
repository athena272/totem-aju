# Simulado - Prova 1 (COMP0506)

Formato da prova real: três questões objetivas com enunciado em comum, uma questão discursiva de busca e uma de lógica. Resolva antes de olhar o gabarito, que está no fim.

---

## Enunciado comum (questões 1 a 3)

O **MiauBot** é um robô em forma de gato que circula pelo campus da universidade. Os objetivos dele são:

- visitar os comedouros dos gatos do campus para conferir se há comida;
- não esbarrar nas pessoas;
- voltar à base para recarregar quando a bateria estiver baixa.

Ele percebe o mundo assim:

- uma **câmera frontal de 120°**;
- um **sensor de proximidade**;
- **GPS**;
- o **nível da bateria**.

Ele age com **quatro patas motorizadas** e um **alto-falante** que mia. Pelo campus passam estudantes, carros e outros gatos. Em dias de chuva, o chão fica molhado e às vezes as patas escorregam, fazendo o robô parar num lugar diferente do planejado.

### Questão 1 (objetiva)

Qual é a classificação correta do ambiente do MiauBot?

a) Totalmente observável, determinístico, estático, discreto, agente único.  
b) Parcialmente observável, estocástico, dinâmico, contínuo, multiagente.  
c) Parcialmente observável, determinístico, dinâmico, discreto, agente único.  
d) Totalmente observável, estocástico, semidinâmico, contínuo, multiagente.  
e) Parcialmente observável, estocástico, estático, contínuo, agente único.

### Questão 2 (objetiva)

O MiauBot vai usar A* para ir da base até um comedouro. Qual é a melhor escolha de h(n)?

a) O número de comedouros já visitados.  
b) A distância em linha reta de n até o comedouro.  
c) Três vezes a distância em linha reta de n até o comedouro.  
d) O custo do caminho já percorrido desde a base até n.  
e) O número de pessoas que a câmera vê em n.

### Questão 3 (objetiva)

Qual das afirmações sobre o MiauBot é **FALSA**?

a) Como a câmera só vê 120° à frente, o MiauBot não conhece o estado completo do campus.  
b) A medida de desempenho pode somar pontos pelos comedouros visitados e descontar pontos por colisões.  
c) Como as pessoas se movem enquanto o MiauBot decide, o ambiente é dinâmico.  
d) Usando A* com h = distância em linha reta, o MiauBot pode parar assim que o comedouro aparecer na lista de espera, porque esse já é o melhor caminho.  
e) O chão molhado faz a mesma ação ter resultados diferentes, o que torna o ambiente estocástico.

---

## Questão 4 (discursiva): busca

O MiauBot está na **Base (S)** e quer chegar ao **Comedouro (G)**. As distâncias entre os pontos são:

| Ligação | Distância |
| --- | --- |
| S até Biblioteca (B) | 3 |
| S até Cantina (C) | 2 |
| B até Didática (D) | 2 |
| B até G | 6 |
| C até G | 3 |
| D até G | 2 |

No horário do almoço, a Cantina está lotada. **Entrar em C custa uma penalidade de +6** (multidão).

Distância em linha reta até G: h(S) = 4, h(B) = 4, h(C) = 3, h(D) = 2, h(G) = 0.

a) Monte a tabela **PEAS** do MiauBot.  
b) Explique como você definiu **g(n)** e **h(n)**, e por que esse h é admissível.  
c) Resolva com **A***, mostrando a lista de espera a cada passo. Dê o caminho e o custo.  
d) Resolva com **busca em largura**, com os filhos em ordem alfabética e o teste do objetivo quando o nó sai da fila. Dê o caminho e o custo.  
e) Compare os dois resultados. Faça também a conta do caminho que passa pela Cantina (distância + penalidade).

---

## Questão 5 (discursiva): lógica

Proposições:

- **M**: há multidão na Cantina;
- **R**: está chovendo (o caminho da Cantina é descoberto);
- **V**: o MiauBot segue pela Cantina.

A base de conhecimento tem a regra **(M ∨ R) ⇒ ¬V**.

a) Monte a tabela-verdade da regra. Em quais linhas ela é violada, e o que essas linhas significam?  
b) Compare o caminho ideal com o caminho falho da questão 4. Se o MiauBot **já estivesse dentro da Cantina** quando a multidão chegou, o que o algoritmo faria?

---

## Gabarito

### Questão 1: b

Responda com as perguntas de sempre:

- **Observabilidade:** a câmera de 120° não vê tudo, então é **parcialmente observável**.
- **Determinismo:** a pata escorrega e a mesma ação dá resultados diferentes, então é **estocástico**.
- **Dinâmica:** as pessoas andam enquanto ele pensa, então é **dinâmico**.
- **Valores:** posição e velocidade num campus são **contínuas**.
- **Agentes:** há estudantes, carros e outros gatos, então é **multiagente**.

As outras alternativas erram: a) quase tudo; c) determinístico, discreto e agente único; d) totalmente observável e semidinâmico; e) estático e agente único.

### Questão 2: b

- A distância em linha reta **nunca é maior** que o caminho real, então é **admissível** e o A* continua achando o melhor caminho.
- a) e e) não medem quanto falta para chegar.
- c) **superestima** o que falta, e o A* pode perder o caminho ótimo.
- d) é o **g(n)** (o que já foi andado), não o h.

### Questão 3: d (é a falsa)

O A* **não para** quando o objetivo entra na lista. Ele para quando o objetivo é **escolhido**, ou seja, quando é o de menor f. A questão 4 mostra isso: G entra na lista com f = 9, mas a resposta certa é 7.

### Questão 4

**a) PEAS**

| Letra | MiauBot |
| --- | --- |
| Desempenho | Comedouros visitados, nenhuma colisão, bateria nunca zerada, menor distância e tempo |
| Ambiente | Campus (caminhos, prédios, cantina), pessoas, carros, outros gatos, clima |
| Atuadores | Patas motorizadas e alto-falante |
| Sensores | Câmera de 120°, sensor de proximidade, GPS e nível da bateria |

**b) g e h**

- **g(n)** = distância percorrida desde a base + penalidades (+6 ao entrar na Cantina lotada).
- **h(n)** = distância em linha reta de n até G.
- **Por que é admissível:** a linha reta nunca é maior que o caminho real. A penalidade fica **só no g**, para o h nunca superestimar.

**c) A\***

| Passo | Escolhe | Vizinhos abertos (g + h = f) | Lista de espera depois do passo |
| --- | --- | --- | --- |
| 1 | S (f = 4) | B: 3 + 4 = **7**; C: (2 + 6) + 3 = **11** | B (7), C (11) |
| 2 | B (f = 7) | D: 5 + 2 = **7**; G: 9 + 0 = **9** | D (7), G (9), C (11) |
| 3 | D (f = 7) | G: 7 + 0 = **7** | G (7), G (9), C (11) |
| 4 | G (f = 7) | É o objetivo: fim | |

No passo 2, G apareceu com f = 9, mas **não foi escolhido**, porque D (7) era menor.

**Resposta: S → B → D → G, com custo 7.** Conferindo: 3 + 2 + 2 = 7.

**d) Busca em largura** (a fila sai pela esquerda e entra pela direita)

| Passo | Tira da fila | Fila depois do passo |
| --- | --- | --- |
| 1 | S | [B, C] |
| 2 | B | [C, D, G] |
| 3 | C (G já está na fila) | [D, G] |
| 4 | D (G já está na fila) | [G] |
| 5 | G: objetivo | |

**Resposta: S → B → G**, com 2 passos e custo 3 + 6 = **9**.

**e) Comparação**

- A **largura** acha o caminho com **menos passos** (2), mas ignora custos e penalidades. O custo dele é 9.
- O **A*** acha o caminho **mais barato** (3 passos, custo 7), porque soma custos e penalidades em g.
- **Caminho pela Cantina, S → C → G:** também tem 2 passos. A conta é 2 + 3 = 5 de distância, mais 6 de penalidade, dando **11**. É o mais curto em distância, mas o mais caro. Se a ordem dos filhos fosse C antes de B, a largura teria escolhido exatamente esse caminho, passando pela multidão.
- A largura também gasta mais memória, porque guarda todos os nós de cada nível.

### Questão 5

**a) Tabela-verdade de (M ∨ R) ⇒ ¬V** (3 variáveis, 8 linhas)

| M | R | V | M ∨ R | ¬V | (M ∨ R) ⇒ ¬V |
| --- | --- | --- | --- | --- | --- |
| V | V | V | V | F | **F** |
| V | V | F | V | V | V |
| V | F | V | V | F | **F** |
| V | F | F | V | V | V |
| F | V | V | V | F | **F** |
| F | V | F | V | V | V |
| F | F | V | F | F | V |
| F | F | F | F | V | V |

A regra é **violada nas linhas 1, 3 e 5**. São os casos em que o MiauBot **segue pela Cantina (V verdadeiro)** mesmo havendo multidão ou chuva. O ⇒ só é falso em **V ⇒ F**. Nas linhas 7 e 8, sem multidão e sem chuva, a regra não proíbe nada, e ele pode passar pela Cantina.

**b) Caminho ideal versus caminho falho**

- **Caminho falho:** S → C → G, com custo 11. A regra proíbe esse caminho quando M é verdadeiro, e o A* traduz isso na penalidade +6 em g.
- **Caminho ideal:** S → B → D → G, com custo 7.
- **Durante o planejamento:** o ramo da Cantina fica com f = 11, maior que os outros. O A* nunca o escolhe e segue pelo caminho mais barato.
- **Se o MiauBot já estivesse dentro da Cantina:** como o ambiente é dinâmico, ele **replaneja a partir de onde está**. O que já foi gasto não volta, e a penalidade de entrar já foi paga. De C, as opções são ir direto para G (custo **3**) ou voltar para S e dar a volta por B e D (2 + 3 + 2 + 2 = **9**). O A* escolhe **sair direto para G**.
