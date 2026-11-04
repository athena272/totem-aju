# Roteiro — Check-in 3 (04/11)

Guia rápido para a mesa: o que foi feito, o que significa, o que abrir e o que falar.

**O professor pede:** protótipo rodando, primeiras métricas e validação do pipeline.

---

## Resumo em uma frase

Protótipo do totem (site + VLibras + menu por dedos), pipeline de coleta de sinais (landmarks → dataset) e primeiro treino com métricas (K-NN e Random Forest, leave-one-signer-out).

---

## Conceitos (para não travar se perguntarem)

### Pipeline

Caminho dos dados:

**câmera → MediaPipe (landmarks) → normalização → janela de 32 quadros → `.npy` + linha no `manifest.jsonl`**

Validar o pipeline = mostrar que isso funciona de ponta a ponta.

### Amostra

Uma **execução gravada de um sinal** (um “take”).

Ex.: Alice faz `banheiro` uma vez → 1 arquivo `.npy` + 1 linha no manifest.

No treino atual: **832 amostras** = 26 sinais × 4 pessoas × 8 repetições.

### Baseline

Primeiro classificador **simples** (sem rede neural profunda), para ter números e provar que o dado tem padrão.

Aqui: **K-NN** e **Random Forest**.

### Features (`mean`)

Cada amostra é um tensor `(32, 225)`. O modelo recebe um vetor:

- **mean** (o que usamos): média no tempo → 225 números.

### K-NN

Classifica pelo “quem se parece mais comigo” (vizinhos mais próximos no espaço das features).

### Random Forest

Várias árvores de decisão votam; a maioria ganha.

### Leave-one-signer-out (LOSO)

Em cada rodada (**fold**), **uma pessoa inteira** fica só no teste; as outras treinam.

Evita o modelo “reconhecer a pessoa” em vez do sinal (vazamento).

Com 4 sinalizadores → 4 folds. Métricas finais = média ± desvio.

### Métricas

| Nome | Em uma frase |
| --- | --- |
| Accuracy | Em quantos % acertou a classe |
| Precision macro | Quando previu uma classe, com que frequência acertou (média entre classes) |
| Recall macro | Dos exemplos reais de cada classe, quantos encontrou |
| F1 macro | Equilíbrio precision/recall (bom número único) |
| Matriz de confusão | Linha = verdadeiro, coluna = previsto; diagonal = acertos |

### Como ler o `report.md`

1. **Cabeçalho** — tamanho do dataset e tipo de split  
2. **Agregado** — média ± variação (o que você cita na mesa)  
3. **Folds** — desempenho quando cada pessoa fica de fora  
4. **Matriz** — onde acertou (diagonal) e onde confundiu  

**Números desta corrida (04/11):**

| Modelo | Accuracy | F1 macro | Pasta |
| --- | --- | --- | --- |
| K-NN | 0.978 ± 0.030 | 0.977 ± 0.032 | `models/20261104T173542Z_knn_mean` |
| Random Forest | 1.000 ± 0.000 | 1.000 ± 0.000 | `models/20261104T173555Z_random_forest_mean` |

Na mesa, prefira o **Random Forest**:

`models/20261104T173555Z_random_forest_mean/report.md`

(A data no nome da pasta é `AAAAMMDDTHHMMSSZ`; a mais recente fica por último na ordem alfabética.)

---

## Antes de sair de casa / no notebook

Com o venv ativo, na raiz do projeto:

```powershell
.\.venv\Scripts\Activate.ps1
totem-train --help
totem-menu --help
```

Dois terminais:

**Terminal 1 — site**

```powershell
cd preview
python -m http.server 8000
```

Abrir: `http://localhost:8000`

**Terminal 2 — menu por dedos** (venv ativo, raiz do projeto)

```powershell
.\.venv\Scripts\Activate.ps1
totem-menu
```

Se `totem-menu` não for reconhecido, o venv não está ativo.

Abrir também:

`models/20261104T173555Z_random_forest_mean/report.md`

---

## Roteiro na mesa (~3 minutos)

| Tempo | O que fazer | O que falar |
| --- | --- | --- |
| 0:00–0:40 | Site → escolher tema → **Ver em Libras** | “Protótipo: totem com respostas curadas e VLibras.” |
| 0:40–1:30 | `totem-menu` → 1 escolha por dedos | “Enquanto o classificador de sinais evolui, a navegação já usa visão (landmarks + regras).” |
| 1:30–2:10 | Mencionar `data/` / coleta / pipeline | “Pipeline: landmarks → `.npy` + manifest; 832 amostras, 26 sinais.” |
| 2:10–3:00 | Abrir o `report.md` do RF | “Baseline K-NN e Random Forest, leave-one-signer-out; RF com 100% de accuracy e F1 nesta corrida.” |

### Frase de fechamento

```
Validamos o pipeline de landmarks, o protótipo já roda com toque, VLibras e menu por dedos, e temos o primeiro baseline com métricas em leave-one-signer-out. A coleta com sinalizadores reais e a ligação do classificador ao preview são os próximos passos.
```

### Se perguntarem do 100% do Random Forest

```
Nos dados atuais o RF ficou muito alto; tratamos como validação do método. A métrica que importa no artigo é em pessoas nunca vistas, com coleta real.
```

### Três números para decorar

1. **832** amostras  
2. **K-NN ~98%** / **RF 100%** (accuracy)  
3. **4 folds** leave-one-signer-out  

---

## Plano B

| Problema | O que fazer |
| --- | --- |
| Câmera / `totem-menu` falha | Só toque + VLibras no site (ainda é protótipo) |
| Porta 8000 ocupada | `python -m http.server 8080` ou `8888` |
| Sem tempo de treinar de novo | Mostrar o `report.md` já gerado (não precisa rodar `totem-train` na frente) |
| Pedirem para rodar o treino | `totem-train --model random_forest --features mean` (mais rápido que `--model all`) |

---

## O que não precisa na mesa

- CNN / PyTorch  
- Quiosque físico  
- Todos os 26 sinais ao vivo  
- Abrir o `model.joblib` (é o modelo salvo; não precisa “ler”)  

---

## Comandos úteis (copiar e colar)

```powershell
.\.venv\Scripts\Activate.ps1
totem-train --model all --features mean
totem-capture --sign ola --signer guilherme --repetitions 3
totem-menu
cd preview; python -m http.server 8000
```
