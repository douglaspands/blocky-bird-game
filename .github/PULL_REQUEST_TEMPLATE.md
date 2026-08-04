## O quê e por quê

<!-- Task(s)/requisito(s) de specs/vN/ resolvidos por este PR. -->

Resolve a task(s) `_` de `specs/vN/tasks.md` (requisito(s) `R_`).

## Checklist

- [ ] `specs/vN/requirements.md`/`design.md` atualizados **antes** do código, se este PR
      muda comportamento ou acrescenta escopo novo.
- [ ] A(s) task(s) correspondente(s) marcada(s) `[x]` em `specs/vN/tasks.md`, com uma
      nota curta do que foi validado.
- [ ] `specs/vN/traceability.md` atualizado, se um critério de aceitação novo ou mudado
      entrou nesta mudança (`tests/test_traceability.py` falha o build se não).
- [ ] `uv run pre-commit run --all-files` verde localmente (ou confie no CI, que roda o
      mesmo gate).
- [ ] `SDL_VIDEODRIVER=dummy uv run pytest` verde, cobertura acima do mínimo declarado.

Ver [`CONTRIBUTING.md`](../CONTRIBUTING.md) para as convenções de branch, commit e tag.
