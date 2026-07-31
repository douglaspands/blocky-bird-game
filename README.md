# Blocky Bee

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
uv run pyinstaller BlockyBee.spec
```

O executável fica em `dist/BlockyBee.exe` (Windows) ou `dist/BlockyBee` (Linux/macOS).
`BlockyBee.spec` já está configurado (onefile, sem console) — não é necessário passar
flags extras.

### Releases automatizadas (GitHub Actions)

Ao publicar uma Release no GitHub (com uma tag de versão, ex. `v1.0.0`), o workflow
[`.github/workflows/release.yml`](.github/workflows/release.yml) builda o executável
para Windows e Linux automaticamente e anexa aos assets da release:

- `BlockyBee-windows-x64-<tag>.zip`
- `BlockyBee-linux-x64-<tag>.tar.bz2`
- `BlockyBee-android-universal-<tag>.apk` (Android — celular/tablet, sempre em retrato, ver abaixo)

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
