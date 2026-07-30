# Design Técnico — Blocky Bird

Rastreabilidade: cada seção referencia os requisitos (R1–R17) de `requirements.md`.

As seções 1–18 (**Parte I**) descrevem o jogo base, herdado da v1 com os ajustes que o Android exigiu, sinalizados como "(v2)" no texto. As seções 19–25 (**Parte II**) são inteiramente novas na v2.

---

# Parte I — Jogo base

## 1. Visão geral

Jogo 2D em Python 3.10+ / `pygame-ce` 2.5+, loop de jogo com timestep fixo a 60 FPS (R9). Arquitetura orientada a objetos com máquina de estados simples e separação entre lógica, renderização e áudio.

**v2 — alvo duplo desktop + Android.** O mesmo código-fonte roda em Windows/Linux (executável PyInstaller, R13) e em Android celular/TV (APK Buildozer, R17). A estratégia para isso é manter *todo* o jogo escrito contra uma resolução lógica fixa de 480×720 e uma camada de ações abstratas de input, empurrando as diferenças de plataforma para três pontos isolados:

| Diferença | Onde é resolvida |
|---|---|
| Tela de tamanho/proporção arbitrária | `pygame.SCALED` no `set_mode`, escala + letterbox automáticos (seção 20) |
| Toque, BACK do Android, D-pad de TV | `input.py`, traduzidos para as mesmas ações abstratas já existentes (seção 21) |
| Onde se pode gravar arquivo | `storage.py`, resolve o diretório por plataforma (seção 23) |

Nenhum módulo de gameplay (`bird`, `pipes`, `biome`, `score`, `particles`, `decor`, `ground`) precisa saber em que plataforma está rodando.

## 2. Estrutura do projeto

```
flappy_bird/
├── pyproject.toml       # Projeto gerenciado por uv (R9.3)
├── uv.lock              # Lockfile gerado por uv
├── main.py              # Entry point: cria Game e roda o loop (R9.3)
├── BlockyBird.spec      # Config do PyInstaller p/ executavel standalone (R13.1)
├── buildozer.spec       # Config do Buildozer p/ APK Android (R17.1)          [novo na v2]
├── p4a-recipes/
│   └── pygame-ce/       # Receita local de build do pygame-ce p/ p4a (sec. 24) [novo na v2]
├── .github/workflows/
│   └── release.yml      # CI: builda e publica executaveis + APK na Release (R13.2, R17.2)
├── specs/               # Specs versionadas (esta pasta é specs/v2/, ver specs/README.md)
└── src/
    ├── __init__.py
    ├── config.py        # Constantes: tela, física, biomas, cores, créditos
    ├── game.py          # Classe Game: loop, máquina de estados (R6)
    ├── bird.py          # Classe Bird: física e animação (R1)
    ├── pipes.py         # PipePair + PipeManager (R2)
    ├── ground.py        # Chão rolante de blocos (R7.3)
    ├── biome.py         # Definições e transição de biomas (R5)
    ├── decor.py         # Parallax de fundo por bioma (R7.4)
    ├── score.py         # Pontuação e persistência do recorde (R4)
    ├── storage.py       # Resolve diretório gravável por plataforma (R4.5)     [novo na v2]
    ├── particles.py     # Sistema de partículas de blocos (R3.2)
    ├── textures.py      # Geração procedural de texturas voxel (R7)
    ├── pixelfont.py     # Fonte bitmap gerada por código (R7.6)               [novo na v2]
    ├── input.py         # InputManager: teclado, mouse, gamepad, toque, TV (R10, R15)
    ├── sounds.py        # Síntese de sons 8-bit (R8)
    └── ui.py            # HUD, telas PRONTO/PAUSADO/GAME_OVER, fonte pixelada (R6, R7.5, R11, R12)
```

### 2.1 Gerenciamento com uv (R9.3)

Projeto inicializado com `uv init`; `pygame-ce>=2.5` declarado como dependência de runtime (R9.2), `pytest` e `pyinstaller` como dependências de **dev** no `pyproject.toml` (R13.1). Comandos padrão:

```bash
uv sync                              # cria/atualiza o ambiente
uv run main.py                       # executa o jogo
uv run pytest                        # roda os testes
uv run pyinstaller BlockyBird.spec   # gera o executavel standalone (R13.1)
```

O APK **não** é gerado por `uv` — o Buildozer roda em container Docker Linux (seção 24), tanto no CI quanto localmente.

> **Migração `pygame` → `pygame-ce` (v2).** `pygame-ce` é um fork mantido pela comunidade, compatível a nível de API e importado igualmente como `import pygame`. A troca é feita apenas no `pyproject.toml` (`pygame>=2.5` → `pygame-ce>=2.5`); nenhum `import` muda. O motivo é que a cadeia de build Android escolhida (python-for-android) tem receita para `pygame-ce`, não para o `pygame` upstream. Os dois pacotes instalam o mesmo módulo `pygame` e **não podem coexistir** no mesmo ambiente — o `uv sync` após a troca precisa recriar o ambiente (`uv sync --reinstall` se necessário).

Nenhum `pip install` ou venv manual — todo o fluxo passa pelo `uv` instalado localmente.

## 3. Máquina de estados (R6)

```
PRONTO ──flap──▶ JOGANDO ──colisão──▶ GAME_OVER ──flap──▶ PRONTO
                  ▲  │
              ESC/P  ESC/P
                  │  ▼
                PAUSADO
```

