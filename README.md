# Blocky Bird

Flappy Bird com temática Minecraft, feito em Python/Pygame. Todos os gráficos e sons
são gerados por código — sem assets externos.

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

## Testes

```bash
SDL_VIDEODRIVER=dummy uv run pytest
```

`SDL_VIDEODRIVER=dummy` roda o Pygame sem abrir uma janela real, útil em CI e
ambientes sem display.

## Estrutura

```
main.py           # Entry point
src/
├── config.py      # Constantes (tela, fisica, gameplay)
├── game.py        # Loop principal e maquina de estados
├── bird.py        # Fisica e animacao do passaro
├── pipes.py       # Colunas/obstaculos
├── ground.py      # Chao rolante
├── biome.py       # Overworld / Cave / Nether
├── decor.py       # Parallax de fundo
├── score.py       # Pontuacao e recorde (highscore.json)
├── particles.py   # Particulas de bloco quebrando
├── textures.py    # Texturas voxel proceduais
├── sounds.py      # Audio sintetizado 8-bit
├── input.py       # Teclado, mouse e controle Xbox
└── ui.py          # HUD e telas (pronto/pausa/game over)
specs/             # Documentos de requisitos, design e plano
tests/             # Testes unitarios (pytest)
```
