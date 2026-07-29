# Design Técnico — Blocky Bird

Rastreabilidade: cada seção referencia os requisitos (R1–R9) de `requirements.md`.

## 1. Visão geral

Jogo 2D em Python 3.10+ / Pygame 2.5+, loop de jogo com timestep fixo a 60 FPS (R9). Arquitetura orientada a objetos com máquina de estados simples e separação entre lógica, renderização e áudio.

## 2. Estrutura do projeto

```
flappy_bird/
├── pyproject.toml       # Projeto gerenciado por uv (R9.3)
├── uv.lock              # Lockfile gerado por uv
├── main.py              # Entry point: cria Game e roda o loop (R9.3)
├── specs/               # Estes documentos
└── src/
    ├── __init__.py
    ├── config.py        # Constantes: tela, física, biomas, cores
    ├── game.py          # Classe Game: loop, máquina de estados (R6)
    ├── bird.py          # Classe Bird: física e animação (R1)
    ├── pipes.py         # PipePair + PipeManager (R2)
    ├── biome.py         # Definições e transição de biomas (R5)
    ├── score.py         # Pontuação e persistência do recorde (R4)
    ├── particles.py     # Sistema de partículas de blocos (R3.2)
    ├── textures.py      # Geração procedural de texturas voxel (R7)
    ├── input.py         # InputManager: teclado, mouse e controle Xbox (R10)
    ├── sounds.py        # Síntese de sons 8-bit (R8)
    └── ui.py            # HUD, telas PRONTO/PAUSADO/GAME_OVER, fonte pixelada (R6, R7.5)
```

### 2.1 Gerenciamento com uv (R9.3)

Projeto inicializado com `uv init`; `pygame>=2.5` e `pytest` (dev) declarados no `pyproject.toml`. Comandos padrão:

```bash
uv sync              # cria/atualiza o ambiente
uv run main.py       # executa o jogo
uv run pytest        # roda os testes
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
GRAVITY = 0.45          # px/frame²
FLAP_IMPULSE = -8.5     # px/frame
MAX_FALL_SPEED = 12
GROUND_H = 96
PIPE_SPACING = 260      # distância horizontal entre pares
PIPE_W = 78             # largura da coluna (bloco 16px × escala ~4.8 → arredondar p/ múltiplo)
BLOCK = 48              # tamanho do bloco renderizado (16×16 escalado 3×)
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
    gap_size: int         # do bioma (R2.2)
    scored: bool          # p/ pontuação única (R4.1)
    biome_id: str         # textura congelada na criação (R2.5)
```

- `PipeManager.update(speed)`: move todos `x -= speed` (R2.3); spawna novo par quando o último está a `PIPE_SPACING` da borda (R2.1); remove pares com `x + PIPE_W < 0` (R2.4).
- `gap_y` aleatório uniforme entre margens seguras (topo + 80, chão − 80) (R2.2).
- Renderização: coluna = pilha de blocos `BLOCK×BLOCK` com textura do bioma; bloco da boca da abertura usa variante de borda (ex.: grama no Overworld) (R2.5).
- Colisão: dois `Rect` por par (superior e inferior); `bird.rect.colliderect()` (R3.1).

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
    Biome("nether",    "Nether",    25, 3.5, 130, ...),
]
```

- `BiomeManager.update(score)`: detecta cruzamento de threshold → inicia fade de 60 frames entre gradientes de céu (R5.4), mostra banner com nome do bioma por 90 frames, toca som de portal (R8.1).
- Colunas já existentes mantêm textura antiga; novas usam o bioma novo (transição natural).
- Decoração parallax (R7.4): duas camadas com fatores 0.3 e 0.6 da velocidade de rolagem; elementos desenhados proceduralmente (nuvens/colinas, estalactites/minérios, mar de lava/pilares).

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

- Síntese com `numpy` + `pygame.sndarray` (numpy é dependência do pygame em muitas instalações; se ausente, gerar via `array` stdlib): ondas quadradas com envelope de decaimento e sweeps de frequência.
  - `flap`: sweep 300→500 Hz, 80 ms.
  - `score`: dois pings 800/1200 Hz, 120 ms (estilo XP orb).
  - `hit`: ruído branco com decay, 200 ms.
  - `portal`: sweep descendente 900→200 Hz, 400 ms.
- `pygame.mixer.init()` em `try/except` → flag `audio_ok`; toda chamada de play checa flag e `muted` (R8.3, R8.4).

## 12. UI (`ui.py`) — R6, R7.5

- Fonte: `pygame.font.SysFont("couriernew", ...)` como fallback, mas preferencial é renderizar texto com fonte bitmap própria simples OU usar `pygame.font.Font(None)` escalado com `scale` inteiro para efeito pixelado; sempre com sombra dura (offset 2–3 px, cinza-escuro) (R7.5).
- HUD: pontuação centralizada no topo (R4.2). Telas: PRONTO (título + instruções, R6.1), PAUSADO (overlay escurecido, R6.3), GAME_OVER (painel com pontuação/recorde, R3.3).

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
| highscore.json corrompido | recorde 0, sobrescreve ao salvar (R4.4) |
| numpy ausente | fallback de síntese via stdlib ou sem som |

## 15. Estratégia de testes

- Unitários (`pytest`, sem abrir janela — usar `SDL_VIDEODRIVER=dummy`): física do Bird (gravidade, clamp, impulso), spawn/remoção/colisão de pipes, thresholds de bioma, pontuação única por pipe, persistência do recorde (arquivo ausente/corrompido).
- Manual: checklist de playtest por requisito (task 13 do plano).