`Game.state: GameState (Enum)`. Cada estado tem `handle_events`, `update`, `draw`. Em PAUSADO e GAME_OVER, `update` de física/obstáculos não roda (R3.3, R6.3).

## 4. Configuração (`config.py`)

```python
SCREEN_W, SCREEN_H = 480, 720   # resolução LÓGICA; a tela real pode ser qualquer uma (R9.1, R14.3)
FPS = 60
TITLE = "Blocky Bird"
CREDITS = "por Douglas e Pedro"   # R11
GRAVITY = 0.45          # px/frame²
FLAP_IMPULSE = -8.5     # px/frame
MAX_FALL_SPEED = 12
GROUND_H = 96
PIPE_SPACING = 260      # distância horizontal entre pares
BLOCK = 48              # tamanho do bloco renderizado (16×16 escalado 3×)
PIPE_W = BLOCK          # largura da coluna = largura do bloco desenhado (evita hitbox maior que o sprite)
HITBOX_SCALE = 0.85     # R3.5
```

Valores de física são referência inicial; calibrar em playtest (task 12).

## 5. Bird (`bird.py`) — R1

- Atributos: `pos: Vector2`, `vel_y: float`, `angle: float`, `frame: int`.
- `flap()`: `vel_y = FLAP_IMPULSE`; toca som flap; seta `angle = +30`.
- `update()`: `vel_y = min(vel_y + GRAVITY, MAX_FALL_SPEED)`; `pos.y += vel_y`; clamp no topo (`pos.y >= 0`, R1.4); interpola `angle` até −60 durante queda (R1.3).
- `rect` (hitbox): sprite rect escalado por `HITBOX_SCALE` centralizado (R3.5).
- Animação: alterna 2 frames de asa a cada 6 frames de jogo; no estado PRONTO faz bobbing senoidal (R6.1).
- Sprite: abelha voxel 16×12 desenhada pixel a pixel em `textures.make_bee()` — corpo amarelo com listras pretas, asas cinza translúcido (R7.2).

## 6. Pipes (`pipes.py`) — R2

```python
class PipePair:
    x: float
    gap_y: float          # centro da abertura
    gap_size: int         # do bioma, congelado na criação (R2.2, R2.5)
    block_main: str       # chave em textures, congelada na criação (R2.5)
    block_edge: str       # chave em textures, congelada na criação (R2.5)
    scored: bool          # p/ pontuação única (R4.1)
```

- `PipeManager.update(speed, gap_size, block_main, block_edge)`: recebe os parâmetros do bioma *atual* a cada frame — move todos `x -= speed` (R2.3); spawna novo par (congelando `gap_size`/`block_main`/`block_edge` correntes) quando o último está a `PIPE_SPACING` da borda (R2.1); remove pares com `x + PIPE_W < 0` (R2.4).
- `gap_y` aleatório uniforme entre margens seguras (topo + `GAP_MARGIN`, chão − `GAP_MARGIN`) (R2.2).
- Renderização: coluna = pilha de blocos `BLOCK×BLOCK` (largura `PIPE_W = BLOCK`, R3.1/R3.5) com a textura congelada na criação; bloco da boca da abertura usa variante de borda (ex.: grama no Overworld) (R2.5).
- Colisão: dois `Rect` por par (superior e inferior), largura `PIPE_W` idêntica à largura desenhada; `bird.rect.colliderect()` (R3.1).

## 7. Biomas (`biome.py`) — R5

```python
@dataclass(frozen=True)
class Biome:
    id: str; name: str
    threshold: int        # pontuação de ativação (R5.1)
    speed: float          # R5.3
    gap_size: int         # R5.3
    sky_top: Color; sky_bottom: Color
    block_main: str; block_edge: str   # chaves em textures
    decor: str            # "overworld" | "cave" | "nether" (R7.4)

BIOMES = [
    Biome("overworld", "Overworld", 0,  2.5, 160, ...),
    Biome("cave",      "Cave",      10, 3.0, 145, ...),
    Biome("nether",    "Nether",    25, 3.3, 140, ...),
]
```

Calibrado na task 12 (R5.3, R9.1): a velocidade/abertura do Nether foram ajustadas de
(3.5, 130px) para (3.3, 140px) apos playtest automatizado mostrar um salto de
dificuldade desproporcional na transicao Cave→Nether (bot competente sobrevivia
~12.7 pontos extras apos entrar no Cave, mas so ~2.4 apos entrar no Nether). Com os
novos valores o Nether permanece o bioma mais dificil, porem navegavel (~11 pontos
extras em media), preservando a curva de dificuldade progressiva.

- `BiomeManager.update(score)`: detecta cruzamento de threshold → inicia fade de 60 frames entre gradientes de céu (R5.4), mostra banner com nome do bioma por 90 frames, toca som de portal (R8.1).
- Colunas já existentes mantêm textura antiga; novas usam o bioma novo (transição natural).
- Decoração parallax (R7.4): duas camadas com fatores 0.3 e 0.6 da velocidade de rolagem; elementos desenhados proceduralmente como pilhas de retângulos (formas quadriculadas/voxel, nunca elipses ou curvas) — nuvens/colinas no Overworld, estalactites/minérios no Cave, lava/pilares no Nether. Detalhes em `decor.py` (seção 16).

## 8. Pontuação (`score.py`) — R4

