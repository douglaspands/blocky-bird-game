# Blocky Bird — Specs v2

**Status:** concluída. **Especificada em:** 2026-07-29. **Aumento de escopo (qualidade) especificado e concluído em:** 2026-07-30. **Correção pós-lançamento (preenchimento de tela, task 35) em:** 2026-07-30. **Ícone do aplicativo (tasks 36–37) especificado e concluído em:** 2026-07-30. **Resolução fixa de volta, pillarbox por zoom/corte (task 40) em:** 2026-07-30. **Orientação retrato travada, suporte a Android TV removido, pillarbox eliminado por letterbox (task 41) em:** 2026-07-30.

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
(`buildozer.spec`, task 41), essa barra sobra sempre no topo/base, nunca nas laterais, na
prática eliminando o pillarbox relatado pelo dono do projeto. As diferenças de plataforma
ficam isoladas em três pontos (escala/SCALED, input e armazenamento), sem que nenhum
módulo de gameplay saiba onde está rodando. Isso preserva a calibração de dificuldade
feita na v1.

Depois da entrega Android, a v2 recebeu um aumento de escopo com dois itens de qualidade
que não mudam o gameplay: (1) **conformidade com Ruff** — todo o código Python do projeto
passa a ser verificado por lint + formatação, checado em CI (`ci.yml`, novo — a entrega
Android só tinha CI de release); (2) **tamanho de fonte sem sobreposição** — a fonte bitmap
própria (`pixelfont.py`, R7.6) protegia só contra estouro horizontal; os deltas fixos em
pixels entre linhas foram trocados por empilhamento (`ui._stack()`) baseado na altura real
da linha, e o tamanho de cada papel de texto foi recalibrado até nenhuma tela sobrepor
texto, com teste automatizado por tela.

Depois disso, um bug real reportado no Galaxy S20 FE (faixa preta nas laterais em vez da
tela preenchida) motivou a task 35: o canvas real passou a se adaptar em runtime à
proporção do aparelho, preenchendo com céu/parallax estendidos o que antes era barra
preta (design seção 20.1.1). A task 38 restringiu essa extensão de fundo só à paisagem, e
a task 39 foi além, tornando a própria área jogável dinâmica em retrato — mas o dono do
projeto pediu a reversão dessa direção (task 40): a resolução lógica volta a ser sempre
fixa em 480×720, e o pillarbox foi eliminado dando zoom na imagem renderizada até cobrir a
tela real por completo, cortando o excedente em vez de mudar a resolução.

O ícone do aplicativo (tasks 36–37, ver abaixo) veio nesse meio-tempo. Por fim, o dono do
projeto pediu mais uma correção (task 41): o app deve rodar **sempre em retrato** no
Android, como sempre foi no desktop — nunca em paisagem. Isso tornou o suporte a Android
TV (paisagem por hardware, tasks 27/29/30) inviável, removido nesta task. Com a orientação
travada, o pillarbox deixou de precisar de zoom/corte: `pygame.SCALED` (o mecanismo
original da task 21) já garante que a barra que sobrar seja sempre letterbox (topo/base),
nunca pillarbox (laterais) — `src/scale.py` passou a calcular esse letterbox (`fit_scale`,
substituindo `cover_scale`), e a imagem nunca é cortada (design seção 20.1.5).

Mais recentemente, o dono do projeto pediu um **ícone do aplicativo** com a personagem do
jogo (a abelha voxel) em vez do ícone genérico do framework — nem a janela/executável do
desktop nem o APK Android tinham um. `scripts/generate_app_icon.py` gera o ícone por
código; no desktop ele aparece na janela/taskbar e no `.exe` do PyInstaller; no Android ele
usa o formato de **ícone adaptativo** (Android 8.0+, camadas de primeiro plano e de fundo
separadas), para que a abelha não fique cortada pelas diferentes máscaras de ícone dos
fabricantes — mais um ícone legado para aparelhos mais antigos. Validado com um build real
do APK: o `.apk` gerado contém de fato um `<adaptive-icon>` com as camadas certas (design
seção 29).

