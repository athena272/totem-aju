
 ### Arquitetura 

```
Webcam
   ↓
OpenCV
   ↓
MediaPipe Hands
   ↓
21 pontos da mão
   ↓
Normalização dos pontos
   ↓
Classificador (Random Forest / MLP)
   ↓
Número em Libras: 0, 1, 2, ..., 9
```


 ### Dataset

 capturar as próprias imagens.

 Por exemplo:

```
dataset/
├── 0/
├── 1/
├── 2/
├── 3/
├── 4/
├── 5/
├── 6/
├── 7/
├── 8/
└── 9/
```

cerca de 300-1000 exemplos por simbolo

 - posição da mão;
- distância da câmera;
- iluminação;
- fundo;
- rotação da mão;
- pessoas diferentes, se possível.

 para guardar as imagens. Podemos fazer:

```
Webcam → MediaPipe → landmarks → CSV
```

 e o CSV poderia ficar assim:

```
x1,y1,z1,x2,y2,z2,...,x21,y21,z21,label
0.52,0.31,-0.02,...,0.61,0.72,-0.04,3
0.51,0.30,-0.01,...,0.60,0.73,-0.03,3
...
```

depois usamos `scikit-learn` para treinamento

 ### Um detalhe importante sobre Libras

 Antes de montar o dataset, precisamos definir **exatamente quais configurações de mão correspondem aos números de 0 a 9 em Libras**, porque não é simplesmente o mesmo que reconhecer os algarismos visualmente em qualquer convenção.

 decidir:

 **A)** reconhecer somente a mão parada mostrando um número;

 ou

 **B)** reconhecer os números em tempo real pela webcam, inclusive quando há movimento entre sinais.

sugiro a gente começar so com **A**

começar com **script que abre a webcam, detecta a mão e salva automaticamente os landmarks em um CSV para cada número de Libras**.
