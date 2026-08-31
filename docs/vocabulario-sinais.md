# Vocabulário de sinais

Este documento é o **contrato de dados** entre a coleta e o treino. Toda amostra
gravada precisa ter como rótulo um dos identificadores listados aqui, e o
classificador só reconhece o que está nesta lista.

A lista canônica está implementada em `src/totem_aju/vocabulary.py`. Este
documento explica o recorte e o significado; o código é a fonte da verdade para
validação.

## Por que um vocabulário fechado

Reconhecimento de Libras **contínua e irrestrita** é um problema de pesquisa
aberto: envolve segmentação de sinais num fluxo contínuo, expressões faciais
gramaticais, classificadores manuais e concordância espacial. Não é viável num
semestre, e uma tentativa nessa direção resulta em um sistema que falha na
demonstração ao vivo.

O recorte adotado é o oposto: **um vocabulário pequeno e fechado, do domínio
turístico, que funciona de verdade**. A interface colabora com essa restrição —
o usuário escolhe uma categoria no touchscreen e sinaliza apenas a palavra-chave,
o que reduz o espaço de busca e aumenta muito a taxa de acerto percebida.

Meta de coleta: **no mínimo 20 repetições por sinal por sinalizador**, com
variação deliberada de iluminação, distância e roupa de fundo.

## Os sinais

Identificadores em `snake_case`, sem acento, estáveis (nunca renomear depois de
haver amostras gravadas — o rótulo está no `manifest.jsonl`).

### Controle da interação

| Identificador | Glosa | Uso |
| --- | --- | --- |
| `ola` | OLÁ | Inicia a interação |
| `obrigado` | OBRIGADO | Encerra cordialmente |
| `sim` | SIM | Confirmação |
| `nao` | NÃO | Negação |
| `ajuda` | AJUDA | Pede atendimento humano |
| `repetir` | REPETIR | Pede que a resposta seja reexibida |

### Perguntas

| Identificador | Glosa | Uso |
| --- | --- | --- |
| `onde` | ONDE | Localização de algo |
| `como_chegar` | COMO-CHEGAR | Rota até um destino |
| `quanto_custa` | QUANTO-CUSTAR | Preço |
| `que_horas` | QUE-HORAS | Horário de funcionamento |

### Serviços e necessidades

| Identificador | Glosa | Uso |
| --- | --- | --- |
| `banheiro` | BANHEIRO | |
| `comer` | COMER | Restaurantes |
| `agua` | ÁGUA | |
| `hospital` | HOSPITAL | Emergência médica |
| `policia` | POLÍCIA | Emergência de segurança |
| `dinheiro` | DINHEIRO | Banco, caixa eletrônico |
| `hotel` | HOTEL | Hospedagem |

### Transporte

| Identificador | Glosa | Uso |
| --- | --- | --- |
| `onibus` | ÔNIBUS | |
| `taxi` | TÁXI | Táxi e aplicativos |
| `aeroporto` | AEROPORTO | |

### Pontos turísticos de Aracaju

| Identificador | Glosa | Referência |
| --- | --- | --- |
| `praia` | PRAIA | Genérico |
| `orla` | ORLA | Orla de Atalaia |
| `mercado` | MERCADO | Mercados Municipais de Aracaju |
| `museu` | MUSEU | |
| `igreja` | IGREJA | |
| `centro` | CENTRO | Centro histórico |

**Total: 26 sinais.**

## Regras de coleta

1. **Enquadramento.** Cabeça e tronco visíveis, mãos com folga nas bordas do
   quadro. Libras usa o espaço de sinalização à frente do corpo; cortar as mãos
   invalida a amostra.
2. **Uma repetição por amostra.** Cada arquivo `.npy` contém uma única execução
   do sinal, do repouso ao repouso.
3. **Identificar o sinalizador.** Sempre informar o `--signer` na coleta. Sem
   isso, a divisão treino/teste por pessoa se torna impossível (ver
   [`terminologia-e-etica.md`](terminologia-e-etica.md), seção 3.2).
4. **Variar as condições.** Gravar em diferentes horários e locais. O totem vai
   operar em ambiente com iluminação e fundo variáveis; um dataset gravado numa
   única condição produz um modelo que só funciona nela.
5. **Validar os sinais com fonte confiável.** Usar o dicionário do INES e, se
   possível, revisão de um intérprete de Libras. Sinais inventados pela equipe
   comprometem o valor do trabalho.

## Datasets públicos de referência

Úteis para comparação de resultados e eventual pré-treino:

- **MINDS-Libras** (UFMG) — 20 sinais, múltiplos sinalizadores.
- **V-Librasil** (LAViD/UFPB) — grande volume de sinais isolados.
- **Dicionário INES** — referência normativa para a execução correta dos sinais.

## Como evoluir esta lista

Acrescentar sinais é seguro; **remover ou renomear não é**, porque quebra a
correspondência com amostras já gravadas. Ao adicionar:

1. incluir a linha na tabela deste documento;
2. adicionar o identificador em `src/totem_aju/vocabulary.py`;
3. coletar o mínimo de repetições antes de retreinar.
