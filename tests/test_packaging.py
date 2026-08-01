"""`buildozer.spec`: o que o APK da v3 carrega (R17.1, R22.2, design secao 40).

O arquivo nao e codigo e nao roda em teste nenhum — ele so e lido pelo buildozer, na
maquina que constroi o APK, semanas depois de alguem edita-lo. Um erro de digitacao
aqui nao quebra nada localmente: aparece como um build que falha no CI ou, pior, como
um APK que sai com o nome, a versao ou as arquiteturas erradas. Estes testes sao o que
traz esse arquivo para dentro do gate.
"""

import configparser
import re
from pathlib import Path

import pytest

SPEC = Path(__file__).resolve().parent.parent / "buildozer.spec"

HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")


@pytest.fixture(scope="module")
def spec() -> configparser.ConfigParser:
    """O `buildozer.spec` lido como INI — que e exatamente como o buildozer o le.

    Sem interpolacao: o buildozer usa `%` como valor literal em varias chaves, e o
    `ConfigParser` padrao trataria isso como referencia a outra chave."""
    parser = configparser.ConfigParser(interpolation=None)
    with open(SPEC, encoding="utf-8") as handle:
        parser.read_file(handle)
    return parser


def test_the_spec_is_well_formed_ini_with_the_sections_buildozer_expects(spec):
    """R22.2: um INI mal formado so seria descoberto na maquina de build."""
    assert spec.sections() == ["app", "buildozer"]


def test_the_app_is_named_blocky_bee(spec):
    """O nome da v3, ate no pacote — `package.name` entra no id do aplicativo e no
    diretorio gravavel do recorde, entao mexer nele depois custa o recorde de quem ja
    joga (R22.1, R22.2)."""
    assert spec["app"]["title"] == "Blocky Bee"
    assert spec["app"]["package.name"] == "blockybee"
    assert spec["app"]["package.domain"] == "com.douglaspands"


def test_the_version_is_the_v3_one(spec):
    """A versao do `.spec` e o que o Android mostra e usa para decidir atualizacao."""
    assert spec["app"]["version"] == "0.3.0"


def test_the_emulator_only_architecture_is_gone(spec):
    """x86_64 so serve a emulador e ia junto no mesmo pacote, para todo aparelho.

    Removida por tamanho de artefato e tempo de build, **nao** por FPS: o aparelho ja
    escolhia a melhor ABI entre as embarcadas, entao nada em execucao muda (design
    secao 40)."""
    archs = [arch.strip() for arch in spec["app"]["android.archs"].split(",")]
    assert archs == ["armeabi-v7a", "arm64-v8a"]


def test_every_real_device_still_has_an_architecture(spec):
    """O outro lado do corte: tirar a ABI errada deixaria aparelhos sem como rodar."""
    archs = [arch.strip() for arch in spec["app"]["android.archs"].split(",")]
    assert "arm64-v8a" in archs, "todo aparelho Android corrente"
    assert "armeabi-v7a" in archs, "aparelhos de 32 bits, ate a API 21 (R17.1)"


def test_the_splash_screen_is_the_sky_and_not_a_black_screen(spec):
    """Cobre a espera entre o toque no icone e o primeiro frame com a cor do topo do
    ceu do Overworld — `biome.py`, `sky_top = (135, 206, 235)`."""
    from src.biome import BIOMES

    color = spec["app"]["android.presplash_color"]
    assert HEX_COLOR.match(color), color
    red, green, blue = (int(color[i : i + 2], 16) for i in (1, 3, 5))
    assert (red, green, blue) == BIOMES[0].sky_top


def test_the_orientation_stays_locked_in_portrait(spec):
    """O manifesto e o lado que convence o Android; `viewport.lock_portrait_orientation`
    e o que convence o SDL. Os dois precisam concordar (R23.5)."""
    assert spec["app"]["orientation"] == "portrait"
    assert spec["app"]["fullscreen"] == "1"


def test_the_android_api_range_is_the_one_the_project_promises(spec):
    """API 21 e o piso declarado desde a v2 (R17.1); mexer aqui muda quem consegue
    instalar."""
    assert spec["app"]["android.api"] == "34"
    assert spec["app"]["android.minapi"] == "21"
    assert spec["app"]["android.ndk_api"] == "21"


def test_the_pinned_p4a_branch_survives(spec):
    """O pino de `v2024.01.21` e o que mantem o build de pe (ver o comentario no
    proprio arquivo e specs/v2/design.md secao 24.1). Um `uv`/buildozer novo que o
    apagasse quebraria o APK, e isso apareceria aqui em vez de no CI."""
    assert spec["app"]["p4a.branch"] == "v2024.01.21"
    assert spec["app"]["p4a.local_recipes"] == "./p4a-recipes"


def test_the_test_and_spec_folders_never_reach_the_apk(spec):
    """Empacotar `tests/` e `specs/` levaria alguns megabytes de texto para dentro do
    aparelho."""
    excluded = [part.strip() for part in spec["app"]["source.exclude_dirs"].split(",")]
    for folder in ("tests", "specs", ".venv", "build", "dist"):
        assert folder in excluded
