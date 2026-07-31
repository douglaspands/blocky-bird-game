# Design Técnico — Blocky Bird

Rastreabilidade: cada seção referencia os requisitos (R1–R21) de `requirements.md`.

As seções 1–18 (**Parte I**) descrevem o jogo base, herdado da v1 com os ajustes que o Android exigiu, sinalizados como "(v2)" no texto. As seções 19–25 (**Parte II**) são inteiramente novas na v2, cobrindo Android. As seções 26–29 (**Parte III**) são aumentos de escopo posteriores da v2, adicionados após a entrega Android: conformidade com `ruff`, calibração do tamanho de fonte, conformidade com `ty` e o ícone do aplicativo.

---

# Parte I — Jogo base

## 1. Visão geral

Jogo 2D em Python 3.10+ / `pygame-ce` 2.5+, loop de jogo com timestep fixo a 60 FPS (R9). Arquitetura orientada a objetos com máquina de estados simples e separação entre lógica, renderização e áudio.

**v2 — alvo duplo desktop + Android.** O mesmo código-fonte roda em Windows/Linux (executável PyInstaller, R13) e em Android celular/tablet, sempre em retrato (APK Buildozer, R17). A estratégia para isso é manter *todo* o jogo escrito contra uma resolução lógica fixa de 480×720 e uma camada de ações abstratas de input, empurrando as diferenças de plataforma para três pontos isolados:

| Diferença | Onde é resolvida |
|---|---|
| Tela de tamanho/proporção arbitrária | `pygame.SCALED` no `set_mode`, escala + letterbox automáticos (seção 20) |
| Toque, BACK do Android | `input.py`, traduzidos para as mesmas ações abstratas já existentes (seção 21) |
| Onde se pode gravar arquivo | `storage.py`, resolve o diretório por plataforma (seção 23) |

Nenhum módulo de gameplay (`bird`, `pipes`, `biome`, `score`, `particles`, `decor`, `ground`) precisa saber em que plataforma está rodando.

## 2. Estrutura do projeto