- `+1` quando `pipe.x + PIPE_W < bird.pos.x` e `not pipe.scored` (R4.1); toca som XP.
- Persistência: `highscore.json` no diretório resolvido por `storage.py` (seção 23, R4.5) — conteúdo `{"highscore": int}`. Leitura com `try/except (OSError, ValueError, KeyError, TypeError)` → fallback 0 (R4.4).
- **Gravação incremental (v2, R4.3/R16.4)**: em vez de salvar só no GAME_OVER, o `Game` grava no instante em que o score da partida em curso ultrapassa o recorde. Como isso acontece no máximo uma vez por partida (a partir daí `highscore` acompanha o score), não há custo de I/O por frame:

```python
# em Game._update_score(), ao incrementar:
if self.score > self.highscore:
    self.highscore = self.score
    score.save_highscore(self.highscore)   # 1 gravação por ponto acima do recorde
```

  Isso garante que um app encerrado pelo Android no meio da partida não perca o recorde já alcançado.

## 9. Partículas (`particles.py`) — R3.2

- `Particle`: pos, vel (explosão radial + gravidade), lifetime 20–40 frames, quad 4–8 px com cor amostrada da textura do bloco atingido.
- `ParticleSystem.burst(pos, texture, n=16)` chamado na colisão. Atualiza/desenha mesmo em GAME_OVER (efeito termina naturalmente enquanto obstáculos ficam congelados).

## 10. Texturas procedurais (`textures.py`) — R7

- Todas geradas uma vez no init, em `Surface` 16×16 com ruído determinístico (`random.Random(seed)`), depois `pygame.transform.scale` para `BLOCK` com vizinho-mais-próximo (pixel perfeito) (R7.1).
- Paletas por bloco: `dirt`, `grass_side`, `stone`, `cobblestone`, `netherrack`, `obsidian`, mais `bee` e elementos de decoração.
- Técnica: cor base + variação aleatória de brilho por pixel (±12%), padrões específicos (grama: faixa verde no topo; obsidiana: manchas roxas).

## 11. Áudio (`sounds.py`) — R8

- Síntese **apenas com stdlib** (`array` + `math` + `random`), sem `numpy`: R9.2 restringe as dependências do projeto a `pygame` + stdlib, então a síntese gera o buffer PCM (16-bit signed, mono, 44100 Hz) manualmente e entrega via `pygame.mixer.Sound(buffer=...)`.
  - `flap`: onda quadrada com sweep 300→500 Hz e decaimento linear, 80 ms.
  - `score`: dois pings de onda quadrada 800/1200 Hz em sequência, 120 ms (estilo XP orb).
  - `hit`: ruído branco com decaimento, 200 ms.
  - `portal`: onda quadrada com sweep descendente 900→200 Hz, 400 ms.
- `pygame.mixer.init(frequency=44100, size=-16, channels=1)` em `try/except` → flag `audio_ok`; toda chamada de `play()` checa `audio_ok` e `muted` (R8.3, R8.4).
- **Android (v2)**: o buffer default do mixer é pequeno demais para o pipeline de áudio do Android e produz estouros/crepitação. Em Android usa-se `buffer=1024` (ou 2048 se necessário) no `mixer.init`; no desktop mantém-se o default. A detecção de plataforma vem de `storage.is_android()` (seção 23), reaproveitando a mesma checagem. Se o `mixer.init` falhar em qualquer plataforma, o comportamento de degradação graciosa da v1 continua valendo (R8.4, R14.6).
- A síntese dos 4 sons acontece uma vez na inicialização. Em aparelho de entrada, gerar ~0,8 s de áudio em Python puro custa na ordem de centenas de milissegundos — aceitável no boot, mas é o motivo de a síntese **não** poder acontecer durante o jogo.

## 12. UI (`ui.py`) — R6, R7.5, R11, R12

- Fonte (**mudou na v2**): a v1 usava `pygame.font.SysFont("couriernew", ...)`, que **não existe no Android** — o SDL cairia numa fonte substituta arbitrária ou falharia, quebrando toda a UI. A v2 passa a usar a fonte bitmap própria de `pixelfont.py` (seção 19), gerada por código, garantindo resultado idêntico em todas as plataformas (R7.6) e alinhado ao princípio de "tudo gerado por código" (R7.1).
- Sombra dura (offset 3 px, marrom-escuro) e escala inteira permanecem como na v1 (R7.5).
- HUD: pontuação centralizada no topo (R4.2). Telas: PRONTO, PAUSADO (overlay escurecido, R6.3), GAME_OVER (painel com pontuação/recorde, R3.3).
- **Controle de mudo na tela (v2, R15.4)**: ícone de alto-falante desenhado por código no canto superior direito da área lógica, com área de toque generosa (mínimo 44×44 px lógicos) para ser confortável no celular. Estado (com som / mudo) refletido no ícone. Em PAUSADO, o overlay mostra também a dica de mudo por D-pad para aparelhos sem toque (seção 21).
- Tela PRONTO (R6.1, R11, R12), de cima para baixo:
  1. Título "BLOCKY BIRD" (dourado).
  2. Créditos (`config.CREDITS`, "POR DOUGLAS E PEDRO") logo abaixo do título (R11.1).
  3. Instrução de comando ("ESPAÇO / CLIQUE PARA VOAR").
  4. Recorde atual ("RECORDE: N", texto dourado simples, sem caixa/contorno) no rodapé da tela, logo acima do chão (R12.1, R12.2).
- Título da janela (`pygame.display.set_caption`) inclui os créditos: `"Blocky Bird - por Douglas e Pedro"` (R11.2).

## 13. Loop principal (`game.py`, `main.py`)

