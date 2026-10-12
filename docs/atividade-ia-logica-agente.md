# Atividade de IA: Lógica proposicional do Agente X

**Disciplina:** COMP0506 - Fundamentos da Inteligência Artificial  
**Período / turma:** 2026.2 - T04  
**Base:** agente desenvolvido na atividade anterior (Pedestre, Motorista e Semáforo Inteligente)  

**Membros do grupo**

| Nome | Matrícula |
| --- | --- |
| Breno Murilo Alexandre Reis Santos | 202100022701 |
| Guilherme Rosário Alves | 202100022784 |
| James Pereira Matos | 202200014130 |
| João Filipe de Araujo Santos Rezende | 202100011548 |
| Manoel Victor Lima Monteiro | 202000012972 |

---

## 1. Agente e situação

**Agente:** o **Agente X**, pedestre isolado da atividade anterior.

**Situação:** com o semáforo verde para pedestres, X atravessa uma faixa de pedestres. À frente dele há um grupo de pedestres, e o vão entre o grupo e o poste da calçada é estreito. O táxi está parado antes da faixa.

---

## 2. Proposições

As percepções de X viram símbolos. Os limites numéricos são os mesmos da atividade anterior (proxêmica e largura de ombros).

| Símbolo | Significado | Como X percebe |
| --- | --- | --- |
| **P** | Há um pedestre muito próximo | Distância até o pedestre mais próximo menor que 0,8 m |
| **C** | O corredor está estreito | Vão livre menor que 1,2 m |
| **G** | O objetivo está à frente | A calçada oposta está na direção do movimento |
| **S** | O sinal está verde para pedestres | Fase do Semáforo Inteligente |
| **T** | Há um táxi sobre a faixa | Veículo ocupando a faixa de pedestres |
| **Y** | X deve ceder a passagem | Conclusão |
| **B** | X deve evitar o caminho atual | Conclusão |
| **A** | X pode avançar | Conclusão |

---

## 3. Base de conhecimento (KB)

| Regra | Fórmula | Leitura |
| --- | --- | --- |
| R1 | P ∧ C ⇒ Y | Pedestre próximo em corredor estreito: X cede |
| R2 | Y ⇒ ¬A | Quem cede não avança pelo caminho atual |
| R3 | Y ⇒ B | Quem cede procura outro caminho |
| R4 | ¬P ∧ G ∧ S ⇒ A | Caminho livre, objetivo à frente e sinal verde: X avança |
| R5 | T ∨ ¬S ⇒ ¬A | Táxi na faixa ou sinal fechado: X não avança |

**Fatos na situação:** P, C, G, S e ¬T.

**Inferência (Modus Ponens):**

1. P e C são verdadeiros; por R1, **Y**.
2. Y; por R2, **¬A**.
3. Y; por R3, **B**.
4. R4 não dispara, porque P é verdadeiro (¬P é falso).
5. R5 não dispara, porque T é falso e S é verdadeiro.

Conclusão: X **cede** e **evita o caminho atual**, que passa pelo grupo.

---

## 4. Tabela-verdade de (T ∨ ¬S) ⇒ ¬A

Regra R5 da KB. V = verdadeiro, F = falso.

| T | S | A | ¬S | T ∨ ¬S | ¬A | (T ∨ ¬S) ⇒ ¬A |
| --- | --- | --- | --- | --- | --- | --- |
| V | V | V | F | V | F | **F** |
| V | V | F | F | V | V | **V** |
| V | F | V | V | V | F | **F** |
| V | F | F | V | V | V | **V** |
| F | V | V | F | F | F | **V** |
| F | V | F | F | F | V | **V** |
| F | F | V | V | V | F | **F** |
| F | F | F | V | V | V | **V** |

A regra é violada em três linhas, todas com X avançando (A verdadeiro) quando há táxi na faixa ou o sinal está fechado. São as situações de risco que a KB proíbe. Nas linhas 5 e 6 (sem táxi e sinal verde) o antecedente é falso, e a regra não obriga nada: quem decide se X avança são as outras regras. É o caso da situação desta atividade.

---

## 5. Relação com o A*

A lógica decide **o quê** (ceder e evitar o caminho atual). O A* da atividade anterior decide **por onde**. A ligação é feita pelo custo g(n):

- **B verdadeiro:** as células perto do grupo recebem a penalidade social da atividade anterior (+5, porque a distância fica entre 0,4 m e 0,8 m).
- **¬A por R5** (táxi na faixa ou sinal fechado): as células da via ficam vermelhas e nem entram como vizinhos.

Grade de 0,5 m por célula (passo ortogonal 0,5 m, diagonal ≈ 0,71 m):

| Caminho | Distância | Penalidade | g(n) |
| --- | --- | --- | --- |
| **A:** reto, pelo vão ao lado do grupo | 8 passos ortogonais = 4,0 | +5 | **9,0** |
| **B:** contorno pelas células verdes | 8 ortogonais + 2 diagonais = 5,42 | 0 | **5,42** |

O caminho A é mais curto, mas a penalidade que a KB justificou o torna mais caro. O A* escolhe o contorno B, coerente com a conclusão lógica de que X deve ceder e evitar o caminho atual.

---

## Referências

HART, Peter E.; NILSSON, Nils J.; RAPHAEL, Bertram. A formal basis for the heuristic determination of minimum cost paths. *IEEE Transactions on Systems Science and Cybernetics*, v. 4, n. 2, p. 100-107, 1968.

RUSSELL, Stuart; NORVIG, Peter. *Artificial Intelligence: A Modern Approach*. 4. ed. Pearson, 2020.