```
flappy_bird/
├── pyproject.toml       # Projeto gerenciado por uv (R9.3)
├── uv.lock              # Lockfile gerado por uv
├── main.py              # Entry point: cria Game e roda o loop (R9.3)
├── BlockyBird.spec      # Config do PyInstaller p/ executavel standalone (R13.1, icone R21.3)
├── buildozer.spec       # Config do Buildozer p/ APK Android (R17.1, icone R21.4-6)
├── p4a-recipes/
│   └── pygame-ce/       # Receita local de build do pygame-ce p/ p4a (sec. 24) [novo na v2]
├── assets/              # PNGs/ICO gerados por script (icones)                [icones: sec. 29]
│   ├── app_icon.ico
│   ├── app_icon_512.png
│   ├── android_icon_legacy.png
│   ├── android_icon_foreground.png
│   └── android_icon_background.png
├── scripts/
│   └── generate_app_icon.py   # Gera todas as variacoes do icone (sec. 29)
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
    ├── assets.py        # Resolve caminho de asset bundlado (fonte/empacotado) (R21.2)
    ├── particles.py     # Sistema de partículas de blocos (R3.2)
    ├── textures.py      # Geração procedural de texturas voxel (R7)
    ├── pixelfont.py     # Fonte bitmap gerada por código (R7.6)               [novo na v2]
    ├── scale.py         # fit_scale: letterbox p/ toque, sem cortar imagem (R14.3)
    ├── input.py         # InputManager: teclado, mouse, gamepad, toque (R10, R15)
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

> **Migração `pygame` → `pygame-ce` (v2).** `pygame-ce` é um fork mantido pela comunidade, compatível a nível de API e importado igualmente como `import pygame`. A troca é feita apenas no `pyproject.toml` (`pygame>=2.5` → `pygame-ce>=2.5`); nenhum `import` muda. O motivo é que a cadeia de build Android escolhida (python-for-android) tem receita para `pygame-ce`, não para o `pygame` upstream. Os dois pacotes instalam o mesmo módulo `pygame` e **não podem coexistir** no mesmo ambiente — o `uv sync` após a troca já resolve isso sozinho (confirmado: desinstala um, instala o outro, sem precisar de `--reinstall`).
>
> **Efeito colateral encontrado (task 26): `pygame-ce` trouxe SDL 2.32.10** (a v1 rodava com SDL 2.28.4, empacotado junto do `pygame` antigo). No SDL novo, `pygame.display.set_mode(..., SCALED)` sob `SDL_VIDEODRIVER=dummy` passou a enfileirar uma sequência de eventos de janela na criação (`WindowShown`, `WindowFocusGained`/`WindowFocusLost`, `ActiveEvent`...) que não existia antes — incluindo um `WindowFocusLost` genuíno, que a v2 acabara de passar a tratar como pausa automática (task 24). Sem tratamento, isso contaminava o primeiro `poll()` de qualquer teste com uma ação `focus_lost` espúria. Confirmado com um driver de vídeo real que essa sequência de eventos **não inclui** `WindowFocusLost` — é um artefato específico do driver `dummy` usado só nos testes, não afeta jogadores de verdade. Corrigido com `pygame.event.clear()` logo após o `set_mode()`, tanto em `Game.__init__()` (defensivo) quanto nos testes que criam janela diretamente.

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
- **Controle de mudo na tela (v2, R15.4)**: ícone de alto-falante desenhado por código no canto superior direito da área lógica, com área de toque generosa (mínimo 44×44 px lógicos) para ser confortável no celular. Estado (com som / mudo) refletido no ícone. Em PAUSADO, o overlay mostra também a dica de mudo por setas do teclado (seção 21.3).
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

| Ação | Teclado/Mouse | Controle Xbox | Android (toque) |
|---|---|---|---|
| `flap` (voar/reiniciar) | ESPAÇO, ↑, clique, ENTER | Botão A (`JOYBUTTONDOWN`, button 0) | Toque na área de jogo |
| `pause` | ESC, P | Start (button 7) | BACK durante JOGANDO (R15.2) |
| `mute` | M, ←/→ em PAUSADO | Y (button 3) | Toque no ícone de mudo |
| `quit` | — | — | BACK fora de JOGANDO (R15.3) |

- `src/input.py`: classe `InputManager` que consome `pygame.event` e retorna set de ações; os estados só conhecem ações, não dispositivos (R10.4, R15.5).
- Init: `pygame.joystick.init()` + inicialização de todos os joysticks presentes (R10.1).
- Hotplug: tratar `JOYDEVICEADDED`/`JOYDEVICEREMOVED` reinicializando o joystick correspondente (R10.2); ausência de controle não afeta o jogo (R10.5).
- Índices de botão seguem o mapeamento padrão do controle Xbox no SDL2/Windows; validar no playtest (task 12).
- Detalhes do input Android (toque, BACK) na seção 21.

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
- **CI/CD** (`.github/workflows/release.yml`): gatilho `release: types: [published]`. Job com matriz `include` (`os`, `platform`, `arch`): `windows-latest`/`windows`/`x64` e `ubuntu-latest`/`linux`/`x64` — `platform`/`arch` explícitos na matriz (não derivados de `runner.arch` em runtime) porque expressões do Actions não têm função de lowercase nativa:
  1. `actions/checkout@v4`.
  2. Instala `uv` via script oficial (`install.ps1` / `install.sh`) — evita fixar versão de action de terceiros.
  3. `uv sync` + `uv run pyinstaller BlockyBird.spec`.
  4. Empacota: Windows → `Compress-Archive` gera `BlockyBird-windows-x64-<tag>.zip`; Linux → `tar -cjf` gera `BlockyBird-linux-x64-<tag>.tar.bz2` (nome inclui plataforma, arquitetura e `github.event.release.tag_name`).
  5. Publica os assets na própria Release via `softprops/action-gh-release@v2` (`permissions: contents: write` no workflow) (R13.2).
- Na v2 esse mesmo workflow ganha um terceiro job para o APK (seção 24), totalizando três assets por release (R13.3). APK é um build "fat" com múltiplas ABIs (`android.archs` no `buildozer.spec`: `armeabi-v7a, arm64-v8a, x86_64`), então o asset é nomeado `BlockyBird-android-universal-<tag>.apk` em vez de citar uma arquitetura única.

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

## 20. Escala lógica e letterbox (R9.1, R14.3, R14.4)

Todo o jogo continua desenhando em coordenadas de 480×720 — nenhuma constante de gameplay muda, e por consequência a calibração de dificuldade da v1 (task 12) permanece válida.

```python
self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.SCALED | pygame.RESIZABLE)
```

Mesma chamada em desktop e Android, sem nenhum branch por plataforma — no Android, `fullscreen = 1` no `buildozer.spec` (seção 24.2) já faz a Activity ocupar o aparelho inteiro, e `orientation = portrait` trava a orientação (R14.4).

- `pygame.SCALED` faz o SDL renderizar numa surface lógica de 480×720 e escalar para a janela/tela real **mantendo a proporção**, preenchendo o excedente com uma barra — letterbox (topo/base) ou pillarbox (laterais), conforme a proporção — sem código de escala manual.
- **Por que a barra é sempre letterbox, nunca pillarbox (R14.3).** O canvas lógico do jogo é 480×720 (proporção 2:3 ≈ 0,667 largura/altura). Com `pygame.SCALED` (escala = `min(janela_w/480, janela_h/720)`), a barra sobra no eixo cuja razão NÃO é a menor das duas — ou seja, pillarbox (laterais) só ocorre quando a janela é proporcionalmente **mais larga** que 2:3. Como a orientação fica travada em retrato (R14.4), a janela do Android nunca fica mais larga que alta; a esmagadora maioria dos celulares é proporcionalmente mais alongada que 2:3 (ex. 20:9 ≈ 0,45), então a barra que sobra é sempre letterbox. Aparelhos hipotéticos mais "quadrados" que 2:3 em retrato (ex. um tablet 4:3) ainda sobrariam algum pillarbox mesmo travados em retrato — aceito conscientemente, dado que a esmagadora maioria dos aparelhos-alvo é mais alongada que a base.
- Consequência para o input: coordenadas de mouse já chegam convertidas para o espaço lógico pelo próprio SDL sob `SCALED`. Eventos de **toque** (`FINGERDOWN`), porém, vêm normalizados em `0.0–1.0` relativos à *janela inteira* — incluindo a barra. A conversão está detalhada na seção 21.

### 20.1 Aproveitamento de tela por aparelho (medido)

Aplicando a fórmula acima às resoluções típicas de celular/tablet em retrato:

| Aparelho | Tela | Escala | Área de jogo | Barra | Área útil |
|---|---|---|---|---|---|
| Celular 9:20 | 1080×2400 | 2,25× | 1080×1620 | 390 px topo/base | 68 % |
| Celular 9:16 | 1080×1920 | 2,25× | 1080×1620 | 150 px topo/base | 84 % |
| Tablet 4:3 (retrato) | 1200×1600 | 2,22× | 1067×1600 | 67 px de cada lado | 89 % |

O tablet 4:3 é o exemplo do caso "mais quadrado que 2:3" citado acima — mesmo em retrato, sobra um pillarbox pequeno, aceito conscientemente.

### 20.2 Incompatibilidade de `SCALED` com a suíte de testes atual (verificado)

Comportamento confirmado experimentalmente neste projeto:

```
SDL_VIDEODRIVER=dummy + set_mode(SCALED):
  1ª chamada  -> OK  (com aviso "no fast renderer available")
  2ª chamada  -> pygame.error: failed to create renderer
