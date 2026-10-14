# Arquitetura do Totem Aju

## Visão geral

O totem é composto por um monitor com touchscreen, uma webcam e um computador.
O software se divide em três camadas com fronteiras bem definidas:

```mermaid
flowchart TB
    subgraph entrada [Entrada: turista surdo sinaliza]
        Cam[Webcam] --> Extractor[LandmarkExtractor]
        Extractor --> Norm[Normalizacao]
        Norm --> Buffer[SequenceBuffer]
        Buffer --> Clf[Classificador temporal]
    end

    subgraph dominio [Dominio: decidir a resposta]
        Clf --> Intencao[Intencao reconhecida]
        Intencao --> Base[Base de conhecimento turistico curada]
        Base --> Resposta[Resposta em portugues]
    end

    subgraph saida [Saida: totem responde]
        Resposta --> Texto[Texto na tela]
        Resposta --> VLibras[VLibras: avatar em Libras]
    end
```

## Princípio estruturante: o domínio não conhece a infraestrutura

A regra que orienta a organização do código é a **inversão de dependência**:
a lógica de negócio depende de abstrações, nunca de bibliotecas concretas.

Concretamente, `vision/extractor.py` define um `Protocol`:

```python
class LandmarkExtractor(Protocol):
    def extract(self, frame: NDArray[np.uint8]) -> FrameLandmarks: ...
```

E `vision/mediapipe_extractor.py` é uma implementação desse contrato, que importa
o MediaPipe **de forma preguiçosa**, dentro do construtor.

Isso não é preciosismo arquitetural; resolve três problemas concretos:

1. **MediaPipe não instala em qualquer Python.** Só há wheels para 3.9–3.12.
   Com o import preguiçoso, a suíte de testes e toda a lógica de pré-processamento
   rodam em qualquer versão, sem MediaPipe instalado.
2. **Testes não podem depender de webcam.** Um `FakeExtractor` que devolve
   landmarks sintéticos permite testar o pipeline inteiro de forma determinística.
3. **A equipe trabalha em paralelo.** Quem cuida do classificador não precisa ter
   a captura funcionando na sua máquina.

## Camadas e responsabilidades

| Módulo | Responsabilidade | Não sabe sobre |
| --- | --- | --- |
| `vision/schema.py` | Estrutura de dados de um quadro de landmarks | Webcam, MediaPipe, disco |
| `vision/extractor.py` | Contrato de extração | Qualquer implementação concreta |
| `vision/mediapipe_extractor.py` | Adaptar MediaPipe ao contrato | Normalização, dataset |
| `vision/normalization.py` | Funções puras de normalização geométrica | Webcam, tempo, disco |
| `vision/sequence.py` | Acumular quadros numa janela temporal | O que é um sinal |
| `data/manifest.py` | Registro persistente das amostras | O que é um landmark |
| `data/recorder.py` | Orquestrar captura para o disco | MediaPipe (recebe o Protocol) |
| `cli/capture.py` | Interação com o operador da coleta | Regras de normalização |
| `vision/heuristics.py` | Dedos abertos por geometria 3D dos landmarks | Webcam, menu, site |
| `menu/selector.py` | Confirmar uma contagem mantida parada | Webcam, disco, significado do número |
| `menu/state.py` | Gravar o estado da câmera para o preview | Categorias e assuntos do site |
| `menu/session.py` | Loop câmera → contagem → escolha → estado | MediaPipe (recebe o Protocol) |
| `cli/menu.py` | Janela com retorno visual e mensagens de erro | Regras de confirmação |
| `preview/js/gesture-menu.js` | Significado do número em cada nível do menu | Webcam, Python |

## Menu por dedos

O menu por dedos liga a webcam ao preview sem servidor de aplicação. O Python
só percebe a mão: conta os dedos, confirma a contagem mantida parada por cerca
de 1 segundo e grava o estado em `preview/gesture_state.json`. O site lê esse
arquivo por polling e decide o que o número significa no nível atual do menu.
Assim, mudar categorias ou assuntos no `knowledge.json` não exige mudar o Python.

```mermaid
flowchart LR
    Cam[Webcam] --> Ext[MediaPipeHolisticExtractor]
    Ext --> Counter[HeuristicFingerCounter]
    Counter --> Sel[FingerHoldSelector]
    Sel --> Pub[GestureStatePublisher]
    Pub -->|"escrita atômica"| File["preview/gesture_state.json"]
    File -->|"polling 250 ms"| Feed["gesture-feed.js"]
    Feed --> Menu["gesture-menu.js"]
    Menu --> App["app.js"]
```

Decisões que evitam falhas difíceis de reproduzir:

- **Tempo, não quadros.** O MediaPipe Holistic em CPU roda de 7 a 20 quadros por
  segundo conforme o computador. O tempo de segurar é medido em segundos, para
  ser o mesmo em qualquer máquina.
