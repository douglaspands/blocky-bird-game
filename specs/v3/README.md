# Blocky Bird — Specs v3

**Status:** concluída (tasks 36–37). **Especificada em:** 2026-07-30. **Validação final pendente:** instalação e checagem visual num aparelho Android real.

## Descrição

Adiciona um **ícone do aplicativo** com a personagem do jogo — a abelha voxel (R7.2) —
em todas as plataformas já suportadas pela v2: janela e executável do desktop
(Windows/Linux, PyInstaller) e ícone do launcher no APK Android. Antes desta versão o
jogo não tinha ícone próprio em lugar nenhum: a janela e o `.exe` usavam o ícone padrão
do pygame/PyInstaller, e o APK usava o ícone genérico do template do buildozer.

Como todo o resto da apresentação visual do jogo (R7.1), o ícone é **gerado por código**
— `scripts/generate_app_icon.py` reaproveita `textures.make_bee()`, no mesmo padrão já
usado por `scripts/generate_tv_banner.py` (v2). Nenhuma imagem externa entra no
repositório manualmente.

No Android, o pedido específico do dono do projeto era que o ícone aparecesse "com as
proporções ajustadas" ao tocar/abrir o app — ou seja, sem a personagem cortada pelas
diferentes máscaras de ícone que cada fabricante aplica (círculo, "squircle", quadrado
arredondado etc.). Isso é resolvido com o formato de **ícone adaptativo** do Android 8.0+
(camadas de primeiro plano e de fundo separadas, com a abelha desenhada para caber
inteira na zona segura de 66/108 dp que qualquer máscara do sistema preserva), mais um
ícone legado equivalente para aparelhos mais antigos (API < 26, sem suporte a ícone
adaptativo).

## Conteúdo desta pasta

- [`requirements.md`](requirements.md) — requisitos R1–R21 em formato EARS (R21 é novo desta versão).
- [`design.md`](design.md) — arquitetura técnica. Partes I–III (seções 1–28) são herdadas da v2 sem mudança de comportamento; a **Parte IV (seção 29)** é inteiramente nova, cobrindo geração e integração do ícone.
- [`tasks.md`](tasks.md) — plano incremental. Tasks 1–35 são o histórico já concluído (v1, Android da v2, e os aumentos de escopo de qualidade da v2); **tasks 36–37 são o trabalho desta versão**.

## O que muda em relação à v2

| Antes (v2) | Depois (v3) |
|---|---|
| Janela do desktop usa o ícone padrão do pygame | Ícone da abelha via `pygame.display.set_icon()` (`src/game.py` + `src/assets.py`) |
| `BlockyBird.spec` não define `icon=` — `.exe` usa o ícone genérico do PyInstaller | `icon='assets/app_icon.ico'`, gerado sem depender de Pillow (container `.ico` montado via stdlib `struct`) |
| `buildozer.spec` não define nenhuma chave de ícone — APK usa o ícone padrão do template | `icon.filename` (legado) + `icon.adaptive_foreground.filename`/`icon.adaptive_background.filename` (Android 8.0+), evitando que a máscara do launcher corte a abelha |

## Riscos e limites conhecidos

- Docker estava acessível nesta sessão de desenvolvimento (cache de SDK/NDK de ~2.6 GB já persistido de uma sessão anterior da v2), então o build real do APK foi executado ponta a ponta: `BUILD SUCCESSFUL in 1m 36s`, e o `.apk` gerado foi inspecionado diretamente (é um zip) — confirmado `res/mipmap-anydpi-v26/icon.xml` como `<adaptive-icon>` de verdade, com `icon_foreground.png`/`icon_background.png` batendo em dimensão e tamanho de arquivo com os PNGs gerados por `scripts/generate_app_icon.py`. Mesma limitação das versões anteriores (design, seção 25): a composição final da máscara pelo launcher (círculo/squircle/quadrado) só é visível de fato num aparelho ou emulador Android real — o que foi verificado aqui é que os recursos corretos chegam ao APK, não a renderização final na tela.
- A construção do `.ico` sem Pillow (só `pygame` + stdlib `struct`) mantém a restrição de dependências já em vigor (R9.2) — é uma técnica menos comum que merece atenção se o formato do PNG gerado pelo pygame mudar em versões futuras do `pygame-ce`.

## Sobre esta versão

Esta pasta é um retrato **completo e autocontido** dos specs da v3 — cobre o jogo
inteiro, não só as mudanças desta versão. As versões anteriores permanecem intactas em
[`specs/v1/`](../v1/) e [`specs/v2/`](../v2/) como histórico. Veja
[`specs/README.md`](../README.md) para o padrão de versionamento.
