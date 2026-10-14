# Totem Aju

[![CI](https://github.com/athena272/totem-aju/actions/workflows/ci.yml/badge.svg)](https://github.com/athena272/totem-aju/actions/workflows/ci.yml)

Totem interativo de acessibilidade comunicacional em **Libras** para turistas
surdos em Aracaju, Sergipe.

Projeto prático da disciplina de Inteligência Artificial, na linha de **Visão
Computacional** aplicada a **fomento ao turismo e preservação cultural**.

## O problema

Pessoas surdas que visitam Aracaju não têm como obter informação turística
básica — onde fica um banheiro, como chegar à Orla de Atalaia, qual ônibus tomar
— em sua própria língua. A acessibilidade comunicacional em espaços públicos não
é uma cortesia: é obrigação prevista na Lei de Libras (10.436/2002) e na Lei
Brasileira de Inclusão (13.146/2015).

O totem atende os dois sentidos da comunicação:

| Sentido | Solução |
| --- | --- |
| Turista surdo → totem | Reconhecimento de sinais em Libras por visão computacional (contribuição técnica deste trabalho) |
| Totem → turista surdo | [VLibras](https://www.gov.br/governodigital/pt-br/vlibras) traduzindo a resposta para Libras num avatar 3D, junto com o texto em português |

## Como funciona

```mermaid
flowchart LR
    Cam[Webcam] --> Ext[MediaPipe Holistic]
    Ext --> Norm[Normalizacao geometrica]
    Norm --> Buf[Janela temporal fixa]
    Buf --> Clf[Classificador temporal]
    Clf --> Base[Base de conhecimento curada]
    Base --> Out[Texto + avatar VLibras]
```

Em vez de trabalhar com pixels crus, o pipeline extrai *landmarks* de mãos, corpo
e face e os normaliza geometricamente. Isso reduz drasticamente a quantidade de
dados necessária e permite operação em tempo real na CPU, sem GPU dedicada.

O recorte do problema é deliberado: **vocabulário fechado** de 26 sinais do
domínio turístico, em vez de Libras contínua irrestrita (que é problema de
pesquisa aberto). Ver [`docs/vocabulario-sinais.md`](docs/vocabulario-sinais.md).

## Documentação

| Documento | Conteúdo |
| --- | --- |
| [`docs/adr/0001-descartar-virtual-human-toolkit-e-unity.md`](docs/adr/0001-descartar-virtual-human-toolkit-e-unity.md) | Por que não usamos o Virtual Human Toolkit nem Unity |
| [`docs/arquitetura.md`](docs/arquitetura.md) | Camadas, responsabilidades e cronograma |
| [`docs/vocabulario-sinais.md`](docs/vocabulario-sinais.md) | Os 26 sinais e as regras de coleta |
| [`docs/terminologia-e-etica.md`](docs/terminologia-e-etica.md) | Terminologia correta, riscos éticos e diretrizes CAPES/MEC |

## Requisitos

**Python 3.12.** O MediaPipe não publica wheels para 3.13 nem 3.14, e compilar
da fonte no Windows não é viável. O 3.12 conviverá sem conflito com outras
versões já instaladas.

## Instalação (Windows / PowerShell)

```powershell
winget install Python.Python.3.12

git clone <url-do-repositorio>
cd totem-aju

py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .
```

Se o `Activate.ps1` for bloqueado pela política de execução:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Em Linux ou macOS, troque a ativação por `source .venv/bin/activate`.

> **Não instale `opencv-python`.** O MediaPipe já depende de
> `opencv-contrib-python`, e as duas distribuições instalam o mesmo módulo
> `cv2`, sobrescrevendo uma à outra.

## Coleta de dados

O vocabulário e a contagem de repetições:

```powershell
totem-capture --list-signs
```

Gravando 20 repetições de um sinal:

```powershell
totem-capture --sign banheiro --signer seu_nome --repetitions 20
```

O parâmetro `--signer` é **obrigatório e importa**: a divisão entre treino e
teste precisa ser feita por pessoa. Se quadros da mesma pessoa caírem nos dois
conjuntos, o modelo aprende a reconhecer a pessoa em vez do sinal, e a acurácia
relatada fica inflada por vazamento de dados.

As amostras vão para `data/`, que é ignorada pelo git: são arquivos binários
grandes e podem conter dados pessoais identificáveis.

Ao gravar, enquadre cabeça e tronco com folga nas bordas para as mãos, e varie
iluminação, distância e fundo entre as sessões. O CLI avisa quando uma amostra
teve baixa taxa de detecção, indicando enquadramento ruim.

## Preview do totem (apresentável agora)

Há um protótipo visual em [`preview/`](preview/) com categorias, respostas
curadas de Aracaju e o widget oficial do **VLibras**. A navegação funciona por
toque e, opcionalmente, pelo **menu por dedos** (seção abaixo).

Na pasta do projeto:

```powershell
cd preview
python -m http.server 8080
```

Abra `http://localhost:8080` no navegador. Depois:

1. escolha uma categoria e um tema;
2. toque em **Ver em Libras** (botão amarelo);
3. se o avatar pedir, toque no texto da resposta para ele sinalizar em Libras.

Não abra o `index.html` direto pelo Explorer: o navegador bloqueia o
`knowledge.json` sem um servidor local.

### Menu por dedos

Com o preview aberto, rode num **segundo terminal**, na raiz do projeto:

```powershell
totem-menu
```

Uma janela mostra a webcam, a contagem de dedos e uma barra de "segurando".
Mantenha a mão parada por cerca de 1 segundo para confirmar a escolha:

| Onde você está | Gesto | Efeito |
| --- | --- | --- |
| Categorias | 1 a 4 dedos | Abre a categoria com aquele número |
| Assuntos | 1 a 5 dedos | Mostra a resposta do assunto com aquele número |
| Assuntos | Punho fechado | Volta para as categorias |

Para repetir o mesmo número (por exemplo, categoria 2 e depois assunto 2),
abaixe a mão antes. Assuntos sem número (como Dinheiro e Hotel) continuam só por
toque. O rodapé do site mostra o estado da câmera: iniciando, procurando a mão,
segurando, desligada ou com erro. Sem o `totem-menu` rodando, o site funciona
normalmente por toque.

Opções úteis: `--camera 1` (outra webcam) e `--hold-seconds 1.5` (tempo para
confirmar). `q` ou `ESC` na janela encerra.

O `totem-menu` conversa com o site gravando `preview/gesture_state.json`
(ignorado pelo git), que o site lê a cada 250 ms.

## Desenvolvimento

A suíte de testes cobre apenas lógica pura e **não exige MediaPipe nem webcam**,
então roda em qualquer máquina da equipe:

```powershell
pip install -r requirements-dev.txt
pytest
```

Os testes do preview (JavaScript) usam o runner nativo do Node 22+, sem
dependências:

```powershell
cd preview
npm test
```

Lint e formatação:

```powershell
ruff check .
ruff format .
```

### Integração contínua

O [workflow de CI](.github/workflows/ci.yml) roda a cada push na `main` e em todo
pull request, em três jobs:

**`qualidade`** — lint, formatação e testes, no Ubuntu e no Windows. Instala
apenas `requirements-dev.txt`, **sem MediaPipe e sem OpenCV**. Isso é
intencional: transforma em verificação contínua a premissa da arquitetura de que
a lógica de domínio depende de `Protocol`, e não de bibliotecas concretas. Se
alguém introduzir um `import mediapipe` no topo de um módulo de domínio, este job
falha.

**`integracao`** — instala as dependências completas e executa
[`scripts/smoke_mediapipe.py`](scripts/smoke_mediapipe.py), verificando que a
biblioteca nativa carrega, que o extractor concreto satisfaz o contrato e que o
vetor produzido tem o formato esperado. Também falha se `opencv-python` for
reintroduzido junto de `opencv-contrib-python`.

**`preview`** — roda os testes JavaScript do menu por dedos com `node --test`.

Antes de abrir um pull request, rode localmente o mesmo que o CI roda:

```powershell
ruff check .
ruff format --check .
pytest
cd preview; npm test
```

### Estrutura

```
src/totem_aju/
  config.py                   constantes compartilhadas por coleta e treino
  vocabulary.py               vocabulário fechado (contrato de dados)
  errors.py                   exceções de domínio
  vision/
    schema.py                 FrameLandmarks (imutável, tipado)
    extractor.py              Protocol LandmarkExtractor
    mediapipe_extractor.py    implementação concreta (único módulo que vê MediaPipe)
    camera.py                 Protocol FrameSource + webcam via OpenCV
    normalization.py          funções puras de normalização geométrica
    sequence.py               janela temporal e reamostragem
    heuristics.py             contagem de dedos e gestos por geometria 3D
    smoothing.py              suavização temporal dos landmarks e dos dedos
  menu/
    selector.py               confirma a contagem mantida parada (lógica pura)
    counter.py                contagem de dedos sobre as heurísticas
    state.py                  estado da câmera → preview/gesture_state.json
    session.py                loop câmera → contagem → escolha → estado
  data/
    manifest.py               índice das amostras em JSON Lines
    recorder.py               orquestra captura → disco
  cli/
    capture.py                interface de coleta
    menu.py                   totem-menu: webcam + janela do menu por dedos
preview/
  index.html                  tela apresentável do totem
  styles.css / app.js         interface e interação
  js/                         catálogo, menu de dois níveis e leitura do estado
  tests/                      testes do preview (node --test)
  knowledge.json              respostas turísticas curadas
scripts/
  smoke_mediapipe.py          verificação do ambiente completo (fora da suíte)
  demo_gestos.py              demonstração das heurísticas de gestos
  camera_base.py              abre a webcam numa janela (teste rápido)
```

O MediaPipe e o OpenCV ficam atrás de `Protocol`, com import preguiçoso nas
implementações concretas. Isso é o que permite testar todo o pipeline com dublês
sintéticos e trabalhar no projeto sem ter a captura configurada. Detalhes em
[`docs/arquitetura.md`](docs/arquitetura.md).

## Situação atual

Concluído: fundação do projeto, pipeline de extração e normalização de landmarks,
coleta de dados com indexação, suite de testes, CI e **preview apresentável**
com base curada + VLibras.

Próximas etapas: coleta do dataset em volume, treino do classificador temporal
e evolução do preview para o quiosque completo (webcam + reconhecimento).

## Licença

MIT. Ver [`LICENSE`](LICENSE).
