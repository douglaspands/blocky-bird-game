# Contribuindo

Este é, antes de tudo, um projeto pessoal — feito para estudar Spec Driven Development
(SDD) na prática e para o meu filho jogar (ver
[Sobre este projeto e o método SDD](README.md#sobre-este-projeto-e-o-metodo-sdd)). Não
há um processo formal de triagem de issues de terceiros, mas as convenções abaixo são
as que o próprio histórico de commits já segue — documentá-las é o que R35.3 pede.

## Fluxo de trabalho: spec antes de código

Qualquer mudança de comportamento começa pela spec, não pelo código. Antes de abrir um
PR:

1. Confira `specs/vN/tasks.md` (a pasta de maior número é sempre a atual) — a mudança
   já é uma task pendente? Se for funcionalidade nova, `requirements.md`/`design.md`/
   `tasks.md` são atualizados **antes** de escrever qualquer código.
2. Implemente uma task por vez, na ordem em que aparece em `tasks.md`.
3. Rode o gate local (`uv run pre-commit run --all-files`, `SDL_VIDEODRIVER=dummy uv run
   pytest`) antes de marcar a task como `[x]`.
4. Se a task introduziu ou mudou um critério de aceitação, atualize
   `specs/vN/traceability.md` na mesma mudança — `tests/test_traceability.py` falha o
   build se um critério ficar sem linha ou se a matriz citar um teste inexistente.

## Branches

- `main` — sempre no estado da última versão lançada.
- `release/vN` — branch de integração de uma versão (`v1`, `v2`, `v3`...), correspondendo
  a `specs/vN/`. Task por task é commitada aqui (ou numa `feature/` que depois vira PR
  para cá) até a versão fechar; então `release/vN` vai para `main` por Pull Request.
- `feature/<slug>` — trabalho em andamento numa fatia específica (ex.:
  `feature/v3-blocky-bee`). `<slug>` descreve o que está sendo feito, não a versão
  sozinha (a versão já está implícita na branch `release/vN` de destino).

## Commits

Mensagem no imperativo, em português, citando a task e/ou o requisito de
`specs/vN/tasks.md`/`requirements.md` que o commit resolve:

```
Adiciona os mobs decorativos das faixas (task 57)
Acrescenta ao escopo da v3 a entrada em toda a area visivel (R34)
```

Um commit por task (ou por um pequeno intervalo de tasks relacionadas) mantém o
histórico legível como um registro do plano sendo executado, não como uma lista de
diffs desconexos.

## Tags e releases

Tags seguem [SemVer](https://semver.org/) com prefixo `v`: `vMAJOR.MINOR.PATCH`, com
sufixo `-RCn` opcional para candidatos a release (`v1.2.0-RC1`, `v1.2.0-RC2`...) antes
da tag final. Publicar uma Release no GitHub com uma dessas tags dispara
[`.github/workflows/release.yml`](.github/workflows/release.yml), que builda e anexa os
executáveis de desktop e o APK — ver a seção "Releases automatizadas" do
[`README.md`](README.md).

## Antes de abrir um Pull Request

- `uv run pre-commit install` uma vez, para os hooks (`ruff`, `ty`, checagens de
  higiene — ver [`.pre-commit-config.yaml`](.pre-commit-config.yaml)) rodarem a cada
  commit. O CI roda os mesmos hooks, então pular a instalação local só adia o feedback.
- `SDL_VIDEODRIVER=dummy uv run pytest` verde, com a cobertura mínima declarada em
  `pyproject.toml` (`tool.pytest.ini_options`).
- A task correspondente marcada `[x]` em `specs/vN/tasks.md`, com uma nota curta do que
  foi validado — o padrão que o próprio arquivo já usa em cada task.
- Use o [template de Pull Request](.github/PULL_REQUEST_TEMPLATE.md) como checklist.
