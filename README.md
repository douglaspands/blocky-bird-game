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

## Gerar executável

Para distribuir um binário que roda com duplo clique, sem precisar instalar Python:

```bash
uv sync
uv run pyinstaller BlockyBird.spec
```

O executável fica em `dist/BlockyBird.exe` (Windows) ou `dist/BlockyBird` (Linux/macOS).
`BlockyBird.spec` já está configurado (onefile, sem console) — não é necessário passar
flags extras.

### Releases automatizadas (GitHub Actions)

Ao publicar uma Release no GitHub (com uma tag de versão, ex. `v1.0.0`), o workflow
[`.github/workflows/release.yml`](.github/workflows/release.yml) builda o executável
para Windows e Linux automaticamente e anexa aos assets da release:

- `BlockyBird-windows-x64-<tag>.zip`
- `BlockyBird-linux-x64-<tag>.tar.bz2`
- `BlockyBird-android-universal-<tag>.apk` (Android — celular e Android TV, ver abaixo)

## Instalar no Android (celular ou TV)

1. Baixe `BlockyBird-android-universal-<tag>.apk` dos assets da Release desejada.
2. No aparelho, abra o arquivo baixado e permita a instalação de "fontes
   desconhecidas" quando solicitado (o app não vem de uma loja, então o Android
   pede essa confirmação uma vez por origem).
3. Toque no ícone "Blocky Bird" para abrir. Em Android TV, o app aparece na home
   com o próprio banner do jogo.

Controles no celular: toque em qualquer ponto da tela para voar/reiniciar; o
ícone de mudo no canto silencia o áudio; o botão BACK do sistema pausa durante o
jogo e fecha o app nas outras telas. Em Android TV, o jogo é 100% operável pelo
controle remoto: OK/Enter para voar, D-pad ←/→ para mudo na tela de pausa, e
BACK com o mesmo comportamento do celular — não é necessário toque nem teclado.

Requisitos: Android 5.0 (API 21) ou superior.

### Build local do APK (Docker + Buildozer)

Reproduz o mesmo processo do CI, útil para testar mudanças na cadeia Android
sem depender de uma Release:

```bash
docker run --rm -v "$(pwd)":/home/user/hostcwd -v "$HOME/.buildozer":/home/user/.buildozer kivy/buildozer android debug
```

No Windows, usando o PowerShell (sem Git Bash/WSL):

```powershell
docker run --rm -v "${PWD}:/home/user/hostcwd" -v "${HOME}/.buildozer:/home/user/.buildozer" kivy/buildozer android debug
```

O APK gerado fica em `bin/*.apk`. Ver `buildozer.spec` e `specs/v2/design.md`
(seção 24) para detalhes da configuração e das receitas locais necessárias.

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
specs/             # Documentos de requisitos, design e plano (versionados em specs/vN/)
tests/             # Testes unitarios (pytest)
```