## Conteúdo desta pasta

- [`requirements.md`](requirements.md) — requisitos R1–R21 em formato EARS (R14–R17 são da entrega Android; R18–R20 são do aumento de escopo de qualidade; R21 é o ícone do aplicativo).
- [`design.md`](design.md) — arquitetura técnica. Parte I (seções 1–18) é o jogo base herdado da v1 com os ajustes que o Android exigiu; Parte II (seções 19–25) é o trabalho de Android; Parte III (seções 26–28) é o aumento de escopo de qualidade; Parte IV (seção 29) é o ícone do aplicativo.
- [`tasks.md`](tasks.md) — plano incremental. Tasks 1–19 são o histórico concluído da v1; tasks 20–30 são o trabalho de Android; **tasks 31–41 são aumentos de escopo posteriores** (qualidade, correções pós-lançamento, o ícone do aplicativo, os ajustes de resolução/pillarbox e, por fim, a remoção do suporte a Android TV).

## O que muda em relação à v1

Três coisas da v1 **quebram** no Android e são corrigidas aqui:

| Problema na v1 | Correção na v2 |
|---|---|
| `SysFont("couriernew")` — fonte inexistente no Android | Fonte bitmap gerada por código (`pixelfont.py`) |
| `highscore.json` gravado a partir do diretório de trabalho, não gravável no Android | `storage.py` resolve o diretório privado do app por plataforma |
| Resolução fixa 480×720, letterbox explicitamente fora de escopo | Resolução lógica continua fixa em 480×720 (calibração de dificuldade intocada); o app roda sempre em retrato no Android (task 41) e `pygame.SCALED` aplica letterbox automático sem cortar a imagem — depois de passar por quatro tentativas anteriores: extensão de fundo na task 35, restrita à paisagem pela task 38, área jogável dinâmica em retrato pela task 39, e zoom/corte sobre resolução fixa pela task 40 |

Além disso: entrada por toque, pausa automática ao ir para segundo plano, gravação
incremental do recorde (sobrevive a encerramento pelo sistema), e migração de `pygame`
para `pygame-ce` (compatível a nível de API, exigida pela cadeia de build Android). Os
mapeamentos de teclado adicionados para Android TV (`K_RETURN`/`K_KP_ENTER` para voar,
D-pad ←/→ para mudo em PAUSADO) continuam no código — são inofensivos em qualquer
plataforma, inclusive desktop — mesmo com o suporte a TV como alvo de distribuição
removido na task 41.

## Riscos e limites conhecidos

- **Maior risco:** a receita de `pygame-ce` para o python-for-android não está mergeada upstream (PR aberto desde 2024), então o projeto mantém uma receita local. Detalhado no design, seção 24.1.
- **Verificação:** não há aparelho Android nem Docker acessível no ambiente de desenvolvimento, então os itens dependentes de hardware exigem teste manual. O checklist de `tasks.md` separa explicitamente o que é automatizável do que precisa de celular real. Ver design, seção 25.
- Publicação na Play Store e assinatura com keystore próprio ficam fora de escopo — o APK é debug-signed, para instalação direta.
- A calibração de tamanho de fonte (task 32) é uma decisão visual, não puramente analítica — os valores finais de escala por papel de texto foram escolhidos por inspeção durante a implementação, com o teste automatizado garantindo a propriedade objetiva (não sobrepor) depois de escolhidos.

## Sobre esta versão

Esta pasta é um retrato **completo e autocontido** dos specs da v2 — cobre o jogo inteiro,
não só as mudanças desta versão. A v1 permanece intacta em [`specs/v1/`](../v1/) como
histórico. Veja [`specs/README.md`](../README.md) para o padrão de versionamento.