```

`pygame.SCALED` exige criar um renderer SDL, e o driver de vídeo `dummy` — que o
`conftest.py` força para rodar headless — só permite **um** por processo. Como
`tests/test_game.py` instancia `Game()` (e portanto chama `set_mode`) em vários testes
diferentes do mesmo processo, adotar `SCALED` ingenuamente **quebra a suíte**.

As variáveis de ambiente `SDL_RENDER_DRIVER=software` e
`SDL_FRAMEBUFFER_ACCELERATION=0` foram testadas e **não** resolvem.

Solução verificada: derrubar e reinicializar o display antes de cada `set_mode`, o que
funciona repetidamente:

```python
# fixture autouse em conftest.py (_reset_display)
pygame.display.quit()
pygame.display.init()
```

## 21. Entrada Android: toque e BACK (R15)

### 21.1 Toque (celular/tablet)

- O SDL sintetiza eventos de mouse a partir do toque por padrão, então `MOUSEBUTTONDOWN` já dispararia `flap` sem código novo. Ainda assim tratamos `pygame.FINGERDOWN` explicitamente, para (a) não depender desse comportamento default e (b) suportar toques simultâneos sem ambiguidade.
- `FINGERDOWN` traz `event.x`/`event.y` normalizados (0.0–1.0) em relação à janela real. Para decidir se o toque caiu no ícone de mudo é preciso converter para coordenadas lógicas, desfazendo o letterbox de `pygame.SCALED` (`InputManager._touch_to_logical`, seção 20 — usa `scale.fit_scale`, escala **min**/fit):

```python
win_w, win_h = pygame.display.get_window_size()
scale, off_x, off_y = fit_scale(SCREEN_W, SCREEN_H, win_w, win_h)  # escala = MIN dos dois eixos
lx = (event.x * win_w - off_x) / scale
ly = (event.y * win_h - off_y) / scale                # -> espaço lógico 480x720
```

- Toque fora da área lógica (na barra de letterbox) é ignorado — não dispara `flap` nem `mute`; toque no ícone de mudo alterna mudo; qualquer outro toque na área de jogo emite `flap` (R15.1, R15.4).

**Descoberto na implementação (task 23): o `MOUSEBUTTONDOWN` sintetizado pelo toque real precisa do MESMO hit-test do ícone.** Se `MOUSEBUTTONDOWN` continuasse mapeando para `flap` incondicionalmente (como na v1), tocar no ícone de mudo no Android dispararia **os dois** eventos — `FINGERDOWN` (mudo, correto) e o `MOUSEBUTTONDOWN` sintético (flap, incorreto) — no mesmo frame. Resolvido com um `_handle_tap(actions, lx, ly)` único, chamado por ambos os handlers: com `pygame.SCALED` em uso, `MOUSEBUTTONDOWN` passa `event.pos` direto (já convertido para o espaço lógico pelo próprio SDL); `FINGERDOWN` passa pela conversão manual acima. `ui.MUTE_ICON_RECT` fica em `ui.py`, junto do `draw_mute_icon()` que o desenha, e `input.py` importa essa geometria para o hit-test — mantendo desenho e posição do botão como uma única fonte de verdade.

### 21.2 Botão BACK (R15.2, R15.3)

O SDL mapeia o BACK do Android para a tecla `pygame.K_AC_BACK`. O `InputManager` a traduz em uma ação `back`, e o `Game` decide pelo estado:

| Estado | BACK faz |
|---|---|
| JOGANDO | pausa (vira ação `pause`) |
| PRONTO / PAUSADO / GAME_OVER | encerra o jogo |

Esse desvio fica no `Game` (que conhece o estado), não no `InputManager` — mantendo a separação da v1 em que o input não conhece estados.

### 21.3 Mapeamentos adicionais de teclado (R15.4, R15.5)

`K_RETURN`/`K_KP_ENTER` mapeiam para `flap` e as setas ←/→ alternam mudo no overlay de PAUSADO — mapeamentos adicionais aos de teclado/mouse/gamepad já cobertos (R10, R15.5), inofensivos em qualquer plataforma (Enter já é um atalho razoável também no desktop).

**Bug real encontrado ao revisar a alcançabilidade.** Um perfil de entrada só com teclas de seta, Enter e BACK — sem tecla ESC/P e sem botão Start de gamepad — conseguia pausar (BACK durante JOGANDO, seção 21.2) mas **não tinha como despausar**: `_flap_action()` não tratava o estado PAUSADO (era no-op), e BACK em PAUSADO encerra o jogo em vez de alternar. O único caminho restante era sair. O mesmo gap afetava quem só usa toque no celular (tocar a tela tampouco despausava). Corrigido fazendo `_flap_action()` também transicionar PAUSADO → JOGANDO (sem chamar `bird.flap()`, para não dar um pulo indesejado ao retomar) — reaproveitando a mesma ação primária (RETURN/toque) já usada para iniciar e reiniciar, em vez de inventar um mecanismo novo.

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

def is_frozen() -> bool:
    return getattr(sys, "frozen", False)        # definido pelo PyInstaller no executavel empacotado

def save_dir() -> Path:
    if is_android():
        try:
            from android.storage import app_storage_path   # fornecido pelo p4a
            return Path(app_storage_path())
        except ImportError:
            return Path(os.environ.get("ANDROID_PRIVATE", "."))
    if is_frozen():
        return Path(sys.executable).resolve().parent       # pasta do .exe/binario empacotado
    return Path(__file__).resolve().parent.parent          # raiz do projeto, rodando de fonte
```

- Detecção por variável de ambiente (`ANDROID_ARGUMENT`), definida pelo p4a — não exige importar nada no desktop.
- Caminho Android: `app_storage_path()` do módulo `android` (embutido pelo p4a) devolve o diretório privado do app, gravável e preservado entre execuções. `ANDROID_PRIVATE` é o fallback.
- Caminho desktop rodando de fonte: raiz do projeto, resolvida a partir do arquivo do módulo — mais robusto que o diretório de trabalho e continua compatível com a suíte de testes, que injeta um `tmp_path` explícito.
- Caminho desktop empacotado (`BlockyBird.spec`/PyInstaller, R13): a pasta do executável, resolvida a partir de `sys.executable`.
- `score.load_highscore()` / `save_highscore()` passam a usar `storage.save_dir() / "highscore.json"` como default, mantendo o parâmetro `path` opcional que os testes já usam.

**Bug pós-lançamento (v1.0.0): recorde não persistia no executável empacotado do Windows.** `BlockyBird.spec` gera um executável **onefile** (`EXE(pyz, a.scripts, a.binaries, a.datas, ...)` em uma única chamada). Nesse modo, o PyInstaller extrai o conteúdo empacotado para um diretório temporário (`sys._MEIPASS`) a cada execução e é **esse** diretório que `__file__` resolve dentro do `.exe` — não a pasta onde o executável está. Como o diretório é apagado quando o processo termina, `highscore.json` nunca aparecia ao lado do `.exe` e o recorde se perdia a cada fechamento. O mesmo problema afeta o build Linux (mesmo `.spec`), só não havia sido reportado ainda. Corrigido detectando o modo empacotado via `sys.frozen` (atributo que o PyInstaller injeta em tempo de execução) e usando `Path(sys.executable).resolve().parent` nesse caso — a pasta real do executável, preservada entre execuções e coerente com a distribuição em zip/tar portátil (R13.2), que não instala em local somente-leitura como `Program Files`. `tests/test_storage.py::test_save_dir_frozen_desktop_uses_executable_dir` cobre o caso simulando `sys.frozen`/`sys.executable` via `monkeypatch`. Validado também manualmente: build real via `uv run pyinstaller BlockyBird.spec`, simulação do modo `frozen` apontando para `dist/BlockyBird.exe` e confirmação de que `highscore.json` é criado e lido corretamente ao lado do executável.

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

