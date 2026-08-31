# ADR 0001 — Descartar o Virtual Human Toolkit e o Unity

- **Status:** Aceito
- **Data:** 2026-08-31
- **Decisores:** equipe do projeto Totem Aju
- **Escopo:** escolha da plataforma tecnológica base do totem

---

## Contexto

O Totem Aju é um totem interativo de acessibilidade comunicacional para turistas
surdos em Aracaju. A comunicação é **bidirecional**, e os dois sentidos têm
naturezas técnicas completamente distintas:

| Sentido | O que precisa acontecer | Dificuldade |
| --- | --- | --- |
| Turista surdo → totem | Reconhecer sinais em Libras a partir de vídeo | Alta (é a contribuição científica do trabalho) |
| Totem → turista surdo | Exibir a resposta em Libras | Baixa, **se** reusarmos solução existente |

Foi sugerida à equipe a adoção do
[Virtual Human Toolkit (USC-ICT)](https://github.com/USC-ICT/vhtoolkit) como
plataforma base. Este documento registra a avaliação dessa sugestão e a decisão
tomada, para que todos os integrantes compartilhem o mesmo entendimento.

## Opções avaliadas

### Opção A — Virtual Human Toolkit (USC-ICT)

O Virtual Human Toolkit é um framework de pesquisa do Institute for Creative
Technologies da University of Southern California para construir **humanos
virtuais conversacionais**: personagens 3D que falam, com síntese de voz,
sincronia labial, gestos, direcionamento de olhar e gerenciamento de diálogo.

Levantamento feito sobre o projeto:

1. **É fundamentalmente Unity + Windows.** O runtime do personagem é uma
   aplicação Unity, e a cadeia de módulos auxiliares é validada apenas em
   Windows. Adotá-lo significa adotar Unity e C# como plataforma do projeto.
2. **Não resolve o problema central.** O toolkit reconhece **fala** (áudio) e
   produz **fala**. Não há nenhum componente de reconhecimento de língua de
   sinais. O lado difícil do nosso problema — interpretar as mãos do usuário —
   continuaria 100% por fazer, e teria de ser escrito de qualquer maneira.
3. **Orientado ao inglês.** O reconhecimento de voz, o gerenciador de diálogo e
   a síntese de fala são construídos em torno do inglês. Não há suporte a Libras
   nem a português brasileiro.
4. **Licença acadêmica restritiva.** A distribuição é sob licença de pesquisa da
   USC, com restrições de redistribuição — inadequada para um artefato que
   pretendemos publicar como software livre junto ao artigo.
5. **Dependências antigas.** O projeto tem baixa atividade de manutenção e fixa
   versões antigas de Unity e de bibliotecas nativas, o que na prática significa
   gastar tempo de equipe fazendo o ambiente compilar em vez de desenvolvendo.

### Opção B — Python (MediaPipe + PyTorch) + web, com VLibras na resposta

Reconhecimento em Python, usando MediaPipe Holistic para extrair os *landmarks*
de mãos, corpo e face em tempo real, alimentando um classificador temporal em
PyTorch. Interface em web, exibida em modo quiosque. Para o sentido
totem → usuário, reusar o [VLibras](https://www.gov.br/governodigital/pt-br/vlibras)
(LAViD/UFPB, iniciativa do governo federal), que traduz português escrito para
Libras e renderiza num avatar 3D pronto.

## Decisão

**Adotamos a Opção B e descartamos o Virtual Human Toolkit e o Unity.**

O raciocínio decisivo é de custo de oportunidade. O Virtual Human Toolkit
resolveria apenas o *avatar que responde* — que é a parte fácil e para a qual
já existe uma solução brasileira, gratuita, feita especificamente para Libras e
muito mais defensável academicamente no nosso contexto. Em troca, ele nos
imporia uma plataforma inteira (Unity, C#, licença restritiva, dependências
legadas) que **não contribui em nada** para o reconhecimento de Libras, que é
onde está o mérito técnico do trabalho e o gargalo do cronograma.

Um segundo fator, prático: a equipe vai escrever visão computacional e
aprendizado de máquina, e esse ecossistema vive em Python. Manter tudo em
Python + web elimina a fronteira de integração entre dois runtimes e permite
que os integrantes trabalhem em paralelo sem que ninguém precise aprender Unity.

## Consequências

**Positivas**

- Todo o esforço da equipe se concentra no problema real: reconhecer Libras.
- O VLibras entrega o avatar sinalizando desde o primeiro dia, sem custo de
  desenvolvimento, e com legitimidade institucional que fortalece o artigo.
- Pilha única (Python + web), sem integração entre runtimes heterogêneos.
- Sem restrição de licença sobre o que publicaremos.
- MediaPipe roda em CPU em tempo real, então o totem não exige GPU dedicada,
  o que reduz o custo de um eventual protótipo físico.

**Negativas e riscos aceitos**

- Não teremos um avatar com expressividade facial customizável; ficamos limitados
  ao avatar do VLibras. Aceitável: expressividade do avatar não é objetivo do
  trabalho.
- Passamos a depender de um serviço externo (VLibras) para a tradução. Mitigação:
  a interface sempre exibe **também o texto em português**, de modo que a
  indisponibilidade do VLibras degrada a experiência sem interromper o serviço.
- MediaPipe restringe a versão do Python a 3.9–3.12 (não há wheels para 3.13 e
  3.14). Mitigação: o projeto fixa Python 3.12 e o código de domínio não importa
  MediaPipe diretamente — ver `docs/arquitetura.md`.

## Escopo que esta decisão não cobre

A decisão define a plataforma, não o recorte do problema. O recorte — vocabulário
fechado de sinais do domínio turístico, em vez de Libras contínua irrestrita —
está registrado em [`../vocabulario-sinais.md`](../vocabulario-sinais.md), e é
igualmente crítico para a viabilidade do projeto no semestre.

## Referências

- Virtual Human Toolkit: <https://github.com/USC-ICT/vhtoolkit>
- VLibras: <https://www.gov.br/governodigital/pt-br/vlibras>
- MediaPipe Holistic: <https://ai.google.dev/edge/mediapipe/solutions/guide>
- Versões de Python suportadas pelo MediaPipe:
  <https://github.com/google-ai-edge/mediapipe/issues/6081>