```python
while running:
    dt = clock.tick(FPS)          # timestep fixo (R9.1, R9.4)
    handle_events()               # input por estado
    state_update()                # física, pipes, biomas, score, partículas
    state_draw()                  # fundo → decoração → pipes → chão → bird → partículas → HUD
    pygame.display.flip()
```

Input unificado (R1.1, R10, R15): eventos de teclado, mouse, joystick e **toque** mapeiam para as mesmas ações abstratas em `input.py`:

| Ação | Teclado/Mouse | Controle Xbox | Android (toque/TV) |
|---|---|---|---|
| `flap` (voar/reiniciar) | ESPAÇO, ↑, clique | Botão A (`JOYBUTTONDOWN`, button 0) | Toque na área de jogo; D-pad center / ENTER na TV |
| `pause` | ESC, P | Start (button 7) | BACK durante JOGANDO (R15.2) |
| `mute` | M | Y (button 3) | Toque no ícone de mudo; D-pad ←/→ em PAUSADO |
| `quit` | — | — | BACK fora de JOGANDO (R15.3) |

- `src/input.py`: classe `InputManager` que consome `pygame.event` e retorna set de ações; os estados só conhecem ações, não dispositivos (R10.4, R15.5).
- Init: `pygame.joystick.init()` + inicialização de todos os joysticks presentes (R10.1).
- Hotplug: tratar `JOYDEVICEADDED`/`JOYDEVICEREMOVED` reinicializando o joystick correspondente (R10.2); ausência de controle não afeta o jogo (R10.5).
- Índices de botão seguem o mapeamento padrão do controle Xbox no SDL2/Windows; validar no playtest (task 12).
- Detalhes do input Android (toque, BACK, D-pad de TV) na seção 21.

## 14. Tratamento de erros

| Falha | Comportamento |
|---|---|
| Mixer indisponível | jogo sem som (R8.4, R14.6) |
| highscore.json corrompido, ausente ou com chave/tipo inválido | recorde 0, sobrescreve ao salvar (R4.4) |
| Nenhum controle Xbox conectado | jogo funciona normalmente com teclado/mouse (R10.5) |
| Diretório de save sem permissão de escrita (Android) | `save_highscore` engole `OSError` e o jogo segue jogável, sem persistir (R4.5) |
| Módulo `android` indisponível (rodando no desktop) | `storage.py` cai no caminho desktop via `ImportError` (seção 23) |
| App enviado para segundo plano | pausa automática, sem perder progresso nem recorde (R16.1, R16.4) |

## 15. Estratégia de testes

- Unitários (`pytest`, 35 testes em `tests/` na v1, sem abrir janela — `conftest.py` força `SDL_VIDEODRIVER=dummy` e isola cada teste em um `tmp_path` para nunca ler/gravar o `highscore.json` real): física do Bird (gravidade, clamp, impulso, ângulo, hitbox, idle bob), spawn/remoção/movimento/congelamento de textura de pipes, thresholds e timers de bioma, persistência do recorde (arquivo ausente/corrompido/tipo inválido), e o `Game` (máquina de estados, pontuação única por pipe, colisão, congelamento em pausa).
- **Novos testes na v2**: glifos e métricas de `pixelfont` (largura/altura previsíveis, cache, caracteres não suportados), conversão de coordenada de toque → espaço lógico com letterbox (incluindo toque nas barras, que deve ser ignorado), `storage.save_dir()` nos dois caminhos (com e sem `ANDROID_ARGUMENT`, e com `ImportError` do módulo `android`), gravação incremental do recorde ao ultrapassar, e as ações `back`/`focus_lost` levando aos estados corretos.
- Manual: checklist de playtest por requisito (`tasks.md`), com os itens de Android separados por dependerem de hardware real — ver seção 25.

## 16. Chão (`ground.py`) — R7.3

- `Ground.update(speed)`: acumula `offset = (offset - speed) % BLOCK`, sincronizado com a velocidade do bioma atual (mesma fonte que `PipeManager.update`).
- `Ground.draw(surface, textures, block_main, block_edge)`: ladrilha blocos de `BLOCK×BLOCK` cobrindo a largura da tela a partir de `offset - BLOCK`; primeira fileira usa `block_edge` (grama/borda), demais usam `block_main`. Ao contrário dos pipes, **não congela** textura — usa sempre o bioma atual, já que é uma faixa contínua, não elementos discretos (R2.5 só se aplica a pipes).
- `Ground.rect`: `Rect(0, SCREEN_H - GROUND_H, SCREEN_W, GROUND_H)`, usado para colisão pássaro×chão (R3.1).

## 17. Decoração de fundo (`decor.py`) — R7.4

- `DecorManager` mantém dois acumuladores de scroll (`far_scrolled`, `near_scrolled`), incrementados por `speed * 0.3` e `speed * 0.6` a cada frame — nunca resetados com `%`, só usados módulo o período de cada camada no momento de desenhar.
- Tiling: `_tile(surface, scrolled, period, drawer)` calcula o índice do primeiro elemento visível (`scrolled // period`) e a posição inicial (`-(scrolled % period)`), chamando `drawer(surface, x, idx)` para cada slot visível.
- Cada elemento é uma forma quadriculada (pilha de retângulos, **nunca elipses**): `_draw_block_shape` desenha uma lista de `(deslocamento_em_unidades, largura_em_unidades)` por linha, de cima para baixo. `idx` semeia `random.Random(idx * salt + n)` para escolher a variante do elemento — determinístico por slot, então o visual não "pisca" ao rolar.
- Por bioma: Overworld → nuvens (`CLOUD_UNIT=14`) + colinas (`HILL_UNIT=18`, apoiadas no chão); Cave → estalactites (triângulos do teto) + veios de minério (clusters de pontos coloridos); Nether → poças de lava (retângulo raso no chão) + pilares (retângulo alto do chão até certa altura).

