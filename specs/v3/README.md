# Blocky Bee — Specs v3

**Status:** em andamento.

## Descrição

A v3 renomeia o jogo para **Blocky Bee** — o personagem sempre foi uma abelha, e "Bird" era
herança do gênero — ataca quatro problemas que sobraram da v2, todos ligados à experiência
real no Android, e acrescenta boas práticas de Git/GitHub esperadas de um projeto Python
público.

**Aproveitamento de tela.** A v2 desenhava numa janela de 480×720 centralizada na tela do
aparelho, o que deixava barra preta nos quatro lados. A v3 cria o display em tela cheia e
adota um **canvas lógico com a proporção real da tela**, mantendo a **área jogável fixa em
480×720 de mundo**. Nenhuma constante de física ou de bioma muda, então a dificuldade
calibrada na v1 continua exatamente a mesma em qualquer aparelho — o que sobra de tela vira
**faixa decorativa**: céu estendido e terra mais funda num celular alongado, corte
transversal do subsolo nas laterais de um monitor. A área jogável passa a ser lida como um
poço vertical cortado na terra, com mobs do universo Minecraft (creeper, enderman, ghast e
outros seis) povoando as faixas sem interagir com o jogo. As faixas são cenário, mas não são
zona morta: tocar ou clicar sobre elas vale como toque na área jogável, para que num celular
alongado o polegar não precise mirar na coluna estreita do meio da tela.

**Desempenho.** O jogo passa a ser renderizado com **aceleração por GPU por padrão**, via
`pygame._sdl2.video`, com cascata de três níveis para compatibilidade (acelerado → driver
escolhido pelo SDL → o caminho de superfície da v2). Todo conteúdo estático — chão, colunas,
parallax, faixas, sprites rotacionados, texto — é pré-renderizado uma vez na inicialização e
enviado à GPU como textura, derrubando ~96 desenhos por frame para menos de 15. Some-se a
isso disciplina de alocação, ajuste do coletor de lixo e a remoção da escrita em disco de
dentro do frame.

**Independência de taxa de quadros.** A v2 aplicava a física uma vez por frame desenhado, o
que fazia o jogo rodar em **câmera lenta** num aparelho que não sustentasse 60 FPS. A v3 usa
timestep fixo com acumulador: o aparelho lento perde fluidez de imagem, nunca velocidade de
jogo. Quando nem isso basta, a **qualidade adaptativa** mede o FPS real e reduz o cenário em
níveis — sempre só o que é decorativo, nunca uma regra de jogo.

**Rigor de SDD.** Sendo este projeto principalmente um exemplo de Spec Driven Development, a
v3 fecha o ciclo: docstring obrigatória em toda classe e função verificada em CI, site de
documentação publicando a API e os specs de todas as versões no mesmo lugar, **matriz de
rastreabilidade** ligando cada critério de aceitação ao design, à task e ao teste que o
prova — vigiada por um teste que quebra o build se um requisito ficar sem rastreio — e
cobertura mínima no CI. O `README.md` passa a explicar a motivação do projeto e a trazer um
prompt de exemplo, para que o método seja reproduzível por quem está começando.

**Boas práticas de Git e GitHub.** As convenções de branch, commit e tag já em uso
informalmente (`main`/`release/vN`/`feature/<slug>`, commits imperativos citando a task,
tags `vMAJOR.MINOR.PATCH`) passam a estar documentadas em `CONTRIBUTING.md`. O projeto ganha
`LICENSE` (MIT), `CHANGELOG.md`, hooks de pre-commit que espelham o gate de CI (`ruff`, `ty`)
mais checagens básicas de higiene — rodados também no próprio CI, para valer mesmo sem
instalação local —, `.editorconfig`/`.gitattributes` para final de linha consistente entre o
desenvolvimento no Windows e o CI no Linux, Dependabot para as dependências Python e as
GitHub Actions, `permissions` de menor privilégio em todo workflow, e um template de Pull
Request.

## Conteúdo desta pasta