> **Atualização (task 28): o risco se confirmou parcialmente, e foi resolvido.** O Docker ficou acessível neste ambiente de desenvolvimento (algo que a seção 25 originalmente dava como indisponível) e o build real foi executado até `BUILD SUCCESSFUL`, gerando um APK de fato. A receita copiada do PR upstream tinha dois bugs reais, só visíveis ao tentar compilar de verdade:
> 1. Faltava `'cython'` em `depends` — `setup.py build_ext` falha com "You need cython" sem isso (outras receitas do p4a que compilam `.pyx`, como `numpy`/`av`, declaram essa dependência; a cópia do PR não).
> 2. `sdl_image_includes` apontava para a raiz de `jni/SDL2_image`, mas a versão do `sdl2_image` recipe do p4a (2.8.0) move o header público para `jni/SDL2_image/include/SDL_image.h` — diferente do `SDL2_ttf`, que mantém `SDL_ttf.h` na raiz (mesmo padrão, layout diferente).
>
> Nenhum dos dois exigiu trocar a versão do `pygame-ce` (2.5.7 seguiu funcionando) — só corrigir a receita em si. Também apareceu um bug não relacionado ao pygame-ce, no próprio `jpeg` recipe **built-in do p4a**: seu `CMakeLists.txt` (libjpeg-turbo 2.0.1) exige `cmake_minimum_required` < 3.5, incompatível com o CMake 4.2.3 do container `kivy/buildozer` atual — resolvido com uma receita local própria (`p4a-recipes/jpeg/__init__.py`) que passa `-DCMAKE_POLICY_VERSION_MINIMUM=3.5`. Isso ilustra um risco mais amplo que a seção 24.1 original não cobria: **o ambiente de build (versão do CMake, do compilador, do próprio p4a) pode driftar independentemente do código do projeto**, já que a imagem `kivy/buildozer` não é pinada por hash — um rebuild futuro pode reintroduzir problemas parecidos mesmo sem nenhuma mudança no repositório.

### 24.2 `buildozer.spec` — pontos que importam

```ini
requirements = python3,pygame-ce,android
orientation = portrait                 # trava retrato, elimina pillarbox (R14.3/R14.4)
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
- `orientation = portrait`: trava a activity em retrato — o jogo nunca roda em paisagem no Android, mesmo se o aparelho for girado. É o que garante, combinado com `pygame.SCALED` (seção 20), que a barra de letterbox sobre sempre no topo/base e nunca nas laterais (pillarbox).
- Assinatura: build `debug` (`buildozer android debug`), assinado com a chave de debug do Android SDK. Instala direto com "fontes desconhecidas" habilitado; não serve para Play Store (fora de escopo, R17.1).

### 24.3 Job de CI do APK (R17.2)

Acrescentado ao `release.yml` existente, como job independente dos de desktop (matriz Windows/Linux da seção 18):

1. `runs-on: ubuntu-latest` — Buildozer exige Linux.
2. Build dentro de container Docker (`kivy/buildozer` ou imagem própria) para ter Android SDK/NDK reprodutíveis, evitando instalar a toolchain no runner.
3. Cache de `~/.buildozer` e `.buildozer` via `actions/cache` — sem cache, o primeiro build baixa SDK+NDK e compila CPython+SDL2+pygame-ce, tipicamente 30–60 min.
4. `buildozer android debug` → APK em `bin/`.
5. Renomear para `BlockyBird-android-universal-<tag>.apk` (nome inclui plataforma e "universal" por conter múltiplas ABIs) e publicar **sem compressão** via `softprops/action-gh-release@v2` — o `.apk` já é um zip; comprimir de novo só atrapalharia a instalação direta (R17.2).

O job é independente para que uma falha no build Android (o passo mais frágil, ver risco em 24.1) não impeça a publicação dos binários de desktop.

> **Correção necessária ao item 3, descoberta na task 28 (build local, não no CI ainda).** O cache real do Android SDK/NDK do buildozer vive em `$HOME/.buildozer` **dentro do container** (`/home/user/.buildozer` na imagem `kivy/buildozer`), não em `.buildozer` do workspace — esse último só guarda os artefatos de build por recipe/arch. Rodar `docker run --rm -v "$WORKSPACE:/home/user/hostcwd" kivy/buildozer ...` sem também montar `/home/user/.buildozer` faz o SDK/NDK (~1-2 GB) serem baixados de novo em **todo** `docker run`, mesmo com `actions/cache` no caminho errado. Pior: o marcador "SDK já instalado" (`android:sdk_installation` em `state.db`, dentro de `.buildozer` do workspace, que É cacheado) fica dessincronizado do container efêmero — em builds subsequentes o buildozer acredita que os pacotes SDK (`platforms;android-34` etc.) já estão instalados e pula a etapa, resultando em `Available Android APIs are ()` e falha. Para o job de CI (task 29), isso significa: cachear/montar também um diretório persistente para `/home/user/.buildozer` do container (não só `.buildozer` do workspace), do mesmo jeito que a task 28 resolveu localmente com um segundo bind mount.

## 25. Limites de verificação nesta versão

Registrado explicitamente porque afeta como as tasks devem ser aceitas:

- **Não há aparelho Android nem emulador neste ambiente de desenvolvimento.** Logo, os itens que dependem de Android real — instalar o APK, jogar por toque, medir FPS em aparelho de entrada, confirmar persistência do recorde no storage do app — **precisam de validação manual pelo dono do projeto**.
- **Atualização (task 28): o Docker local, dado como inacessível na v1** (ao tentar validar o workflow com `act`), **ficou disponível neste ambiente** numa sessão posterior. Isso permitiu rodar o build real (`docker run kivy/buildozer android debug`) ponta a ponta até `BUILD SUCCESSFUL`, algo que a v1 não conseguia verificar — ver seção 24.1/24.2/24.3 para os bugs reais encontrados e corrigidos nesse processo. A disponibilidade do Docker pode variar entre sessões/ambientes; não assumir que builds futuros terão o mesmo acesso sem verificar (`docker ps`) primeiro.
- O que **pode** ser verificado automaticamente aqui: fonte bitmap (comparação de superfícies renderizadas), conversão de coordenadas de toque para espaço lógico (função pura, testável), resolução do diretório de save por plataforma (com `ANDROID_ARGUMENT` monkeypatched), transições de estado por ações `back`/`focus_lost` (eventos sintéticos), e o jogo inteiro no desktop com `SCALED` (incluindo redimensionamento de janela).
- O checklist manual em `tasks.md` marca claramente qual item é de qual categoria. Nenhum item dependente de hardware deve ser marcado como concluído sem teste real.

---

# Parte III — Qualidade (aumento de escopo da v2)

## 26. Conformidade com Ruff (R18)

**Config.** `[tool.ruff]` em `pyproject.toml`, sem arquivo `ruff.toml` separado (mantém o padrão de configuração centralizada já usado para `pytest`/dependências):

```toml
[tool.ruff]
line-length = 110
target-version = "py310"   # alinhado a requires-python (R9.2)

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "B", "SIM", "RUF"]
ignore = []