## 18. Distribuição e empacotamento — R13

- **Executável local**: `BlockyBird.spec` (gerado por `pyinstaller --onefile --windowed`, depois versionado e usado diretamente) builda com `uv run pyinstaller BlockyBird.spec`, produzindo `dist/BlockyBird.exe` (Windows) ou `dist/BlockyBird` (Linux/macOS). `pyinstaller` é dependência de **dev** apenas (`pyproject.toml`), não afeta a dependência de runtime do jogo (R9.2 continua valendo: só `pygame` + stdlib em tempo de execução) (R13.1).
- **CI/CD** (`.github/workflows/release.yml`): gatilho `release: types: [published]`. Job com matriz `[windows-latest, ubuntu-latest]`:
  1. `actions/checkout@v4`.
  2. Instala `uv` via script oficial (`install.ps1` / `install.sh`) — evita fixar versão de action de terceiros.
  3. `uv sync` + `uv run pyinstaller BlockyBird.spec`.
  4. Empacota: Windows → `Compress-Archive` gera `BlockyBird-windows-<tag>.zip`; Linux → `tar -cjf` gera `BlockyBird-linux-<tag>.tar.bz2` (nome inclui `github.event.release.tag_name`).
  5. Publica os assets na própria Release via `softprops/action-gh-release@v2` (`permissions: contents: write` no workflow) (R13.2).
- Na v2 esse mesmo workflow ganha um terceiro job para o APK (seção 24), totalizando três assets por release (R13.3).

---

# Parte II — Android (v2)

## 19. Fonte bitmap própria (`pixelfont.py`) — R7.6

**Problema.** A v1 renderiza todo texto com `pygame.font.SysFont("couriernew", size, bold=True)`. Android não possui Courier New — o SDL substituiria por uma fonte arbitrária (métricas e largura diferentes, quebrando o alinhamento centralizado das telas) ou falharia. Isso torna a UI da v1 inviável no Android.

**Solução.** Fonte bitmap 5×7 desenhada por código, no mesmo espírito das texturas (R7.1):

- Cada glifo é uma lista de 7 strings de 5 caracteres (`"#"` = pixel aceso, `"."` = vazio), definida como constante no módulo. Conjunto necessário, extraído de todos os textos do jogo: `A-Z`, `0-9`, `:`, `/`, `!`, `-`, espaço. Textos já são todos em maiúsculas na v1, então minúsculas não são necessárias (`draw_text` aplica `.upper()` por garantia).
- `render(text, scale, color) -> Surface`: monta uma `Surface` com `SRCALPHA`, acende os pixels de cada glifo como retângulos `scale × scale`, com 1 coluna de espaçamento entre glifos. Resultado já é pixel-perfeito por construção — **dispensa** o `SysFont` + `transform.scale` da v1.
- Cache: `dict[(text, scale, color)] -> Surface`, evitando remontar strings estáticas (título, instruções) a cada frame. O HUD de pontuação muda pouco (no máximo 1× por ponto), então o cache também o cobre bem.
- `ui.draw_text` passa a chamar `pixelfont.render`, mantendo a assinatura atual e o desenho da sombra dura. As chamadas existentes em `ui.py` seguem funcionando; o parâmetro `base_size` da v1 é convertido em `scale` (fator inteiro de pixel, `max(1, base_size // 2)`), preservando a hierarquia visual de tamanhos.

**Descoberto na implementação (task 20): a fonte bitmap é proporcionalmente mais larga que a `SysFont` antiga.** Cada glifo ocupa `5 + 1` unidades (glifo + espaçamento); numa fonte de sistema como Courier New os caracteres são mais estreitos e há hinting de kerning. Mapear `base_size` direto para uma escala fixa estourava a tela em 3 dos 9 textos reais do jogo: `"BLOCKY BIRD"` (585 px), `"ESPACO / CLIQUE PARA VOAR"` (745 px) e `"ESPACO / CLIQUE PARA REINICIAR"` (716 px) — todos acima dos 480 px disponíveis. Corrigido com um ajuste automático em `ui.py`:

```python
MAX_TEXT_W = SCREEN_W - 40   # margem de 20px de cada lado

def _fit_scale(text: str, scale: int) -> int:
    n = len(text)
    while scale > 1 and _text_width(n, scale) > MAX_TEXT_W:
        scale -= 1
    return scale
```

`draw_text` chama `_fit_scale` antes de renderizar, reduzindo a escala apenas o necessário para caber. Como é calculado por string (não hardcoded por tela), continua correto mesmo que os textos mudem no futuro — não é uma correção pontual para os 3 casos encontrados, é uma garantia geral.

**Fallback documentado.** Se o custo de desenhar os glifos se mostrar alto, a alternativa é `pygame.font.Font(None, size)`, que usa a fonte **embutida no próprio pygame** (disponível também no Android, sem depender do sistema). É a rota de menor esforço, porém sem controle pixel-a-pixel do traço — a fonte bitmap é a preferida por consistência visual e por eliminar a dependência do módulo `pygame.font`.

## 20. Escala lógica e letterbox (R9.1, R14.3)

