# Blocky Bird — Specs v3

**Status:** especificação concluída, implementação pendente. **Especificada em:** 2026-07-30.

## Descrição

Duas melhorias de qualidade que não mudam o gameplay nem a plataforma:

1. **Conformidade com Ruff** — todo o código Python do projeto (`main.py`, `src/`, `tests/`,
   `scripts/`, `p4a-recipes/`) passa a ser verificado por `ruff` (lint + formatação), com
   configuração explícita em `pyproject.toml` e checagem obrigatória num novo workflow de CI
   (`ci.yml`, rodando em cada push/PR — a v2 só tinha CI de release).
2. **Tamanho de fonte sem sobreposição** — a fonte bitmap própria introduzida na v2
   (`pixelfont.py`, R7.6) protege contra estouro horizontal (`_fit_scale`) mas não vertical:
   os deltas entre linhas de uma mesma tela são pixels fixos, calculados a olho para o
   tamanho original, e colidem quando o texto renderizado é maior do que o assumido. A v3
   troca esses deltas por empilhamento baseado na altura real da linha e recalibra o tamanho
   de cada papel de texto (título, instrução, HUD, overlay de pausa, game over, recorde) até
   nenhuma tela sobrepor texto — com um teste automatizado por tela para não regredir.

## Conteúdo desta pasta

- [`requirements.md`](requirements.md) — requisitos R1–R19 em formato EARS (R18–R19 são novos da v3).
- [`design.md`](design.md) — arquitetura técnica. Partes I–II (seções 1–25) são o jogo herdado da v1/v2. Parte III (seções 26–27) é o novo trabalho de qualidade da v3.
- [`tasks.md`](tasks.md) — plano incremental. Tasks 1–19 (v1) e 20–30 (v2) são histórico concluído; **tasks 31–32 são o trabalho da v3**.

## Riscos e limites conhecidos

- A calibração de tamanho de fonte (task 32) é uma decisão visual, não puramente analítica —
  os valores finais de escala por papel de texto são escolhidos por inspeção durante a
  implementação, com o teste automatizado garantindo a propriedade objetiva (não sobrepor)
  depois de escolhidos.
- Aplicar `ruff format` pela primeira vez num repositório inteiro tende a gerar um diff grande
  e majoritariamente mecânico (aspas, quebras de linha); a task 31 pede revisão manual de
  qualquer correção de `ruff check --fix` que não seja puramente estilística antes de aceitar.

## Sobre esta versão

Esta pasta é um retrato **completo e autocontido** dos specs da v3 — cobre o jogo inteiro,
não só as mudanças desta versão. As versões anteriores permanecem intactas em
[`specs/v1/`](../v1/) e [`specs/v2/`](../v2/) como histórico. Veja
[`specs/README.md`](../README.md) para o padrão de versionamento.