[tool.ruff.lint.isort]
known-first-party = ["src"]
```

- `line-length = 110`: a base de código atual tem linhas de até 122 caracteres (`pipes.py`); 110 é folgado o bastante para não forçar quebras artificiais em toda expressão de configuração/design (constantes de bioma, tuplas de cor), mas ainda mais apertado que o "sem limite" de fato — a auditoria inicial (task de conformidade) deve rever as poucas linhas acima de 110 caso a caso, não simplesmente subir o limite para acomodá-las.
- Conjunto de regras: `E`/`W` (pycodestyle), `F` (pyflakes — imports não usados, variáveis não usadas, o núcleo do lint), `I` (isort — ordenação de imports, já relevante porque `src/*.py` importa consistentemente com `from src import x`), `UP` (pyupgrade — sintaxe moderna compatível com o `requires-python = ">=3.10"` do projeto), `B` (bugbear — armadilhas comuns tipo mutable default argument, relevante aqui porque a v2 já documentou um bug real dessa categoria em `score.py`, seção 22), `SIM` (simplificações óbvias), `RUF` (regras específicas do próprio ruff). Não inclui `D` (docstrings) nem `ANN` (obrigatoriedade de type hints) — o projeto não usa docstrings de módulo/função de forma sistemática nem type hints em 100% das assinaturas, e exigir isso agora seria um escopo muito maior que "conformidade com ruff"; pode ser revisitado numa versão futura se o time decidir adotar esse padrão.
- Formatação: `uv run ruff format .` (equivalente a `black`, embutido no ruff — não precisa de dependência separada) aplicada uma vez no repositório inteiro como parte da task de conformidade; depois disso, `ruff format --check` no CI garante que não regride.

**Escopo da varredura.** Todo `.py` versionado: `main.py`, `src/**/*.py`, `tests/**/*.py`, `scripts/**/*.py`, `p4a-recipes/**/__init__.py`, `conftest.py`. As receitas em `p4a-recipes/` são código nosso (não vendored de terceiros — a v2 já as adaptou/corrigiu, seção 24.1), então entram na varredura como qualquer outro módulo do projeto.

**CI.** Não existe hoje um workflow que rode em push/PR (`release.yml` só dispara em publicação de Release) — esta extensão de escopo adiciona `.github/workflows/ci.yml`, `on: [push, pull_request]`, `runs-on: ubuntu-latest`, com `uv sync`, `uv run ruff check .`, `uv run ruff format --check .` e `SDL_VIDEODRIVER=dummy uv run pytest` como steps do mesmo job (falha rápida: lint antes dos testes). Isso é uma lacuna que esta extensão fecha incidentalmente — sem esse workflow, uma regressão de lint (ou de teste) só seria percebida manualmente ou na hora de cortar uma release.

**Correção de violações.** Regra do projeto (R18.6): consertar o código, não silenciar. Supressões (`# noqa: CODE`) só quando a regra genuinamente não se aplica ao caso (ex.: um `import` não usado propositalmente para efeito colateral), sempre com o código específico da regra (nunca `# noqa` nu) e um comentário de uma linha explicando o motivo.

## 27. Calibração de tamanho de fonte (R19)

**Problema real, não cosmético.** `ui._fit_scale()` (v2, seção 19) só protege contra estouro **horizontal** — reduz a escala até a largura do texto caber em `MAX_TEXT_W`. Não existe proteção equivalente na vertical: os deslocamentos entre linhas de uma mesma tela são deltas fixos em pixels, calculados à mão para os `base_size` originais (ex. `draw_ready_screen`: título em `SCREEN_H // 3`, créditos em `+ 28`, instrução em `+ 70`; `draw_game_over_screen`: `- 60`, `+ 0`, `+ 30`, `+ 70`). A altura real de uma linha renderizada é `pixelfont.GLYPH_H * scale` (7 × scale) mais a sombra (offset de 3 px) — se `scale` for maior do que o assumido quando esses deltas foram escolhidos, duas linhas vizinhas colidem. É exatamente o sintoma relatado: textos grandes demais se sobrepondo em várias telas.

**Abordagem.** Duas mudanças complementares em `ui.py`, sem tocar em `pixelfont.py`:

1. **Layout vertical por empilhamento, não por offset fixo.** Uma função `_stack(surface, center_x, top_y, lines)` que recebe uma lista de `(text, base_size, color)` na ordem em que aparecem na tela, calcula a escala de cada linha (via `_fit_scale`, já existente) e posiciona cada uma logo abaixo da anterior, com uma margem fixa pequena (ex. 8 px) entre linhas — a posição de uma linha passa a depender da altura real (`GLYPH_H * scale`) da linha anterior, não de uma constante escolhida a olho. Isso resolve o critério R19.3 de uma vez para as quatro telas, e é a mudança estrutural principal desta extensão de escopo.
2. **Revisão dos `base_size` por papel.** Com o empilhamento cuidando do espaçamento vertical, o que resta ajustar é o tamanho absoluto de cada papel de texto para a resolução lógica de 480×720. Os valores atuais (`title=18`, `HUD=20`) resultam em `scale = base_size // 2` → 9 e 10, ou seja glifos de 45–50 px de altura num canvas de 720 px — proporcionalmente grandes para uma tela que também precisa caber título + subtítulo + instrução + recorde sem se espremer. A task de implementação deve testar visualmente uma faixa reduzida (ex. título `scale` 5–6 em vez de 9, textos secundários `scale` 2–3) e registrar os valores finais escolhidos — o "tamanho ideal" pedido não é um número que dá para derivar analiticamente, é uma calibração visual como a task 12 (curva de dificuldade) já foi para gameplay.

**Verificação automatizada (R19.5).** Como toda a UI é desenhada em coordenadas lógicas fixas (480×720, independente do aparelho — a escala física fica inteiramente a cargo de `pygame.SCALED`, seção 20), a ausência de sobreposição é uma propriedade determinística do código, testável sem precisar de tela real:

```python
# tests/test_ui_layout.py (novo)
def _rects_for_screen(draw_fn, *args) -> list[pygame.Rect]:
    """Instrumenta draw_text para capturar os Rects em vez de (só) desenhar."""
    ...


def test_ready_screen_texts_do_not_overlap():
    rects = _rects_for_screen(ui.draw_ready_screen, highscore=999999)
    for a, b in itertools.combinations(rects, 2):
        assert not a.colliderect(b)
    for r in rects:
        assert 20 <= r.left and r.right <= SCREEN_W - 20
```

Repetido para as quatro telas (PRONTO, HUD+nada mais por enquanto — só um texto, mas fica como regressão —, PAUSADO, GAME_OVER), incluindo o caso de recorde com muitos dígitos (`RECORDE: 999999`) para não regredir se o score crescer além do testado até aqui. O ícone de mudo (`ui.MUTE_ICON_RECT`, constante) entra na mesma checagem de colisão nas telas onde é desenhado (celular, R15.4) — é um retângulo fixo, não precisa de instrumentação extra.