Todo o jogo continua desenhando em coordenadas de 480×720 — nenhuma constante de gameplay muda, e por consequência a calibração de dificuldade da v1 (task 12) permanece válida.

```python
flags = pygame.SCALED | pygame.RESIZABLE          # desktop
flags = pygame.SCALED | pygame.FULLSCREEN         # Android
self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), flags)
```

- `pygame.SCALED` faz o SDL renderizar numa surface lógica de 480×720 e escalar para a janela/tela real **mantendo a proporção**, preenchendo o excedente com barras — letterbox (topo/base) ou pillarbox (laterais) conforme a proporção. É exatamente o comportamento pedido em R14.3, sem código de escala manual.
- Consequência para o input: coordenadas de mouse/toque precisam ser convertidas do espaço da tela real para o espaço lógico. Com `SCALED`, o pygame já entrega eventos de mouse em coordenadas lógicas. Eventos de **toque** (`FINGERDOWN`), porém, vêm normalizados em `0.0–1.0` relativos à *janela inteira* — incluindo as barras. A conversão está detalhada na seção 21.
- Overscan de TV: o letterbox já mantém a área de jogo longe das bordas laterais; os textos de UI ficam com margem natural. Não é necessário tratamento extra de safe area.

### 20.1 Aproveitamento de tela por aparelho (medido)

Aplicando a fórmula acima às resoluções típicas:

| Aparelho | Tela | Escala | Área de jogo | Barras | Área útil |
|---|---|---|---|---|---|
| Android TV 16:9 | 1920×1080 | 1,50× | 720×1080 | 600 px de cada lado | 38 % |
| Celular 9:20 | 1080×2400 | 2,25× | 1080×1620 | 390 px topo/base | 68 % |
| Celular 9:16 | 1080×1920 | 2,25× | 1080×1620 | 150 px topo/base | 84 % |
| Tablet 4:3 | 1600×1200 | 1,67× | 800×1200 | 400 px de cada lado | 50 % |

O celular fica confortável. A TV usa só 38 % da tela — é o custo consciente da decisão de manter a jogabilidade e a calibração de dificuldade idênticas em todo aparelho. Se isso incomodar na prática, a evolução natural (v3) é preencher as barras com céu e parallax estendidos, sem mexer na área jogável.

### 20.2 Incompatibilidade de `SCALED` com a suíte de testes atual (verificado)

Comportamento confirmado experimentalmente neste projeto, com pygame 2.6.1:

```
SDL_VIDEODRIVER=dummy + set_mode(SCALED):
  1ª chamada  -> OK  (com aviso "no fast renderer available")
  2ª chamada  -> pygame.error: failed to create renderer
```

`pygame.SCALED` exige criar um renderer SDL, e o driver de vídeo `dummy` — que o
`conftest.py` força para rodar headless — só permite **um** por processo. Como
`tests/test_game.py` instancia `Game()` (e portanto chama `set_mode`) em 6 testes
diferentes do mesmo processo, adotar `SCALED` ingenuamente **quebra a suíte**.

As variáveis de ambiente `SDL_RENDER_DRIVER=software` e
`SDL_FRAMEBUFFER_ACCELERATION=0` foram testadas e **não** resolvem.

Solução verificada: derrubar e reinicializar o display antes de cada `set_mode`, o que
funciona repetidamente:

```python
# fixture autouse em conftest.py
pygame.display.quit()
pygame.display.init()
```

A task 21 deve incluir esse ajuste no `conftest.py` como parte da entrega, e a suíte
completa deve passar antes de considerá-la concluída.

## 21. Entrada Android: toque, BACK e Android TV (R14.4, R15)

### 21.1 Toque (celular/tablet)

- O SDL sintetiza eventos de mouse a partir do toque por padrão, então `MOUSEBUTTONDOWN` já dispararia `flap` sem código novo. Ainda assim tratamos `pygame.FINGERDOWN` explicitamente, para (a) não depender desse comportamento default e (b) suportar toques simultâneos sem ambiguidade.
- `FINGERDOWN` traz `event.x`/`event.y` normalizados (0.0–1.0) em relação à janela real. Para decidir se o toque caiu no ícone de mudo é preciso converter para coordenadas lógicas, desfazendo o letterbox:

```python
win_w, win_h = pygame.display.get_window_size()
scale = min(win_w / SCREEN_W, win_h / SCREEN_H)      # fator do SCALED
draw_w, draw_h = SCREEN_W * scale, SCREEN_H * scale
off_x, off_y = (win_w - draw_w) / 2, (win_h - draw_h) / 2   # barras
lx = (event.x * win_w - off_x) / scale
ly = (event.y * win_h - off_y) / scale                # -> espaço lógico 480x720
```

- Toque fora da área lógica (nas barras) é ignorado; toque no ícone de mudo alterna mudo; qualquer outro toque na área de jogo emite `flap` (R15.1, R15.4).

**Descoberto na implementação (task 23): o `MOUSEBUTTONDOWN` sintetizado pelo toque real precisa do MESMO hit-test do ícone.** Se `MOUSEBUTTONDOWN` continuasse mapeando para `flap` incondicionalmente (como na v1), tocar no ícone de mudo no Android dispararia **os dois** eventos — `FINGERDOWN` (mudo, correto) e o `MOUSEBUTTONDOWN` sintético (flap, incorreto) — no mesmo frame. Resolvido com um `_handle_tap(actions, lx, ly)` único, chamado por ambos os handlers: `MOUSEBUTTONDOWN` passa `event.pos` direto (já em espaço lógico graças ao `SCALED`, confirmado na task 21); `FINGERDOWN` passa o resultado da conversão acima. `ui.MUTE_ICON_RECT` fica em `ui.py`, junto do `draw_mute_icon()` que o desenha, e `input.py` importa essa geometria para o hit-test — mantendo desenho e posição do botão como uma única fonte de verdade.