- **Trava contra repetição.** Depois de escolher um número, o mesmo número só
  vale de novo quando a mão sai do quadro. Sem isso, quem escolhe a categoria 3
  e continua com a mão parada escolheria o assunto 3 sem querer.
- **Escrita atômica com nova tentativa.** O estado é gravado num arquivo
  temporário e substituído de uma vez, para o site nunca ler um JSON pela metade.
  No Windows, a substituição falha por alguns milissegundos enquanto o servidor
  lê o arquivo; o publisher tenta de novo antes de desistir.
- **Escolha com identificador.** Cada escolha tem um `event_id` e continua no
  arquivo nas gravações seguintes. Uma gravação perdida não perde a escolha, e o
  site aplica cada uma só uma vez, inclusive ao recarregar a página.
- **Sempre há retorno.** O rodapé do site mostra se a câmera está iniciando,
  procurando a mão, segurando, sem resposta, encerrada ou com erro.

## Por que normalizar os landmarks

O MediaPipe devolve coordenadas relativas ao quadro da imagem. Isso significa que
o *mesmo* sinal produz vetores completamente diferentes se a pessoa estiver mais
à esquerda ou mais distante da câmera. Sem tratamento, o modelo gastaria dados
aprendendo a ignorar posição e distância.

A normalização aplicada é geométrica e determinística:

1. **Translação:** subtrair a posição do pulso, tornando o pulso a origem.
2. **Escala:** dividir pela distância pulso–base do dedo médio, tornando a
   representação invariante ao tamanho da mão na imagem.

O efeito prático é reduzir drasticamente a quantidade de dados necessária — o que
é exatamente o que viabiliza o projeto num semestre. Como são funções puras, as
duas propriedades (invariância a translação e a escala) são verificadas
diretamente por testes unitários.

## Por que reamostrar a sequência

Duas pessoas executam o mesmo sinal em durações diferentes, e a mesma pessoa varia
entre repetições. O classificador, porém, exige tensores de formato fixo.

O `SequenceBuffer` mantém uma janela deslizante e produz sempre uma sequência de
comprimento canônico (`SEQUENCE_LENGTH`) por interpolação linear ao longo do eixo
temporal, preservando o primeiro e o último quadro.

## Por que o manifest registra o sinalizador

Cada amostra gravada anota o identificador de quem sinalizou. Isso é obrigatório,
não opcional: no treino, a divisão entre treino e teste precisa ser feita **por
pessoa**. Se quadros da mesma pessoa aparecerem nos dois conjuntos, o modelo
reconhece a pessoa em vez do sinal, e a acurácia relatada no artigo estaria
inflada por vazamento de dados — um erro metodológico grave e fácil de cometer.

O formato é JSON Lines (`manifest.jsonl`), append-only: uma amostra por linha.
Se a coleta for interrompida com Ctrl+C, perde-se no máximo a última linha, em
vez de corromper um JSON inteiro.

## Fluxo de dados da coleta

```mermaid
sequenceDiagram
    participant Op as Operador
    participant CLI as cli/capture
    participant Rec as data/recorder
    participant Ext as LandmarkExtractor
    participant FS as Disco

    Op->>CLI: informa sinal e id do sinalizador
    CLI->>Rec: record_sample()
    loop cada quadro da janela
        Rec->>Ext: extract(frame)
        Ext-->>Rec: FrameLandmarks
        Rec->>Rec: normaliza e acumula
    end
    Rec->>FS: grava .npy
    Rec->>FS: adiciona linha ao manifest.jsonl
    Rec-->>CLI: SampleRecord
    CLI-->>Op: confirmacao
```

## Decisões de plataforma

O descarte do Virtual Human Toolkit e do Unity está registrado em
[`adr/0001-descartar-virtual-human-toolkit-e-unity.md`](adr/0001-descartar-virtual-human-toolkit-e-unity.md).

Ambiente: **Python 3.12** (limite imposto pelo MediaPipe), dependências fixadas
em `requirements.txt`, ambiente virtual em `.venv`.

## Cronograma

| Período | Entrega |
| --- | --- |
| até 03/09 | Checkpoint: equipe, tema e justificativa definidos |
| setembro | Coleta do dataset e pipeline de extração de landmarks |
| outubro | Treino e avaliação do classificador; integração do VLibras |
| início de novembro | Montagem do quiosque e testes com usuários surdos |
| 23–25/11 | Apresentação final e artigo |

## Fora do escopo desta fase

Treino do classificador, back-end FastAPI, integração do VLibras e front-end de
quiosque. A fundação e a coleta vêm primeiro porque **dado é o caminho crítico**:
sem amostras gravadas, nenhuma das etapas seguintes pode começar.