- [`requirements.md`](requirements.md) — requisitos R1–R35 em formato EARS. R1–R13 são o jogo base (v1); R14–R17 são a entrega Android e R18–R21 os aumentos de escopo da v2; **R22–R35 são da v3** (identidade, tela e orientação, preservação da dificuldade, faixas decorativas, GPU, desempenho, timestep, qualidade adaptativa, instrumentação, documentação, rastreabilidade, motivação/método, entrada em toda a área visível e boas práticas de Git/GitHub).
- [`design.md`](design.md) — arquitetura técnica. Parte I (seções 1–18) é o jogo base; Parte II (19–25) é Android; Parte III (26–28) é qualidade; Parte IV (29) é o ícone; **Parte V (30–44) é a v3**.
- [`tasks.md`](tasks.md) — plano incremental. Tasks 1–19 são o histórico da v1; 20–41 são a v2; **tasks 42–79 são a v3**.
- [`traceability.md`](traceability.md) — matriz critério → design → task → teste, verificada por `tests/test_traceability.py`.

## O que muda em relação à v2

| Problema na v2 | Correção na v3 |
|---|---|
| `set_mode` sem `FULLSCREEN`: janela de 480×720 centralizada, barra preta nos quatro lados | Tela cheia na resolução nativa, canvas lógico com a proporção real do aparelho |
| Barra preta inevitável por descompasso de proporção (2:3 contra ~0,45 no celular e ~1,78 no monitor) | O que sobra vira faixa decorativa temática, em vez de barra |
| Tentativas anteriores de preencher a tela mudavam a dificuldade (task 39) ou cortavam a cena (task 40) | Área jogável fixa em 480×720 de mundo; só o canvas ao redor é elástico |
| Toque fora dos 480×720 era descartado (barra de letterbox, zona morta) | A tela inteira é superfície de entrada: qualquer ponto faz voar, só o ícone de mudo é exceção |
| ~96 desenhos por frame, todos em CPU, nenhuma superfície convertida | Render acelerado por GPU com todo conteúdo estático pré-renderizado |
| Física por frame: aparelho lento roda o jogo em câmera lenta | Timestep fixo com acumulador; aparelho lento perde só fluidez |
| ~40 objetos descartados por frame; escrita de JSON dentro do frame | Retângulos e listas persistentes, `gc.freeze()`, persistência no fim da partida ou ao ir para segundo plano |
| Sem instrumentação: otimização só por percepção | Sobreposição de diagnóstico no aparelho e benchmark headless reproduzível |
| Docstrings esparsas, sem site de documentação, sem rastreabilidade formal | Gate de docstring no CI, MkDocs Material + mkdocstrings, matriz de rastreabilidade verificada por teste |

## Riscos e limites conhecidos

- **Maior risco: `pygame._sdl2.video` é marcado como experimental** no pygame-ce. A API usada aqui (`Window.from_display_module`, `Renderer`, `Texture`, `logical_size`, `coordinates_from_window`) está presente e estável na 2.5.7, que é a versão fixada tanto no `pyproject.toml` quanto na receita local do p4a — mas uma atualização futura de pygame-ce pode exigir ajuste. A cascata de compatibilidade (design seção 33.3) limita o dano: o pior caso é o jogo cair para o caminho de superfície da v2, não deixar de abrir.
- **A troca de `package.name` para `blockybee` é uma quebra deliberada:** o Android trata o novo identificador como outro aplicativo, então quem tiver a v2 instalada fica com dois ícones e o recorde antigo não é migrado. O sandbox do Android impede a migração sem armazenamento compartilhado e permissão, o que seria um preço alto por um inteiro. Decisão registrada no design, seção 31.
- **Verificação:** o que depende de aparelho Android real (ausência de barra preta, trava de orientação, FPS sustentado, aparência das faixas e dos mobs) não é verificável no ambiente de desenvolvimento. O checklist de `tasks.md` separa explicitamente o automatizável do que precisa de celular.
- A escolha de onde vai o espaço que sobra (até duas fileiras de bloco no chão, o resto no céu) é uma decisão visual, não analítica. O limite existe para que uma tela muito alongada não vire uma tira fina de jogo sobre um bloco de terra gigante; o valor exato foi escolhido por inspeção.
- Com céu visível acima do teto invisível da abelha, o limite superior do voo fica menos evidente do que na v2, onde coincidia com a borda da tela. Posicionar o HUD nessa faixa ajuda a lê-la como área de interface; se incomodar na validação em aparelho, a saída é uma fileira de blocos marcando o limite.

## Sobre esta versão

Esta pasta é um retrato **completo e autocontido** dos specs da v3 — cobre o jogo inteiro,
não só as mudanças desta versão. A v1 e a v2 permanecem intactas em [`specs/v1/`](../v1/) e
[`specs/v2/`](../v2/) como histórico, inclusive com o nome antigo do jogo, que era o correto
quando foram escritas. Veja [`specs/README.md`](../README.md) para o padrão de versionamento.
