# Blocky Bird — Specs v1

**Status:** concluída. **Concluída em:** 2026-07-29.

## Descrição

Primeira implementação completa do Blocky Bird: um clone de Flappy Bird em
Python/Pygame com temática Minecraft, jogado com uma abelha voxel que voa entre
colunas de blocos ao longo de três biomas com dificuldade crescente (Overworld →
Cave → Nether). Todos os gráficos e sons são gerados por código (sem assets
externos), com pontuação, recorde persistente, partículas de bloco quebrando,
suporte a teclado/mouse/controle de Xbox, e distribuição como executável
standalone para Windows e Linux (com build automatizado via GitHub Actions em
cada Release).

## Conteúdo desta pasta

- [`requirements.md`](requirements.md) — requisitos R1–R13 em formato EARS.
- [`design.md`](design.md) — arquitetura técnica, módulos e decisões de implementação.
- [`tasks.md`](tasks.md) — plano de implementação incremental (tasks 1–13) mais as
  tarefas adicionais pedidas via chat após a conclusão do plano original
  (tasks 14–19), e o checklist de verificação manual.

## Sobre esta versão

Esta pasta é um retrato **completo e autocontido** dos specs no momento em que a
v1 foi concluída — cobre o jogo inteiro, não só as mudanças desta versão (não há
v0 anterior).

Ao pedir uma nova funcionalidade depois desta versão, uma pasta `specs/v2/` (e
assim por diante) é criada com `requirements.md`, `design.md` e `tasks.md`
igualmente completos, já incorporando tudo desta versão mais a novidade — sem
alterar o conteúdo desta pasta. Veja [`specs/README.md`](../README.md) para o
padrão completo.
