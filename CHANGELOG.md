# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/), com
versionamento [SemVer](https://semver.org/) (tags `vMAJOR.MINOR.PATCH`, ver
[`CONTRIBUTING.md`](CONTRIBUTING.md)).

> **Este arquivo passa a valer a partir daqui.** As tags anteriores a esta mudança
> (`v0.0.1`–`v1.2.0`) não mapeiam 1:1 para as pastas `specs/vN/` — `v1.2.0`, por
> exemplo, está no commit do *merge* de `release/v2` para `main`, versionada como
> incremento menor da v1 mas contendo o trabalho inteiro da v2. Reconstruir entradas
> retroativas detalhadas inventaria uma narrativa "por versão de spec" que as tags de
> fato não sustentam (ver `specs/v3/design.md`, seção 44). O histórico de cada versão
> encerrada já está descrito em [`specs/v1/README.md`](specs/v1/README.md) e
> [`specs/v2/README.md`](specs/v2/README.md), e os binários de cada tag nas
> [Releases do GitHub](https://github.com/douglaspands/blocky-bird-game/releases) — este
> documento não duplica isso.

## [Não lançado] — v3

Ver [`specs/v3/README.md`](specs/v3/README.md) para a descrição completa. Resumo:

### Added

- Jogo renomeado para **Blocky Bee**.
- Tela cheia em qualquer proporção, com canvas lógico e faixas decorativas temáticas
  (céu, subsolo, mobs), sem alterar a área jogável nem a dificuldade.
- Renderização acelerada por GPU por padrão, com cascata de compatibilidade e todo
  conteúdo estático pré-renderizado.
- Timestep fixo e qualidade adaptativa, para o jogo nunca rodar em câmera lenta.
- Docstrings obrigatórias (gate no `ruff`), site de documentação (MkDocs) e matriz de
  rastreabilidade verificada por teste automatizado.
- Boas práticas de Git/GitHub: `LICENSE`, `CONTRIBUTING.md`, hooks de pre-commit
  espelhando o gate de CI, Dependabot, `permissions` de menor privilégio.

## Anterior à v3

Ver [`specs/v1/README.md`](specs/v1/README.md), [`specs/v2/README.md`](specs/v2/README.md)
e as [Releases do GitHub](https://github.com/douglaspands/blocky-bird-game/releases)
(`v0.0.1`–`v1.2.0`).