### 21.2 Botão BACK (R15.2, R15.3)

O SDL mapeia o BACK do Android para a tecla `pygame.K_AC_BACK`. O `InputManager` a traduz em uma ação `back`, e o `Game` decide pelo estado:

| Estado | BACK faz |
|---|---|
| JOGANDO | pausa (vira ação `pause`) |
| PRONTO / PAUSADO / GAME_OVER | encerra o jogo |

Esse desvio fica no `Game` (que conhece o estado), não no `InputManager` — mantendo a separação da v1 em que o input não conhece estados.

### 21.3 Android TV (R14.4)

- Android TV **não tem tela de toque** e é obrigatoriamente operável por D-pad/controle remoto. O SDL entrega o D-pad de duas formas, dependendo do aparelho: como joystick/gamepad (já suportado desde a v1, R10) ou como teclado (`K_RETURN`/`K_KP_ENTER` para o botão central, setas para as direções).
- Mapeamento adicional necessário: `K_RETURN`/`K_KP_ENTER` → `flap`. As setas ↑ já disparam `flap` na v1, o que cobre remotes que enviam D-pad como setas.
- Mudo sem tecla M e sem toque: no estado PAUSADO, D-pad ←/→ alterna mudo, com a dica escrita no overlay. Escolhido por não exigir um sistema de foco/navegação de menu — o overlay de pausa é a única tela onde isso é necessário, e a ação é reversível e sem risco.
- Nada disso exige detectar "é TV": os mapeamentos convivem com os de desktop (R15.5), então o mesmo binário atende celular e TV.

## 22. Ciclo de vida do app (R16.1, R16.2)

O pygame 2 expõe os eventos de ciclo de vida do SDL:

```python
elif event.type in (pygame.APP_WILLENTERBACKGROUND, pygame.APP_DIDENTERBACKGROUND):
    actions.add(ACTION_FOCUS_LOST)
```

- `Game` trata `focus_lost` transicionando JOGANDO → PAUSADO (R16.1). Nos outros estados é ignorado.
- Ao voltar (`APP_DIDENTERFOREGROUND`) o jogo **permanece** em PAUSADO — nenhuma retomada automática, para o jogador não perder a partida por causa de uma volta inesperada (R16.2).
- Como fallback em plataformas que não emitem os eventos de app, `pygame.WINDOWFOCUSLOST` recebe o mesmo tratamento (útil também no desktop: alt-tab pausa o jogo).
- O recorde já está salvo nesse ponto pela gravação incremental (seção 8), então um encerramento pelo sistema não perde nada (R16.4).

## 23. Armazenamento por plataforma (`storage.py`) — R4.5

A v1 grava `highscore.json` via caminho relativo, resolvido a partir do diretório de trabalho. No Android o diretório de trabalho **não é gravável**, e a escrita falharia silenciosamente (a v1 já engole `OSError`), fazendo o recorde nunca persistir.

```python
def is_android() -> bool:
    return "ANDROID_ARGUMENT" in os.environ     # definido pelo python-for-android

def save_dir() -> Path:
    if is_android():
        try:
            from android.storage import app_storage_path   # fornecido pelo p4a
            return Path(app_storage_path())
        except ImportError:
            return Path(os.environ.get("ANDROID_PRIVATE", "."))
    return Path(__file__).resolve().parent.parent          # raiz do projeto, no desktop
```

- Detecção por variável de ambiente (`ANDROID_ARGUMENT`), definida pelo p4a — não exige importar nada no desktop.
- Caminho Android: `app_storage_path()` do módulo `android` (embutido pelo p4a) devolve o diretório privado do app, gravável e preservado entre execuções. `ANDROID_PRIVATE` é o fallback.
- Caminho desktop: raiz do projeto, resolvida a partir do arquivo do módulo — mais robusto que o diretório de trabalho e continua compatível com a suíte de testes, que injeta um `tmp_path` explícito.
- `score.load_highscore()` / `save_highscore()` passam a usar `storage.save_dir() / "highscore.json"` como default, mantendo o parâmetro `path` opcional que os testes já usam.

**Descoberto na implementação (task 22): o default não pode ser um valor de parâmetro fixo.** `def load_highscore(path: Path = storage.save_dir() / "highscore.json")` calcularia o caminho **uma única vez, na importação do módulo** — clássica armadilha de default mutável/calculado em Python. Isso congelaria o resultado de `storage.save_dir()` para sempre no valor visto no import (impossibilitando reagir a mudança de plataforma em runtime, e tornando o comportamento impossível de isolar via `monkeypatch` nos testes). Corrigido resolvendo dentro do corpo da função, com `None` como sentinela:

```python
def _default_path() -> Path:
    return storage.save_dir() / "highscore.json"

def load_highscore(path: Path | None = None) -> int:
    path = path if path is not None else _default_path()
    ...
```

