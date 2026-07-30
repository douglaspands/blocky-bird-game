# Design Técnico — Blocky Bird

Rastreabilidade: cada seção referencia os requisitos (R1–R13) de `requirements.md`.

## 1. Visão geral

Jogo 2D em Python 3.10+ / Pygame 2.5+, loop de jogo com timestep fixo a 60 FPS (R9). Arquitetura orientada a objetos com máquina de estados simples e separação entre lógica, renderização e áudio.

## 2. Estrutura do projeto

```
flappy_bird/
├── pyproject.toml       # Projeto gerenciado por uv (R9.3)
├── uv.lock              # Lockfile gerado por uv
├── main.py              # Entry point: cria Game e roda o loop (R9.3)
├── BlockyBird.spec      # Config do PyInstaller p/ executavel standalone (R13.1)
├── .github/workflows/
│   └── release.yml      # CI: builda e publica executaveis na Release (R13.2)
├── specs/               # Specs versionadas (esta pasta é specs/v1/, ver specs/README.md)
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
    ├── particles.py     # Sistema de partículas de blocos (R3.2)
    ├── textures.py      # Geração procedural de texturas voxel (R7)
    ├── input.py         # InputManager: teclado, mouse e controle Xbox (R10)
    ├── sounds.py        # Síntese de sons 8-bit (R8)
    └── ui.py            # HUD, telas PRONTO/PAUSADO/GAME_OVER, fonte pixelada (R6, R7.5, R11, R12)
```

### 2.1 Gerenciamento com uv (R9.3)

Projeto inicializado com `uv init`; `pygame>=2.5` declarado como dependência de runtime, `pytest` e `pyinstaller` como dependências de **dev** no `pyproject.toml` (R13.1). Comandos padrão:

```bash
uv sync                              # cria/atualiza o ambiente
uv run main.py                       # executa o jogo
uv run pytest                        # roda os testes
uv run pyinstaller BlockyBird.spec   # gera o executavel standalone (R13.1)
```

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
SCREEN_W, SCREEN_H = 480, 720
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
- Persistência: `highscore.json` na raiz — `{"highscore": int}`. Leitura com `try/except (OSError, ValueError, KeyError)` → fallback 0 (R4.4). Gravação apenas em GAME_OVER se superou (R4.3).

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

## 12. UI (`ui.py`) — R6, R7.5, R11, R12

- Fonte: `pygame.font.SysFont("couriernew", ...)` renderizada sem anti-aliasing e escalada 3× (`pygame.transform.scale`) para efeito pixelado; sempre com sombra dura (offset 3 px, marrom-escuro) (R7.5).
- HUD: pontuação centralizada no topo (R4.2). Telas: PRONTO, PAUSADO (overlay escurecido, R6.3), GAME_OVER (painel com pontuação/recorde, R3.3).
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

Input unificado (R1.1, R10): eventos de teclado, mouse e joystick mapeiam para ações abstratas em `input.py`:

| Ação | Teclado/Mouse | Controle Xbox |
|---|---|---|
| `flap` (voar/reiniciar) | ESPAÇO, ↑, clique | Botão A (`JOYBUTTONDOWN`, button 0) |
| `pause` | ESC, P | Start (button 7) |
| `mute` | M | Y (button 3) |

- `src/input.py`: classe `InputManager` que consome `pygame.event` e retorna set de ações; os estados só conhecem ações, não dispositivos (R10.4).
- Init: `pygame.joystick.init()` + inicialização de todos os joysticks presentes (R10.1).
- Hotplug: tratar `JOYDEVICEADDED`/`JOYDEVICEREMOVED` reinicializando o joystick correspondente (R10.2); ausência de controle não afeta o jogo (R10.5).
- Índices de botão seguem o mapeamento padrão do controle Xbox no SDL2/Windows; validar no playtest (task 12).

## 14. Tratamento de erros

| Falha | Comportamento |
|---|---|
| Mixer indisponível | jogo sem som (R8.4) |
| highscore.json corrompido, ausente ou com chave/tipo inválido | recorde 0, sobrescreve ao salvar (R4.4) |
| Nenhum controle Xbox conectado | jogo funciona normalmente com teclado/mouse (R10.5) |

## 15. Estratégia de testes

- Unitários (`pytest`, 35 testes em `tests/`, sem abrir janela — `conftest.py` força `SDL_VIDEODRIVER=dummy` e isola cada teste em um `tmp_path` para nunca ler/gravar o `highscore.json` real): física do Bird (gravidade, clamp, impulso, ângulo, hitbox, idle bob), spawn/remoção/movimento/congelamento de textura de pipes, thresholds e timers de bioma, persistência do recorde (arquivo ausente/corrompido/tipo inválido), e o `Game` (máquina de estados, pontuação única por pipe, colisão, congelamento em pausa).
- Manual: checklist de playtest por requisito (task 13 do plano).

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
