# Terminologia e ética

Documento de referência para o artigo, a apresentação e a comunicação da equipe.

## 1. Terminologia correta

Este é um ajuste pequeno de vocabulário com impacto grande na recepção do
trabalho. Bancas, revisores e — principalmente — a própria comunidade surda
percebem imediatamente o uso de termos incorretos.

| Não usar | Usar | Por quê |
| --- | --- | --- |
| surdo-mudo, mudinho | **pessoa surda**, **surdo** | Pessoas surdas não são mudas: possuem aparelho fonador funcional e se comunicam por Libras, que é uma língua completa |
| deficiente auditivo (como sinônimo de surdo) | **pessoa surda** ou **pessoa com deficiência auditiva** | São grupos distintos: quem se identifica culturalmente como surdo usa Libras; quem tem perda auditiva parcial pode se comunicar oralmente |
| portador de deficiência | **pessoa com deficiência** | Deficiência não é algo que se porta ou se carrega |
| linguagem de sinais | **língua de sinais**, **Libras** | Libras é uma língua com gramática, sintaxe e morfologia próprias, não uma "linguagem" |
| normal (em oposição a surdo) | **pessoa ouvinte** | O antônimo de surdo é ouvinte |

Observação sobre o nosso próprio projeto: a descrição inicial da ideia usava
"pessoas surdas e mudas". Foi corrigida para "pessoas surdas", e o termo antigo
não deve aparecer em nenhum artefato do trabalho.

## 2. Fundamentação legal (justificativa do projeto)

- **Lei nº 10.436/2002** — reconhece a Libras como meio legal de comunicação e
  expressão no Brasil.
- **Decreto nº 5.626/2005** — regulamenta a lei anterior e trata do acesso das
  pessoas surdas à comunicação e à informação.
- **Lei nº 13.146/2015 (Lei Brasileira de Inclusão)** — estabelece a
  acessibilidade comunicacional como direito, incluindo o acesso à informação em
  espaços públicos e turísticos.

Em conjunto, esses instrumentos transformam a acessibilidade comunicacional em
espaços turísticos de "boa prática desejável" em **obrigação legal**, o que
sustenta a relevância do totem para o turismo sergipano.

## 3. Riscos éticos e mitigações

Seção alinhada às diretrizes da CAPES/MEC sobre uso ético e responsável de IA na
produção acadêmica. Cada risco abaixo deve ser reportado no artigo com a
mitigação correspondente.

### 3.1 Viés do dataset e variação regional da Libras

**Risco.** A Libras tem variação regional e geracional: um sinal usado em Aracaju
pode diferir do usado em São Paulo. Como o dataset será gravado pelos próprios
integrantes da equipe e por poucos colaboradores, o modelo aprenderá as variantes
e o estilo de execução dessas poucas pessoas.

**Mitigação.** Registrar o identificador do sinalizador em toda amostra
(implementado em `data/manifest.py`), fazer a divisão treino/teste **por pessoa**
para não inflar a acurácia, buscar o maior número possível de sinalizadores
distintos, e declarar explicitamente no artigo a composição do dataset (número de
sinalizadores, origem, fluência em Libras) como limitação do trabalho.

### 3.2 Vazamento de dados na avaliação

**Risco.** Dividir treino e teste aleatoriamente por amostra faria quadros da
mesma pessoa e da mesma gravação caírem nos dois conjuntos. O modelo passaria a
reconhecer a pessoa, e a acurácia relatada seria artificialmente alta.

**Mitigação.** Divisão obrigatoriamente agrupada por sinalizador, e relato da
acurácia em sinalizadores **nunca vistos** no treino como métrica principal.

### 3.3 Exclusão de quem não é fluente em Libras

**Risco.** Nem toda pessoa surda é fluente em Libras — há quem se comunique por
leitura labial, por escrita ou por oralização. Um totem exclusivamente baseado em
Libras excluiria essas pessoas.

**Mitigação.** A interface nunca depende só do reconhecimento de sinais: o
touchscreen oferece navegação por ícones e categorias, e toda resposta é exibida
**em texto e em Libras simultaneamente**.

### 3.4 Alucinação de LLM em informações factuais

**Risco.** Se um modelo de linguagem gerar livremente as respostas, ele pode
inventar horários de funcionamento, preços de ingresso, linhas de ônibus ou
endereços. No contexto de um turista seguindo a orientação do totem, uma
informação inventada gera prejuízo real.

**Mitigação.** As respostas são restritas a uma **base de conhecimento curada**
pela equipe; o modelo de linguagem, quando usado, atua apenas para selecionar e
reformular conteúdo dessa base, nunca para gerar fatos. Informações voláteis
(preços, horários) exibem a data da última verificação. Quando não há resposta na
base, o totem declara que não sabe em vez de arriscar.

### 3.5 Privacidade e imagem

**Risco.** O totem captura vídeo de pessoas em espaço público, e o dataset contém
imagens e gestos identificáveis dos colaboradores.

**Mitigação.** O totem processa os quadros em memória e **persiste apenas
landmarks** (coordenadas numéricas), nunca vídeo, durante a operação. O
`.gitignore` impede que gravações brutas e dados de coleta sejam versionados. A
coleta para o dataset é feita com consentimento informado e finalidade declarada.

### 3.6 Falsa sensação de acessibilidade

**Risco.** Um totem que funciona mal pode ser usado institucionalmente como prova
de que a acessibilidade "já foi resolvida", desestimulando a contratação de
intérpretes humanos.

**Mitigação.** Declarar no artigo e na própria interface que o totem é um recurso
complementar de vocabulário limitado, não substituto de intérprete de Libras.

## 4. Uso de LLMs na produção do trabalho

Conforme as diretrizes da CAPES/MEC, o uso de modelos de linguagem como
ferramenta de apoio é permitido, desde que com transparência e autoria própria.
A equipe deve:

- registrar em que etapas houve apoio de LLM (revisão de texto, apoio à
  codificação, sugestão de estrutura);
- garantir autoria própria na **modelagem, validação e análise crítica** dos
  resultados;
- verificar manualmente toda referência bibliográfica e todo dado factual
  produzido com apoio de LLM, dado o risco conhecido de alucinação.

## 5. Validação com usuários

O maior diferencial possível para este trabalho é a validação com pessoas surdas
reais. Metas: pelo menos 2 a 3 participantes surdos ou intérpretes de Libras,
com registro de acertos, erros e dificuldades observadas. Caminhos de contato:
o setor de acessibilidade e os intérpretes de Libras da UFS, e associações de
surdos em Aracaju.
