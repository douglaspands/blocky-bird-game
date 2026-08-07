"""Higiene de Git/GitHub (task 74+, design secao 44, R35).

Estes arquivos nao sao codigo do jogo e nao rodam em nenhum outro teste — sao
configuracao lida por ferramentas externas (pip/uv, pre-commit, Dependabot, GitHub) ou
por um humano (LICENSE, CONTRIBUTING.md). Um erro aqui so apareceria semanas depois,
como uma licenca que ninguem le, um hook que nunca roda ou um Dependabot mal configurado
que nunca abre PR nenhum. Mesma logica de tests/test_packaging.py para o buildozer.spec.
"""

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent

LICENSE = ROOT / "LICENSE"
PYPROJECT = ROOT / "pyproject.toml"
README = ROOT / "README.md"
EDITORCONFIG = ROOT / ".editorconfig"
GITATTRIBUTES = ROOT / ".gitattributes"
PRE_COMMIT_CONFIG = ROOT / ".pre-commit-config.yaml"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
CONTRIBUTING = ROOT / "CONTRIBUTING.md"
CHANGELOG = ROOT / "CHANGELOG.md"
DEPENDABOT = ROOT / ".github" / "dependabot.yml"
PR_TEMPLATE = ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md"
RELEASE_WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"
DOCS_WORKFLOW = ROOT / ".github" / "workflows" / "docs.yml"


def _pre_commit_hook_ids() -> set[str]:
    data = yaml.safe_load(PRE_COMMIT_CONFIG.read_text(encoding="utf-8"))
    return {hook["id"] for repo in data["repos"] for hook in repo["hooks"]}


def test_the_license_file_is_mit_with_the_current_copyright_holder():
    """R35.1: sem o arquivo, nao ha licenca nenhuma — so a ausencia de aviso legal."""
    text = LICENSE.read_text(encoding="utf-8")
    assert "MIT License" in text
    assert "Copyright (c) 2026 Douglas Panhota" in text


def test_pyproject_declares_the_same_license_as_the_license_file():
    """R35.2: os metadados do pacote e o arquivo LICENSE nao podem divergir.

    Sem `tomllib` (so a partir do Python 3.11, e o projeto fixa `requires-python
    >= 3.10`) e sem depender de um parser TOML de terceiros so para uma linha —
    regex no bloco `[project]` basta.
    """
    text = PYPROJECT.read_text(encoding="utf-8")
    project_section = text.split("[project]", 1)[1].split("\n[", 1)[0]
    match = re.search(r'^license\s*=\s*"([^"]+)"', project_section, re.MULTILINE)
    assert match is not None, "campo license ausente em [project]"
    assert match.group(1) == "MIT"


def test_readme_references_the_license_and_disclaims_the_minecraft_trademark():
    """R35.1: a licenca cobre o codigo, nao a marca Minecraft — o README precisa dizer isso."""
    text = README.read_text(encoding="utf-8")
    assert "[MIT](LICENSE)" in text
    assert "marca **Minecraft**" in text


def test_editorconfig_is_root_and_normalizes_whitespace():
    """R35.7: sem `root = true`, um `.editorconfig` num diretorio pai poderia sobrescrever isto."""
    text = EDITORCONFIG.read_text(encoding="utf-8")
    assert re.search(r"^root\s*=\s*true", text, re.MULTILINE)
    assert "end_of_line = lf" in text
    assert "indent_size = 4" in text, "identacao de 4 espacos para .py, igual ao ruff format"


def test_gitattributes_normalizes_line_endings_and_marks_known_binaries():
    """R35.7: sem isto, um clone novo no Linux (CI) ve o repo inteiro mudado so por CRLF/LF."""
    text = GITATTRIBUTES.read_text(encoding="utf-8")
    assert re.search(r"^\*\s+text=auto\s+eol=lf", text, re.MULTILINE)
    assert re.search(r"^\*\.png\s+binary", text, re.MULTILINE)
    assert re.search(r"^\*\.ico\s+binary", text, re.MULTILINE)


def test_pre_commit_mirrors_the_ci_lint_and_type_gate():
    """R35.5: ruff e ty precisam ser os mesmos hooks que o CI roda separadamente."""
    hook_ids = _pre_commit_hook_ids()
    assert {"ruff-check", "ruff-format", "ty"} <= hook_ids


def test_pre_commit_has_the_hygiene_hooks_ruff_and_ty_do_not_cover():
    """R35.5: whitespace, YAML/TOML e conflito de merge nao sao checados por ruff/ty/pytest."""
    hook_ids = _pre_commit_hook_ids()
    expected = {
        "trailing-whitespace",
        "end-of-file-fixer",
        "check-merge-conflict",
        "check-added-large-files",
        "check-toml",
        "check-yaml",
        "mixed-line-ending",
    }
    assert expected <= hook_ids


def test_ci_also_runs_the_pre_commit_hooks():
    """R35.6: sem isto, os hooks de higiene so valem para quem lembrar de instalar localmente."""
    text = CI_WORKFLOW.read_text(encoding="utf-8")
    assert "pre-commit run --all-files" in text


def test_ci_runs_a_build_web_smoke_test_on_every_push():
    """R40.5: sem isto, uma referencia externa remanescente so quebraria o build web

    na proxima vez que um humano lembrasse de rodar `scripts/build_web.py` manualmente
    (tasks 90/91) - o `SystemExit` de `inline_assets` so protege quem roda o script.
    """
    data = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    jobs = data["jobs"]
    assert "build-web-smoke" in jobs
    steps = " ".join(step.get("run", "") for step in jobs["build-web-smoke"]["steps"])
    assert "scripts/build_web.py" in steps