**Por que não mexer em `pixelfont.py`.** O glifo 5×7 em si não é o problema — é proporcional e legível; o que precisa de ajuste é *onde* e *em que escala* cada texto é colocado. Manter a mudança inteira em `ui.py` preserva o cache de `pixelfont.render` (v2, seção 19) e não arrisca reabrir a receita de build Android (a fonte já roda em produção real desde a task 28 da v2).

## 28. Conformidade com ty (R20)

**Por que ty, além de ruff.** `ruff` (seção 26) cobre estilo e armadilhas sintáticas, mas não checa se os tipos batem — e a v2 já teve um bug real dessa categoria escapar para produção (persistência do recorde, seção 23). `ty` é o checador de tipos estático do mesmo time do `ruff`/`uv` (Astral), então entra com a mesma filosofia de configuração centralizada em `pyproject.toml` e sem dependência extra de toolchain.

**Config.** `[tool.ty.environment]`/`[tool.ty.src]` em `pyproject.toml`, mesmo padrão de configuração centralizada usado para `ruff`:

```toml
[tool.ty.environment]
python-version = "3.10"          # alinhado a requires-python (R9.2), mesmo raciocinio do target-version do ruff

[tool.ty.src]
exclude = ["p4a-recipes", "specs", ".buildozer", "build", "dist"]
```

- `python-version = "3.10"`: alinhado ao `requires-python` do projeto, mesmo raciocínio do `target-version` do ruff (seção 26).
- `exclude`: `p4a-recipes/` sai do escopo porque essas receitas importam `sh` e `pythonforandroid.*` — pacotes que só existem dentro da imagem Docker do buildozer (R17, seção 24.1), nunca no `.venv` de desenvolvimento local; checá-las localmente só produziria `unresolved-import` permanente e não-acionável, diferente de `ruff` (que enxerga só sintaxe/estilo e não precisa resolver imports de verdade). `specs/`, `.buildozer/`, `build/`, `dist/` saem pelo mesmo motivo de `specs/` no ruff (não é código do jogo) mais artefatos de build que não são versionados.

**Escopo da varredura.** `main.py`, `src/**/*.py`, `tests/**/*.py`, `scripts/**/*.py`, `conftest.py` — o mesmo escopo do ruff (seção 26) menos `p4a-recipes/`.

**CI.** Novo step em `.github/workflows/ci.yml`, `uv run ty check .`, entre `ruff format --check` e `pytest` (mesma lógica de falha rápida: tipos antes de rodar a suíte).

**Supressões pontuais (R20.4).** Dois padrões legítimos não são erro de tipo de verdade, só uma limitação do que é estaticamente verificável, e usam `# ty: ignore[regra]` com comentário curto (mesma disciplina do `# noqa: CODE` do ruff, R18.6):

- `src/storage.py`: `from android.storage import app_storage_path` dentro do `try/except ImportError` (seção 23) — módulo só existe em runtime python-for-android, nunca no venv de dev. `# ty: ignore[unresolved-import]`.
- `tests/test_storage.py`: o fake do módulo `android.storage` (`test_save_dir_android_uses_app_storage_path`) atribui atributos dinamicamente a uma instância de `types.ModuleType` para simular o módulo injetado pelo p4a — válido em runtime (módulos aceitam atributo arbitrário), mas não declarado no stub de `ModuleType`. `# ty: ignore[unresolved-attribute]`.

**Violações reais encontradas na auditoria inicial (3, todas corrigidas no código — nenhuma suprimida):**

- `src/biome.py` (`_lerp_color`) e `src/particles.py` (`ParticleSystem.burst`): ambas construíam uma cor RGB a partir de uma expressão de tamanho variável (genexpr num caso, slice de `pygame.Color` no outro) e atribuíam a um `tuple[int, int, int]` — `ty` infere `tuple[int, ...]` para as duas formas, então o tamanho fixo nunca é garantido estaticamente (só por convenção do chamador). Corrigido desempacotando os três componentes em variáveis nomeadas e retornando/atribuindo um literal de tupla de 3 elementos, que `ty` já infere com o tamanho certo — sem mudar o comportamento em runtime.
- `src/input.py` (`InputManager`): `dict[int, pygame.joystick.Joystick]` usava `Joystick` como anotação de tipo, mas o próprio stub do pygame-ce documenta que `Joystick` é, na implementação atual, uma função-fábrica que devolve `JoystickType` (não uma classe) — "in the future, when the C implementation is fixed to add `__init__`/`__new__` to Joystick and it's exported directly, the typestubs here must be updated too". Corrigido usando `pygame.joystick.JoystickType`, o tipo de verdade da instância. Aproveitado para remover a chamada redundante `joystick.init()` logo após `Joystick(device_index)` (o stub marca `JoystickType.init` como `@deprecated("since 2.0.0. Multiple initializations are not supported anymore")` — a construção já inicializa o joystick).

**Suíte completa (70 testes) e `ruff check`/`ruff format --check` permanecem verdes após todas as correções.**

---

# Parte IV — Ícone do aplicativo (aumento de escopo da v2)

## 29. Ícone do app: geração por código e integração por plataforma (R21)

**Problema.** O jogo nunca definiu um ícone próprio. Na janela do desktop (`pygame.display.set_mode`, R9.1) o pygame usa seu ícone padrão; o executável PyInstaller (`BlockyBird.spec`, R13.1) não passava `icon=`, então o `.exe` herdava o ícone genérico do bootloader; o `buildozer.spec` (R17.1) não declarava `icon.filename` nem as chaves de ícone adaptativo, então o APK usava o ícone padrão do Android (o "robozinho" verde genérico do template do buildozer). Nada disso identificava o jogo visualmente antes de abri-lo.

**Princípio herdado (R7.1).** Como todo o resto da apresentação visual, o ícone é gerado por código, reaproveitando `textures.make_bee()` — nenhum arquivo de imagem externo entra no repositório manualmente. `scripts/generate_app_icon.py` segue o mesmo padrão já usado por outros scripts de geração de assets do projeto: um script standalone que importa `src/textures.py`/`src/pixelfont.py`, desenha em superfícies `pygame.Surface` e salva PNGs em `assets/`. A diferença desta task é que, além de PNG, o ícone do Windows precisa de um arquivo `.ico` multi-resolução.

### 29.1 `scripts/generate_app_icon.py`

Gera cinco arquivos em `assets/`, todos a partir da mesma abelha-fonte (`textures.make_bee(0)`, redesenhada em alta resolução por reamostragem `pygame.transform.scale` sem suavização — igual a `textures.py`, R7.1 exige pixel-art nítida, não um blur):