**Consequência para o isolamento dos testes.** A fixture `_isolate_cwd` do `conftest.py` (task 13) já isolava `highscore.json` via `monkeypatch.chdir(tmp_path)`, porque a v1 resolvia o caminho padrão relativo ao cwd. Como `storage.save_dir()` no desktop agora resolve a partir de `__file__` (não do cwd), o `chdir` sozinho deixou de bastar — a fixture precisou ganhar `monkeypatch.setattr("src.storage.save_dir", lambda: tmp_path)`. Isso, por sua vez, tornou `storage.save_dir()` impossível de testar de verdade em `tests/test_storage.py` (a fixture autouse mascarava a implementação real para todo teste); resolvido com `monkeypatch.undo()` no início dos testes que precisam da implementação real, revertendo a proteção só ali.

## 24. Empacotamento Android e CI do APK (R17)

### 24.1 Cadeia de build

Buildozer → python-for-android (p4a) → bootstrap SDL2 → APK. É a rota padrão para Python em Android e a única que preserva o código pygame existente (as alternativas exigiriam reescrever a renderização em Kivy ou migrar para WASM, o que não gera APK).

> **Risco conhecido, decidido conscientemente.** A receita de `pygame-ce` para o python-for-android **não está mergeada** no p4a — vive num pull request aberto ([kivy/python-for-android#2971](https://github.com/kivy/python-for-android/pull/2971), sem merge desde 2024). Portanto o projeto carrega sua **própria receita local** em `p4a-recipes/pygame-ce/__init__.py`, apontada por `p4a.local_recipes` no `buildozer.spec`. Consequências: (a) a receita é código nosso a manter; (b) atualizações de `pygame-ce` podem exigir ajuste na receita; (c) a task de build (28) deve tratar "a receita não compila" como resultado possível, e nesse caso a alternativa é fixar a versão de `pygame-ce` conhecida como funcional. Esse é o ponto de maior incerteza da v2 e deve ser atacado cedo.

### 24.2 `buildozer.spec` — pontos que importam

```ini
requirements = python3,pygame-ce,android
orientation = all                      # necessário p/ Android TV em paisagem (R17.4)
fullscreen = 1
p4a.local_recipes = ./p4a-recipes
p4a.bootstrap = sdl2

android.api = 34                       # target moderno
android.minapi = 21                    # Android 5.0+ (R14.1)
android.ndk_api = 21
android.archs = armeabi-v7a, arm64-v8a, x86_64      # (R14.2)
android.allow_backup = True
```

- `android` entra em `requirements` por causa do `android.storage` usado na seção 23.
- `orientation = all`: travar em `portrait` faria a activity ser forçada a retrato numa TV, que é paisagem por hardware — resultando em imagem girada ou recusa de execução. Com `all` + letterbox (seção 20), celular em retrato e TV em paisagem são ambos corretos. O efeito colateral é que girar o celular também gira o jogo (pillarbox); aceitável.
- Android TV, via injeção no manifesto (R17.3):
  - `<uses-feature android:name="android.hardware.touchscreen" android:required="false" />` — sem isso a TV não reconhece o app como compatível.
  - `<uses-feature android:name="android.software.leanback" android:required="false" />` — não obrigatório, mantendo o APK instalável em celular.
  - `<category android:name="android.intent.category.LEANBACK_LAUNCHER" />` no intent principal, para o app aparecer na home da TV.
  - Banner de 320×180 (`android.banner`), gerado por código a partir das texturas do jogo (mantendo R7.1) e salvo como PNG no build.
- Assinatura: build `debug` (`buildozer android debug`), assinado com a chave de debug do Android SDK. Instala direto com "fontes desconhecidas" habilitado; não serve para Play Store (fora de escopo, R17.1).

### 24.3 Job de CI do APK (R17.2)

Acrescentado ao `release.yml` existente, como job independente dos de desktop (matriz Windows/Linux da seção 18):

1. `runs-on: ubuntu-latest` — Buildozer exige Linux.
2. Build dentro de container Docker (`kivy/buildozer` ou imagem própria) para ter Android SDK/NDK reprodutíveis, evitando instalar a toolchain no runner.
3. Cache de `~/.buildozer` e `.buildozer` via `actions/cache` — sem cache, o primeiro build baixa SDK+NDK e compila CPython+SDL2+pygame-ce, tipicamente 30–60 min.
4. `buildozer android debug` → APK em `bin/`.
5. Renomear para `BlockyBird-<tag>.apk` e publicar **sem compressão** via `softprops/action-gh-release@v2` — o `.apk` já é um zip; comprimir de novo só atrapalharia a instalação direta (R17.2).

O job é independente para que uma falha no build Android (o passo mais frágil, ver risco em 24.1) não impeça a publicação dos binários de desktop.

## 25. Limites de verificação nesta versão

Registrado explicitamente porque afeta como as tasks devem ser aceitas:

- **Não há aparelho Android nem emulador neste ambiente de desenvolvimento**, e o Docker local não está acessível (verificado na v1, ao tentar validar o workflow com `act`). Logo, os itens que dependem de Android real — instalar o APK, jogar por toque, operar por controle remoto de TV, medir FPS em aparelho de entrada, confirmar persistência do recorde no storage do app — **precisam de validação manual pelo dono do projeto**.
- O que **pode** ser verificado automaticamente aqui: fonte bitmap (comparação de superfícies renderizadas), conversão de coordenadas de toque para espaço lógico (função pura, testável), resolução do diretório de save por plataforma (com `ANDROID_ARGUMENT` monkeypatched), transições de estado por ações `back`/`focus_lost` (eventos sintéticos), e o jogo inteiro no desktop com `SCALED` (incluindo redimensionamento de janela).
- O checklist manual em `tasks.md` marca claramente qual item é de qual categoria. Nenhum item dependente de hardware deve ser marcado como concluído sem teste real.