def test_docs_workflow_publishes_the_web_build_alongside_the_docs_site():
    """R41.1: uma implantacao, dois conteudos — o jogo precisa ir para site/play/

    antes do upload-pages-artifact, senao a publicacao do Pages so teria a
    documentacao (mesma implantacao ja usada por ela, R31.4), nunca o jogo.
    """
    data = yaml.safe_load(DOCS_WORKFLOW.read_text(encoding="utf-8"))
    steps = data["jobs"]["build"]["steps"]
    run_steps = " ".join(step.get("run", "") for step in steps)
    assert "scripts/build_web.py" in run_steps
    assert "site/play/index.html" in run_steps

    build_web_index = next(i for i, s in enumerate(steps) if "scripts/build_web.py" in s.get("run", ""))
    docs_build_index = next(i for i, s in enumerate(steps) if "mkdocs build" in s.get("run", ""))
    upload_uses = "actions/upload-pages-artifact"
    upload_index = next(i for i, s in enumerate(steps) if s.get("uses", "").startswith(upload_uses))
    assert docs_build_index < build_web_index < upload_index


def test_release_workflow_attaches_the_web_build_as_a_fourth_asset():
    """R41.2: mesmo padrao de isolamento de risco do build-apk (design v2 secao 24.1) —

    um job independente, para que uma falha no build web nao impeca a publicacao dos
    binarios de desktop/Android ja existentes.
    """
    data = yaml.safe_load(RELEASE_WORKFLOW.read_text(encoding="utf-8"))
    jobs = data["jobs"]
    assert "build-web" in jobs
    assert jobs["build-web"] != jobs.get("build-apk"), "precisa ser um job proprio, nao um alias"

    steps = jobs["build-web"]["steps"]
    run_steps = " ".join(step.get("run", "") for step in steps)
    assert "scripts/build_web.py" in run_steps

    gh_release_action = "softprops/action-gh-release"
    upload_step = next(step for step in steps if step.get("uses", "").startswith(gh_release_action))
    assert "BlockyBee-web-${{ github.event.release.tag_name }}.html" in upload_step["with"]["files"]


def test_contributing_documents_the_branch_naming_convention():
    """R35.3: os tres prefixos ja usados em `git branch -a` precisam estar documentados."""
    text = CONTRIBUTING.read_text(encoding="utf-8")
    assert "`main`" in text
    assert "`release/vN`" in text
    assert "`feature/<slug>`" in text


def test_contributing_documents_commit_and_tag_conventions_and_the_hook_install_command():
    """R35.3: commit imperativo citando task/requisito, tag SemVer com `v`, e como instalar o hook."""
    text = CONTRIBUTING.read_text(encoding="utf-8")
    assert "vMAJOR.MINOR.PATCH" in text
    assert "uv run pre-commit install" in text


def test_readme_points_to_contributing():
    """Fluxo de contribuição fica num só lugar — o README so aponta, nao duplica.

    Link absoluto do GitHub, nao relativo: `CONTRIBUTING.md` fica na raiz do repo, fora
    de `docs/`, entao um link relativo quebraria `mkdocs build --strict` (mesmo ajuste
    que a task 66 ja fez para o link de `release.yml`).
    """
    text = README.read_text(encoding="utf-8")
    assert "github.com/douglaspands/blocky-bird-game/blob/main/CONTRIBUTING.md" in text


def test_changelog_follows_keep_a_changelog_with_an_unreleased_section():
    """R35.4: sem cabecalho reconhecivel e sem secao Unreleased, nao e Keep a Changelog de fato."""
    text = CHANGELOG.read_text(encoding="utf-8")
    assert "keepachangelog.com" in text
    assert "## [Não lançado]" in text


def test_changelog_does_not_rewrite_pre_v3_history():
    """Design.md secao 44: as tags anteriores nao mapeiam para specs/vN — apontar, nao inventar."""
    text = CHANGELOG.read_text(encoding="utf-8")
    assert "specs/v1/README.md" in text
    assert "specs/v2/README.md" in text
    assert "github.com/douglaspands/blocky-bird-game/releases" in text


def test_dependabot_covers_uv_and_github_actions():
    """R35.8: 'pip' nao le uv.lock — precisa ser exatamente o ecossistema 'uv' (GA desde marco/2025)."""
    data = yaml.safe_load(DEPENDABOT.read_text(encoding="utf-8"))
    ecosystems = {update["package-ecosystem"] for update in data["updates"]}
    assert ecosystems == {"uv", "github-actions"}


def test_every_workflow_declares_least_privilege_permissions():
    """R35.9: sem `permissions:` explicito, um workflow herda o padrao do repo, nao o menor privilegio."""
    for workflow in (CI_WORKFLOW, RELEASE_WORKFLOW, DOCS_WORKFLOW):
        data = yaml.safe_load(workflow.read_text(encoding="utf-8"))
        assert "permissions" in data, f"{workflow.name} sem bloco permissions"


def test_pull_request_template_points_back_to_the_sdd_workflow():
    """R35.10: o checklist precisa lembrar tasks.md/traceability.md, nao so pedir 'descreva sua mudanca'."""
    text = PR_TEMPLATE.read_text(encoding="utf-8")
    assert "tasks.md" in text
    assert "traceability.md" in text
