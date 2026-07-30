# Blocky Bird — Specs v2

**Status:** especificação concluída, implementação pendente. **Especificada em:** 2026-07-29.

## Descrição

Torna o Blocky Bird jogável em **Android** — celular/tablet por toque e **Android TV**
por controle remoto — no maior número possível de aparelhos (Android 5.0+, ABIs ARM 32/64
e x86_64), distribuído como **APK instalável diretamente**, publicado sem compressão nos
assets de cada Release do GitHub. O suporte a desktop da v1 é mantido: cada release
continua gerando os binários de Windows e Linux, agora acompanhados do APK.

O mesmo código-fonte atende as duas plataformas. Todo o jogo continua escrito contra uma
resolução lógica fixa de 480×720 — a diferença de tela é resolvida por escala com
letterbox, e as diferenças de plataforma ficam isoladas em três pontos (escala, input e
armazenamento), sem que nenhum módulo de gameplay saiba onde está rodando. Isso preserva
a calibração de dificuldade feita na v1.

## Conteúdo desta pasta

- [`requirements.md`](requirements.md) — requisitos R1–R17 em formato EARS (R14–R17 são novos da v2).
- [`design.md`](design.md) — arquitetura técnica. Parte I (seções 1–18) é o jogo base herdado da v1 com os ajustes que o Android exigiu; Parte II (seções 19–25) é o novo trabalho de Android.
- [`tasks.md`](tasks.md) — plano incremental. Tasks 1–19 são o histórico concluído da v1; **tasks 20–30 são o trabalho da v2**.

## O que muda em relação à v1

Três coisas da v1 **quebram** no Android e são corrigidas aqui:

| Problema na v1 | Correção na v2 |
|---|---|
| `SysFont("couriernew")` — fonte inexistente no Android | Fonte bitmap gerada por código (`pixelfont.py`) |
| `highscore.json` gravado a partir do diretório de trabalho, não gravável no Android | `storage.py` resolve o diretório privado do app por plataforma |
| Resolução fixa 480×720, letterbox explicitamente fora de escopo | `pygame.SCALED`, escala proporcional com letterbox/pillarbox |

Além disso: entrada por toque e por controle remoto de TV, pausa automática ao ir para
segundo plano, gravação incremental do recorde (sobrevive a encerramento pelo sistema),
e migração de `pygame` para `pygame-ce` (compatível a nível de API, exigida pela cadeia
de build Android).

## Riscos e limites conhecidos

- **Maior risco:** a receita de `pygame-ce` para o python-for-android não está mergeada upstream (PR aberto desde 2024), então o projeto mantém uma receita local. Detalhado no design, seção 24.1.
- **Verificação:** não há aparelho Android nem Docker acessível no ambiente de desenvolvimento, então os itens dependentes de hardware exigem teste manual. O checklist de `tasks.md` separa explicitamente o que é automatizável do que precisa de celular ou TV real. Ver design, seção 25.
- Publicação na Play Store e assinatura com keystore próprio ficam fora de escopo — o APK é debug-signed, para instalação direta.

## Sobre esta versão

Esta pasta é um retrato **completo e autocontido** dos specs da v2 — cobre o jogo inteiro,
não só as mudanças desta versão. A v1 permanece intacta em [`specs/v1/`](../v1/) como
histórico. Veja [`specs/README.md`](../README.md) para o padrão de versionamento.
