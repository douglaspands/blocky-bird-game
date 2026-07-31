# Blocky Bird — Specs v2

**Status:** concluída.

## Descrição

Torna o Blocky Bird jogável em **Android** — celular/tablet por toque, sempre em
**retrato** — no maior número possível de aparelhos (Android 5.0+, ABIs ARM 32/64 e
x86_64), distribuído como **APK instalável diretamente**, publicado sem compressão nos
assets de cada Release do GitHub. O suporte a desktop da v1 é mantido: cada release
continua gerando os binários de Windows e Linux, agora acompanhados do APK.

O mesmo código-fonte atende as duas plataformas. Todo o jogo continua escrito contra uma
resolução lógica fixa de 480×720 — a diferença de tela é resolvida por `pygame.SCALED`,
que escala a imagem para caber inteira na tela real, sobrando barra (letterbox) no eixo
que não bate, sem nunca cortar a imagem; com a orientação sempre travada em retrato
(`buildozer.spec`), essa barra sobra sempre no topo/base, nunca nas laterais. As
diferenças de plataforma ficam isoladas em três pontos (escala/SCALED, input e
armazenamento), sem que nenhum módulo de gameplay saiba onde está rodando. Isso preserva
a calibração de dificuldade feita na v1.

Além da entrega Android, a v2 recebeu três aumentos de escopo que não mudam o gameplay:
(1) **conformidade com Ruff** — todo o código Python do projeto passa a ser verificado por
lint + formatação, checado em CI (`ci.yml`); (2) **conformidade com ty** — checagem
estática de tipos, também em CI; (3) **tamanho de fonte sem sobreposição** — a fonte
bitmap própria (`pixelfont.py`, R7.6) recebeu empilhamento vertical por altura real de
linha (`ui._stack()`) no lugar de deltas fixos em pixels, e o tamanho de cada papel de
texto foi recalibrado até nenhuma tela sobrepor texto, com teste automatizado por tela.

Por fim, o dono do projeto pediu um **ícone do aplicativo** com a personagem do jogo (a
abelha voxel) em vez do ícone genérico do framework — nem a janela/executável do desktop
nem o APK Android tinham um. `scripts/generate_app_icon.py` gera o ícone por código; no
desktop ele aparece na janela/taskbar e no `.exe` do PyInstaller; no Android ele usa o
formato de **ícone adaptativo** (Android 8.0+, camadas de primeiro plano e de fundo
separadas), para que a abelha não fique cortada pelas diferentes máscaras de ícone dos
fabricantes — mais um ícone legado para aparelhos mais antigos. Validado com um build real
do APK: o `.apk` gerado contém de fato um `<adaptive-icon>` com as camadas certas (design
seção 29).

## Conteúdo desta pasta

- [`requirements.md`](requirements.md) — requisitos R1–R21 em formato EARS (R14–R17 são da entrega Android; R18–R20 são do aumento de escopo de qualidade; R21 é o ícone do aplicativo).
- [`design.md`](design.md) — arquitetura técnica. Parte I (seções 1–18) é o jogo base herdado da v1 com os ajustes que o Android exigiu; Parte II (seções 19–25) é o trabalho de Android; Parte III (seções 26–28) é o aumento de escopo de qualidade; Parte IV (seção 29) é o ícone do aplicativo.
- [`tasks.md`](tasks.md) — plano incremental. Tasks 1–19 são o histórico concluído da v1; tasks 20–30 são o trabalho de Android; **tasks 31–41 são aumentos de escopo posteriores** (qualidade, o ícone do aplicativo e o ajuste final de tela cheia/orientação no Android).

## O que muda em relação à v1

Três coisas da v1 **quebram** no Android e são corrigidas aqui:

| Problema na v1 | Correção na v2 |
|---|---|
| `SysFont("couriernew")` — fonte inexistente no Android | Fonte bitmap gerada por código (`pixelfont.py`) |
| `highscore.json` gravado a partir do diretório de trabalho, não gravável no Android | `storage.py` resolve o diretório privado do app por plataforma |
| Resolução fixa 480×720, letterbox explicitamente fora de escopo | Resolução lógica continua fixa em 480×720 (calibração de dificuldade intocada); o app roda sempre em retrato no Android e `pygame.SCALED` aplica letterbox automático sem cortar a imagem — a barra sobra sempre no topo/base, nunca nas laterais |

Além disso: entrada por toque, pausa automática ao ir para segundo plano, gravação
incremental do recorde (sobrevive a encerramento pelo sistema), migração de `pygame`
para `pygame-ce` (compatível a nível de API, exigida pela cadeia de build Android), e
mapeamentos adicionais de teclado (Enter para voar, setas para mudo em PAUSADO).

## Riscos e limites conhecidos

- **Maior risco:** a receita de `pygame-ce` para o python-for-android não está mergeada upstream (PR aberto desde 2024), então o projeto mantém uma receita local. Detalhado no design, seção 24.1.
- **Verificação:** não há aparelho Android nem Docker acessível no ambiente de desenvolvimento, então os itens dependentes de hardware exigem teste manual. O checklist de `tasks.md` separa explicitamente o que é automatizável do que precisa de celular real. Ver design, seção 25.
- Publicação na Play Store e assinatura com keystore próprio ficam fora de escopo — o APK é debug-signed, para instalação direta.
- A calibração de tamanho de fonte (task 32) é uma decisão visual, não puramente analítica — os valores finais de escala por papel de texto foram escolhidos por inspeção durante a implementação, com o teste automatizado garantindo a propriedade objetiva (não sobrepor) depois de escolhidos.

## Sobre esta versão

Esta pasta é um retrato **completo e autocontido** dos specs da v2 — cobre o jogo inteiro,
não só as mudanças desta versão. A v1 permanece intacta em [`specs/v1/`](../v1/) como
histórico. Veja [`specs/README.md`](../README.md) para o padrão de versionamento.
