"""O teste que vigia `specs/vN/traceability.md` (task 68, design secao 42).

Falha se um criterio `RN.M` de `requirements.md` nao aparece na matriz (R32.2) e falha se
a matriz cita um teste que nao existe (R32.3). Sem isso a matriz e so mais um documento
que envelhece em silencio assim que um requisito novo entra ou um teste e renomeado.
"""

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = Path(__file__).resolve().parent


def _latest_specs_dir() -> Path:
    """A pasta de spec vigente: a de maior numero em `specs/`, por convencao do projeto."""
    versions = [p for p in (ROOT / "specs").iterdir() if p.is_dir() and re.fullmatch(r"v\d+", p.name)]
    return max(versions, key=lambda p: int(p.name[1:]))


SPECS_DIR = _latest_specs_dir()
REQUIREMENTS = SPECS_DIR / "requirements.md"
TRACEABILITY = SPECS_DIR / "traceability.md"

_SECTION = re.compile(r"^## R(\d+)\b.*$", re.MULTILINE)
_ITEM = re.compile(r"^(\d+)\. ", re.MULTILINE)
_CRITERIO = re.compile(r"^R\d+\.\d+$")
_TEST_REF = re.compile(r"`([\w./]+\.py)::(\w+)`")


def _required_criteria() -> list[str]:
    """Todo `RN.M` de `requirements.md`, na ordem em que aparece no documento."""
    text = REQUIREMENTS.read_text(encoding="utf-8")
    sections = list(_SECTION.finditer(text))
    criteria = []
    for index, section in enumerate(sections):
        start = section.end()
        end = sections[index + 1].start() if index + 1 < len(sections) else len(text)
        r_number = section.group(1)
        for item_number in _ITEM.findall(text[start:end]):
            criteria.append(f"R{r_number}.{item_number}")
    return criteria


def _matrix_rows() -> dict[str, str]:
    """Mapa `RN.M -> conteudo da coluna Testes`, lido linha a linha da tabela markdown."""
    rows: dict[str, str] = {}
    for line in TRACEABILITY.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.split("|")]
        if len(cells) < 5 or not _CRITERIO.match(cells[1]):
            continue
        rows[cells[1]] = cells[4]
    return rows


def _defined_test_functions(path: Path) -> set[str]:
    """Todo nome de funcao definido no arquivo, em qualquer nivel (modulo ou classe)."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)}


def test_every_acceptance_criterion_is_in_the_matrix():
    """R32.2: um criterio novo em requirements.md sem linha na matriz quebra o build."""
    required = _required_criteria()
    assert required, "a extracao de requirements.md nao encontrou nenhum criterio RN.M"
    missing = [criterio for criterio in required if criterio not in _matrix_rows()]
    assert not missing, f"faltando em {TRACEABILITY}: {missing}"


def test_the_matrix_has_no_row_left_over_from_a_renumbered_requirement():
    """O outro lado de R32.2: uma linha sem criterio correspondente sobrou de um requisito renumerado."""
    required = set(_required_criteria())
    extra = [criterio for criterio in _matrix_rows() if criterio not in required]
    assert not extra, f"em {TRACEABILITY} mas nao existe mais em {REQUIREMENTS}: {extra}"


def test_every_test_reference_in_the_matrix_resolves_to_a_real_function():
    """R32.3: uma referencia inventada, ou um teste renomeado sem atualizar a matriz, quebra o build."""
    unresolved = []
    functions_by_file: dict[str, set[str]] = {}
    for criterio, testes in _matrix_rows().items():
        for file_name, func_name in _TEST_REF.findall(testes):
            test_path = TESTS_DIR / file_name
            if not test_path.is_file():
                unresolved.append(f"{criterio}: {file_name} nao existe em {TESTS_DIR}")
                continue
            if file_name not in functions_by_file:
                functions_by_file[file_name] = _defined_test_functions(test_path)
            if func_name not in functions_by_file[file_name]:
                unresolved.append(f"{criterio}: {file_name}::{func_name} nao existe")
    assert not unresolved, unresolved