| Arquivo | Tamanho | Uso | Camada |
|---|---|---|---|
| `app_icon_512.png` | 512×512 | Ícone de janela do desktop (`pygame.display.set_icon`, R21.2) e fonte para o `.ico` | abelha + fundo (céu/grama), composto |
| `app_icon.ico` | 16/32/48/64/128/256 px, um único arquivo | Ícone do `.exe` no PyInstaller (`BlockyBird.spec`, R21.3) | mesma composição de `app_icon_512.png`, reamostrada por tamanho |
| `android_icon_legacy.png` | 512×512 | `icon.filename` do `buildozer.spec` — Android < 8.0/API 26 sem suporte a ícone adaptativo (R21.6) | abelha + fundo, com margem de ~10% (launchers antigos aplicam sua própria máscara/sombra por cima, sem zona segura formalizada) |
| `android_icon_foreground.png` | 432×432, fundo transparente | `icon.adaptive_foreground.filename` (R21.4) | só a abelha, escalada para caber nos 66 dp centrais de um canvas de 108 dp (≈61%, ou ≤264 px de lado dentro do canvas de 432 px) — a zona segura de máscara (R21.5) |
| `android_icon_background.png` | 432×432, opaco | `icon.adaptive_background.filename` (R21.4) | gradiente de céu liso (mesmas cores de `biome.py`, bioma Overworld), sem a abelha — camada de fundo do ícone adaptativo não precisa de zona segura, só não deve ter detalhe importante perto da borda |

```python
# scripts/generate_app_icon.py (esqueleto)
FOREGROUND_CANVAS = 432
SAFE_ZONE_FRACTION = 66 / 108   # zona segura do icone adaptativo Android (R21.5)

def make_foreground() -> pygame.Surface:
    surf = pygame.Surface((FOREGROUND_CANVAS, FOREGROUND_CANVAS), pygame.SRCALPHA)
    bee = textures.make_bee(0)
    max_side = int(FOREGROUND_CANVAS * SAFE_ZONE_FRACTION)
    bee = _scale_nearest_fit(bee, max_side)   # nearest-neighbor, preserva proporcao, cabe em max_side
    surf.blit(bee, bee.get_rect(center=(FOREGROUND_CANVAS // 2, FOREGROUND_CANVAS // 2)))
    return surf
```

- `_scale_nearest_fit`: mesma técnica de `textures.py` (escala inteira/vizinho-mais-próximo) aplicada ao maior lado da abelha até caber em `max_side`, mantendo a proporção original do sprite — evita esticar a abelha de forma desproporcional (o pedido original do dono do projeto, "proporções ajustadas").
- Composição do ícone com fundo (`app_icon_512.png`, `android_icon_legacy.png`): céu com o mesmo gradiente do Overworld (`biome.BIOMES[0].sky_top/sky_bottom`) e uma faixa de grama/terra na base (reaproveitando `textures.make_block("grass_side")`/`"dirt"`), com a abelha centralizada e ocupando a maior parte do quadro — visualmente consistente com a cena real do jogo.

### 29.2 Construção do `.ico` sem depender de Pillow

O projeto não tem `Pillow` como dependência (R9.2 restringe o runtime a `pygame-ce` + stdlib; scripts de geração de assets seguem a mesma disciplina para não introduzir uma dependência de build só para isto). O formato ICO moderno (desde o Windows Vista) aceita cada entrada como um PNG completo em vez de um bitmap `BITMAPINFOHEADER` cru — é o que torna viável montar o `.ico` só com `pygame.image.save` (gera os PNGs) e o módulo `struct` da stdlib (monta o container):

```python
import struct

ICO_SIZES = [16, 32, 48, 64, 128, 256]

def build_ico(source: pygame.Surface, out_path: Path) -> None:
    entries = []
    for size in ICO_SIZES:
        scaled = pygame.transform.smoothscale(source, (size, size))
        buf = io.BytesIO()
        pygame.image.save(scaled, buf, "app_icon.png")   # forca o encoder PNG do pygame via extensao
        png_bytes = buf.getvalue()
        entries.append((size, png_bytes))

    header = struct.pack("<HHH", 0, 1, len(entries))   # ICONDIR: reservado, tipo=1 (icone), contagem
    offset = len(header) + len(entries) * 16            # cada ICONDIRENTRY tem 16 bytes
    dir_entries = b""
    image_data = b""
    for size, png_bytes in entries:
        wh = 0 if size == 256 else size                 # 0 significa 256 no formato ICO
        dir_entries += struct.pack(
            "<BBBBHHII", wh, wh, 0, 0, 1, 32, len(png_bytes), offset
        )
        image_data += png_bytes
        offset += len(png_bytes)

    out_path.write_bytes(header + dir_entries + image_data)
```

- Diferente da composição do ícone em si (que usa escala nearest-neighbor para preservar o estilo pixel-art), o redimensionamento **para o `.ico`** usa `smoothscale`: em tamanhos pequenos (16/32 px) o nearest-neighbor de um sprite originalmente desenhado a 512 px produziria ruído ilegível — o mesmo trade-off que qualquer ícone de app enfrenta entre "pixel-art fiel" e "legível em 16 px". A composição de origem (`app_icon_512.png`) permanece nearest-neighbor/pixel-perfeita; só a redução de escala para os tamanhos pequenos do `.ico` usa suavização.
- Validação do `.ico` gerado: reabrir cada entrada com `pygame.image.load` a partir dos bytes extraídos (round-trip) e checar as dimensões — suficiente para garantir que o container está bem formado, sem precisar de uma lib externa de leitura de `.ico`.

### 29.3 Integração no desktop (R21.2, R21.3)

- **Ícone da janela** (`src/game.py`, `Game.__init__`): logo antes do `set_mode`, carrega `app_icon_512.png` via um novo helper `src/assets.py::asset_path()` e chama `pygame.display.set_icon(pygame.image.load(...))`. Envolvido em `contextlib.suppress(OSError, pygame.error)` que apenas segue sem ícone customizado — mesma disciplina de degradação graciosa já usada para áudio (R8.4, design seção 14): um ícone ausente/corrompido nunca deve impedir o jogo de abrir.
- **`src/assets.py::asset_path(filename)`**: resolve o caminho de um asset lido em runtime (hoje, só o ícone da janela — texturas/sons continuam 100% proceduais, sem arquivo), considerando onde o arquivo foi bundlado:

```python
def asset_path(filename: str) -> Path:
    if storage.is_frozen():
        # PyInstaller onefile extrai os dados empacotados (via `datas=` no .spec)
        # para sys._MEIPASS a cada execucao — ao contrario de storage.save_dir()
        # (secao 23), aqui o diretorio temporario e o lugar CERTO para ler um
        # asset builtin/somente-leitura, nao para gravar algo que precisa
        # sobreviver ao fechamento do processo.
        base = Path(getattr(sys, "_MEIPASS", "."))
    else:
        base = Path(__file__).resolve().parent.parent   # raiz do projeto (fonte ou apk do p4a)
    return base / "assets" / filename
```

  Distinção importante em relação a `storage.save_dir()` (seção 23): lá, `sys._MEIPASS` é explicitamente **evitado** porque é o diretório certo pra ler, mas errado pra persistir (é apagado ao fechar o processo) — o bug da task 33 foi justamente usar `__file__`/implicitamente `_MEIPASS` para decidir onde *gravar*. Aqui o caso é o oposto: o ícone é um recurso somente-leitura empacotado junto do executável, e `_MEIPASS` é exatamente onde o PyInstaller o extrai — usar `sys.executable.parent` aqui exigiria copiar o PNG manualmente para perto do `.exe` distribuído, o que o `datas=` do `.spec` já resolve sem esse passo manual.
- **`BlockyBird.spec`**: dois ajustes — `datas=[('assets/app_icon_512.png', 'assets')]` no `Analysis(...)` (para o ícone da janela funcionar também no executável empacotado, via `asset_path()` acima) e `icon='assets/app_icon.ico'` no `EXE(...)` (ícone do arquivo `.exe` em si, R21.3 — resolvido pelo PyInstaller em tempo de build, não em runtime, então não passa por `asset_path()`).
- No Android, `asset_path()` cai no branch `else` (nem frozen do PyInstaller nem nada especial) — `Path(__file__).resolve().parent.parent` resolve para a raiz do projeto tanto rodando de fonte quanto dentro do APK (o p4a preserva a árvore de arquivos Python do projeto, e `source.include_exts = py,png` no `buildozer.spec` já inclui os PNGs de `assets/` no pacote). Na prática, porém, o Android não usa `pygame.display.set_icon()` para nada visível — a Activity não tem barra de título, e o ícone mostrado nos apps recentes/launcher vem do manifesto (seção 29.4), não de uma chamada de runtime; a chamada simplesmente não tem efeito observável lá, sem precisar de nenhum `if is_android()` para pular.

### 29.4 Integração no Android — ícone adaptativo (R21.4, R21.5, R21.6)

```ini
# buildozer.spec, secao [app] — caminhos relativos, mesmo estilo ja usado no
# arquivo (android.extra_manifest_xml etc.); equivalentes a %(source.dir)s/...
# ja que source.dir = . neste projeto
icon.filename = assets/android_icon_legacy.png
icon.adaptive_foreground.filename = assets/android_icon_foreground.png
icon.adaptive_background.filename = assets/android_icon_background.png
```

- `icon.filename` sozinho já cobriria todos os aparelhos (API < 26 usa direto; API ≥ 26 sem as chaves adaptativas aplicaria sua própria máscara circular default sobre esse PNG quadrado, geralmente cortando as bordas) — as duas chaves `icon.adaptive_*` são o que efetivamente resolve o pedido do dono do projeto ("proporções ajustadas"): o buildozer/p4a gera os recursos `mipmap-anydpi-v26/icon.xml` (`<adaptive-icon>`, referenciando as duas camadas) exigidos pelo Android 8.0+, deixando o **sistema** compor a máscara final a partir de uma abelha que já foi desenhada sabendo que só o círculo central de ~66% será garantidamente visível — em vez de o buildozer aplicar uma máscara genérica sobre uma imagem que não foi pensada para isso.
- Sem essas chaves (comportamento antes desta task), o Android 8+ usaria o ícone quadrado como se fosse já a camada de primeiro plano inteira — a máscara circular padrão corta as pontas de qualquer conteúdo que não esteja já contido num círculo central, o que na prática cortaria as antenas/asas da abelha se ela ocupasse o quadro inteiro. É esse recorte que o dono do projeto estava descrevendo como o ícone "sem as proporções ajustadas".
- `icon.filename` (legado) usa a composição com fundo (abelha + céu/grama), já que aparelhos API < 26 não aplicam máscara de sistema — o ícone aparece como o PNG entrega, então precisa parecer "terminado" por si só (mesmo raciocínio do ícone de janela do desktop, seção 29.3).

**Verificado com build real (não apenas estático).** Docker estava acessível neste ambiente (imagem `kivy/buildozer` já em cache local, mesma condição documentada na seção 25) e o build real (`buildozer android debug`) foi executado ponta a ponta, reaproveitando o cache de SDK/NDK persistido de sessões anteriores — `BUILD SUCCESSFUL in 1m 36s`. O comando `p4a` invocado pelo buildozer (visível no log) confirma a tradução das três chaves do spec para as flags reais do python-for-android: `--icon .../android_icon_legacy.png --icon-fg .../android_icon_foreground.png --icon-bg .../android_icon_background.png`. Além disso, o `.apk` gerado foi extraído (é um zip) e inspecionado diretamente: `res/mipmap-anydpi-v26/icon.xml` existe e contém as strings `adaptive-icon`/`background`/`foreground` (XML binário compilado pelo aapt, confirmando um `<adaptive-icon>` de verdade); `res/mipmap/icon_foreground.png` (432×432, RGBA) e `res/mipmap/icon_background.png` (432×432, RGB sem alfa) batem em dimensão **e em tamanho de arquivo em bytes** com os PNGs gerados por `scripts/generate_app_icon.py` — prova de que são exatamente os arquivos gerados, não um fallback ou o ícone padrão do template. O que **não** foi possível verificar neste ambiente (mesma limitação da seção 25): a composição final da máscara pelo launcher (círculo/squircle/quadrado arredondado) só é visível de fato num aparelho ou emulador Android real — o que foi confirmado é que os recursos corretos, nos tamanhos certos, com/sem alfa conforme esperado, chegam ao APK.

### 29.5 Testes

- `tests/test_generate_app_icon.py`: chama as funções puras do script (composição do foreground, cálculo de `max_side` pela zona segura, `build_ico`) sem depender de rodar o script inteiro como processo. Casos: a abelha do foreground cabe em `SAFE_ZONE_FRACTION * FOREGROUND_CANVAS` em ambos os eixos; o `.ico` gerado tem as 6 entradas esperadas e cada uma decodifica de volta para as dimensões corretas via `pygame.image.load`; `android_icon_background.png` não tem pixels com alfa parcial (é uma camada opaca de verdade, já que o Android a trata como fundo sólido).
- `tests/test_assets.py`: `asset_path()` nos dois ramos (`storage.is_frozen()` verdadeiro/falso via monkeypatch, mesmo padrão já usado para `storage.save_dir()` em `tests/test_storage.py`, seção 23).
- Smoke test manual (`uv run main.py` e o `.exe` gerado por PyInstaller): ambos abrem sem exceção; `pyinstaller` confirma "Copying icon to EXE" no log de build.
