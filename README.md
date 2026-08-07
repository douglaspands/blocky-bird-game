# Blocky Bee

Flappy Bird com temática Minecraft, feito em Python/Pygame. Todos os gráficos e sons
são gerados por código — sem assets externos.

A tela inteira é aproveitada em qualquer proporção: a área jogável continua sendo
exatamente a mesma coluna de 480×720 de mundo (a dificuldade não muda entre aparelhos),
e o espaço que sobra vira faixa decorativa com cenário do universo Minecraft — céu
estendido, chão mais fundo, corte transversal do subsolo do bioma atual e mobs que não
interagem com o jogo. Tocar sobre a faixa também faz a abelha voar, então nenhuma parte
da tela é zona morta. A renderização usa aceleração por GPU por padrão (com fallback
automático até o caminho por superfície da v2, caso o aparelho não suporte), com todo
o conteúdo estático pré-renderizado na inicialização — ver [Desempenho](#desempenho).

Motivação do projeto, o que é Spec Driven Development e um prompt de exemplo para
reproduzir o método em outro projeto: ver [Sobre este projeto e o método SDD](#sobre-este-projeto-e-o-metodo-sdd).

## Requisitos

- Python >= 3.10
- [uv](https://docs.astral.sh/uv/) instalado

## Executar

```bash
uv sync
uv run main.py
```

## Controles

| Ação | Teclado/Mouse | Controle Xbox |
|---|---|---|
| Voar / reiniciar | ESPAÇO, ↑ ou clique | Botão A |
| Pausar/despausar | ESC ou P | Start |
| Mudo | M | Botão Y |

O controle é opcional: teclado e mouse funcionam normalmente sem ele, e conectar ou
desconectar durante a partida não interrompe o jogo.

## Desempenho

O jogo renderiza com aceleração por GPU por padrão. Se o renderizador acelerado não
puder ser criado, o sistema tenta um renderizador escolhido pelo próprio SDL antes de
cair para o caminho de desenho por superfície da v2 — o jogo continua funcional em
qualquer um dos três caminhos, sem exigir configuração do jogador.

### Sobreposição de diagnóstico

```bash
BLOCKY_PERF=1 uv run main.py
```

Com `BLOCKY_PERF=1` (desligado por padrão, sem custo quando desligado), a tela exibe
taxa de quadros, tempo de atualização, tempo de desenho e o caminho de renderização
efetivamente em uso.

### Benchmark

```bash
uv run scripts/benchmark.py
```

Roda sem display real (usa `SDL_VIDEODRIVER=dummy` internamente) e mede tempo por
quadro (p50/p95) e volume de alocação por quadro nos estados PRONTO, JOGANDO (nos três
biomas) e GAME_OVER, imprimindo uma tabela markdown comparável entre execuções. Use
`--frames N` para ajustar a amostra de cada cenário.

## Testes

```bash
SDL_VIDEODRIVER=dummy uv run pytest
```

`SDL_VIDEODRIVER=dummy` roda o Pygame sem abrir uma janela real, útil em CI e
ambientes sem display. A suíte mede cobertura de `src/` a cada execução
(`pyproject.toml::tool.pytest.ini_options`) e falha se cair abaixo do mínimo declarado.

## Documentação

```bash
uv run mkdocs serve
```

Publica localmente (com recarregamento automático) a página de apresentação do
projeto, a API extraída das docstrings de `src/` e os documentos de spec de todas as
versões, lado a lado. `uv run mkdocs build --strict` gera o mesmo site em `site/` e é
o que valida o build no CI antes do deploy para o GitHub Pages
([`.github/workflows/docs.yml`](https://github.com/douglaspands/blocky-bird-game/blob/main/.github/workflows/docs.yml)).
As dependências de documentação ficam restritas ao grupo `dev` — não entram no
executável nem no APK empacotados.

## Jogar no navegador (build web)

O mesmo código-fonte compila para um único `.html` autocontido via
[`pygbag`](https://github.com/pygame-web/pygbag) (WebAssembly):

```bash
uv run python scripts/build_web.py
```

Gera `dist/BlockyBee.html`. Para testar localmente num navegador (abrir via
`file://` não reflete como o GitHub Pages serve o jogo, e as ferramentas de
rede/console do navegador exigem uma origem http(s) real), builda e sobe um
servidor local em um só passo:

```bash
uv run python scripts/serve_web.py
```

Abre `http://127.0.0.1:8000/BlockyBee.html` no navegador. `--port` muda a
porta; `--no-build` pula o build e só serve o `dist/BlockyBee.html` que já
existe (útil para reabrir rápido sem rebuildar).

> **Achado em aberto (task 91/99 de [`specs/v4/tasks.md`](specs/v4/tasks.md)):**
> hoje o `.html` gerado por `scripts/build_web.py` fica preso em "Loading,
> please wait ..." e nunca termina de carregar — bug real, já investigado a
> fundo (não é falha de rede nem de configuração local) e registrado como
> tarefa em aberto, não uma regressão desta sessão. O mesmo código, buildado
> só com `uv run python -m pygbag --build main.py` (sem o empacotamento em
> arquivo único de `scripts/build_web.py`, então ainda depende de rede para
> buscar o runtime do CDN do `pygbag`) carrega e joga normalmente — útil como
> alternativa para testar o jogo em si enquanto o bug do build único
> continua aberto.

## Gerar executável

Para distribuir um binário que roda com duplo clique, sem precisar instalar Python:

```bash
uv sync
uv run pyinstaller BlockyBee.spec
```

O executável fica em `dist/BlockyBee.exe` (Windows) ou `dist/BlockyBee` (Linux/macOS).
`BlockyBee.spec` já está configurado (onefile, sem console) — não é necessário passar
flags extras.

### Releases automatizadas (GitHub Actions)

Ao publicar uma Release no GitHub (com uma tag de versão, ex. `v1.0.0`), o workflow
[`.github/workflows/release.yml`](https://github.com/douglaspands/blocky-bird-game/blob/main/.github/workflows/release.yml)
builda o executável para Windows e Linux automaticamente e anexa aos assets da release:

- `BlockyBee-windows-x64-<tag>.zip`
- `BlockyBee-linux-x64-<tag>.tar.bz2`
- `BlockyBee-android-universal-<tag>.apk` (Android — celular/tablet, sempre em retrato, ver abaixo)

Ver [`CHANGELOG.md`](https://github.com/douglaspands/blocky-bird-game/blob/main/CHANGELOG.md) para o que muda em cada versão.

## Instalar no Android (celular)

1. Baixe `BlockyBee-android-universal-<tag>.apk` dos assets da Release desejada.
2. No aparelho, abra o arquivo baixado e permita a instalação de "fontes
   desconhecidas" quando solicitado (o app não vem de uma loja, então o Android
   pede essa confirmação uma vez por origem).
3. Toque no ícone "Blocky Bee" para abrir.

Controles: toque em qualquer ponto da tela para voar/reiniciar; o ícone de mudo
no canto silencia o áudio; o botão BACK do sistema pausa durante o jogo e fecha
o app nas outras telas. O app roda sempre em orientação retrato, mesmo girando
o aparelho.

Requisitos: Android 5.0 (API 21) ou superior.

### Build local do APK (Docker + Buildozer)

Reproduz o mesmo processo do CI, útil para testar mudanças na cadeia Android
sem depender de uma Release:

```bash
yes y | docker run --rm -i -v "$(pwd)":/home/user/hostcwd -v "$HOME/.buildozer":/home/user/.buildozer kivy/buildozer android debug
```

No Windows, usando o PowerShell (sem Git Bash/WSL):

```powershell
docker run --rm -it -v "${PWD}:/home/user/hostcwd" -v "${HOME}/.buildozer:/home/user/.buildozer" kivy/buildozer android debug
```

A imagem `kivy/buildozer` roda como root e o buildozer pede confirmação
interativa (`input()`) para isso, além da aceitação das licenças do Android
SDK no primeiro build — sem stdin conectado, o processo recebe EOF
imediatamente e falha (`EOFError: EOF when reading a line`). O `-it` conecta
o terminal para responder `y` manualmente quando solicitado; no bash, o CI
(ver `.github/workflows/release.yml`) usa `yes y | docker run -i ...` para
automatizar isso, já que o PowerShell não tem `yes` embutido.

O APK gerado fica em `bin/*.apk`. Ver `buildozer.spec` e `specs/v2/design.md`
(seção 24) para detalhes da configuração e das receitas locais necessárias.

## Estrutura

```
main.py            # Entry point
src/
├── config.py       # Constantes (tela, fisica, gameplay) e o viewport ativo
├── game.py         # Loop principal, timestep fixo e maquina de estados
├── viewport.py     # Canvas logico e area jogavel (faixas decorativas em qualquer proporcao)
├── bands.py        # Faixas laterais: corte transversal do subsolo do bioma
├── render.py       # Interface de render + cascata GPU -> SDL -> superficie
├── bird.py         # Fisica e animacao do passaro
├── pipes.py        # Colunas/obstaculos
├── ground.py       # Chao rolante
├── biome.py        # Overworld / Cave / Nether
├── decor.py        # Parallax de fundo
├── mobs.py         # Mobs decorativos das faixas (nao interagem com o jogo)
├── score.py        # Pontuacao e recorde (highscore.json)
├── storage.py      # Diretorio gravavel do recorde/qualidade por plataforma
├── quality.py      # Qualidade adaptativa (mede FPS e ajusta o nivel visual)
├── perf.py         # Instrumentacao: medicao por frame e sobreposicao de diagnostico
├── particles.py    # Particulas de bloco quebrando
├── textures.py     # Texturas voxel proceduais
├── pixelfont.py    # Fonte bitmap propria, gerada por codigo
├── sounds.py       # Audio sintetizado 8-bit
├── input.py        # Teclado, mouse, toque e controle Xbox
├── assets.py       # Resolucao de caminho de asset bundlado (empacotado ou nao)
├── scale.py        # Escala/letterbox da resolucao logica para a janela real
└── ui.py           # HUD e telas (pronto/pausa/game over)
specs/              # Documentos de requisitos, design e plano (versionados em specs/vN/)
scripts/            # generate_app_icon.py, benchmark.py, build_web.py, serve_web.py
docs/               # Esqueleto de inclusoes para o site MkDocs (ve Documentacao acima)
tests/              # Testes unitarios (pytest)
```

## Contribuindo

Convenções de branch, commit, tag e o fluxo de spec-antes-de-código estão em
[`CONTRIBUTING.md`](https://github.com/douglaspands/blocky-bird-game/blob/main/CONTRIBUTING.md).

## Licença

Código sob a licença [MIT](LICENSE). A licença cobre o código deste repositório — não
a marca **Minecraft**: todo gráfico e som do jogo é gerado por código, sem asset nem
material da Mojang (ver [Sobre este projeto e o método SDD](#sobre-este-projeto-e-o-metodo-sdd)).

## Sobre este projeto e o método SDD

### Por que este projeto existe

Duas motivações, sem rodeio. A primeira é estudar **Spec Driven Development (SDD)**
na prática, num projeto real e pequeno o bastante para caber na cabeça inteiro. A
segunda é fazer um jogo para o meu filho, o Pedro, que gosta de jogos e de Minecraft
— o que explica escolhas que de outro modo pareceriam arbitrárias: a temática voxel,
o fato de todo gráfico e som ser gerado por código (sem material da Mojang nem asset
de terceiros) e os créditos ("por Douglas e Pedro") que estão no jogo desde a v1.

### O que é Spec Driven Development

SDD é desenvolver a partir de uma especificação que **governa** o código, em vez de
um código que a especificação descreve depois de pronto. Na prática, neste
repositório, isso significa:

- **Três documentos por versão, escritos antes do código:** [`requirements.md`](specs/v3/requirements.md)
  (o quê e por quê, em critérios de aceitação no formato EARS — `QUANDO <evento>, O
  sistema DEVE <resposta>`), [`design.md`](specs/v3/design.md) (como, com as decisões
  técnicas e os porquês de cada uma) e [`tasks.md`](specs/v3/tasks.md) (a ordem de
  implementação, uma tarefa por vez).
- **A spec como fonte da verdade, não o código.** Uma dúvida sobre "por que o jogo
  faz X" se resolve lendo o requisito e a seção de design correspondente, não
  arqueologia de commit.
- **Uma tarefa por vez, marcada `[x]` só depois de validada** — testada, com
  `ruff`/`ty`/`pytest` verdes — nunca antes.
- **Pastas `specs/vN/` autocontidas e imutáveis.** Cada versão tem seus três
  documentos completos, refletindo o estado inteiro do jogo naquele momento; versões
  concluídas nunca são reescritas (ver [`specs/README.md`](specs/README.md)) — são
  histórico, não rascunho.
- **A matriz de rastreabilidade** ([`specs/v3/traceability.md`](specs/v3/traceability.md))
  fechando o ciclo: uma linha por critério de aceitação, ligando requisito → design →
  tarefa → teste, com um teste automatizado (`tests/test_traceability.py`) garantindo
  que ela nunca fica desatualizada em silêncio.

### Prompt de exemplo

Um prompt pronto para uso, que planejaria e construiria um projeto como este seguindo
o método — combinando a voz de quem define o produto com a de quem define a técnica.
Cada parte vem com uma linha dizendo o porquê; o prompt é genérico o bastante para
outro domínio, não amarrado a jogos.

```text
Você vai atuar em duas vozes para planejar e construir este projeto por Spec Driven
Development (SDD): primeiro como Product Owner, depois como Tech Lead com prática em
Python. Gere os três documentos de spec ANTES de escrever qualquer código.

## Voz 1 — Product Owner

- Objetivo do produto em uma frase.
  (Uma frase força prioridade; se não cabe em uma frase, o escopo ainda não está claro.)
- Público-alvo: quem usa e em que contexto.
  (Molda decisões de UX e de plataforma que, sem isso, ficam arbitrárias.)
- User stories no formato "Como <papel>, quero <ação>, para que <benefício>".
  (O "para que" é o que evita construir a coisa certa pela razão errada.)
- Critérios de aceitação em EARS para cada user story:
  "QUANDO <evento>, O sistema DEVE <resposta>" (ou ENQUANTO/SE para condições
  contínuas ou opcionais).
  (Testável por construção — cada critério vira um teste, sem ambiguidade de "pronto".)
- Uma seção explícita de "fora de escopo": o que este projeto DELIBERADAMENTE não
  faz.
  (É o item que mais falta em quem está começando, e o que evita que o agente invente
  funcionalidade não pedida.)

## Voz 2 — Tech Lead com prática em Python

- Stack e versão mínima, gerenciamento de dependências com `uv` (`uv sync`,
  `uv run`), estrutura de pastas do pacote.
  (Fixa o ambiente de execução antes de qualquer decisão de design depender dele.)
- Ferramental de qualidade como GATE, não como sugestão: `ruff` (lint + formatação),
  `ty` (tipos) e `pytest`, todos rodando em CI.
  (Sem gate automatizado, "qualidade" vira promessa que ninguém confere.)
- Restrições de design explícitas (ex.: sem asset externo; nenhuma dependência que
  não rode no alvo de deploy).
  (Restrição dita cedo é decisão; restrição descoberta tarde é retrabalho.)
- Protocolo de trabalho: gerar `requirements.md`, `design.md` e `tasks.md` antes de
  codar; implementar uma tarefa de `tasks.md` por vez, na ordem; testar cada uma;
  marcar `[x]` só depois de validada.
  (É o que faz a spec continuar governando o código depois da primeira tarefa, e não
  só na primeira hora do projeto.)

Ao final de cada tarefa, pare e aguarde validação antes de seguir para a próxima.
```
