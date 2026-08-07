"""Empacota o jogo como um unico arquivo `.html` autocontido (R40, design secao 51).

Roda em tres passos:

1. `pygbag --build` sobre uma copia isolada do jogo (so `main.py` + `src/` +
   `assets/`, staged num diretorio persistente em `.cache/` - rodar direto na
   raiz do repo empacotaria a arvore inteira, inclusive `.venv` (achado da
   task 85: sem `pygbag.ini`, "Ignored dirs: []"); o diretorio de stage
   precisa ser persistente, nao um tempdir, para que o proprio cache interno
   do `pygbag` (template/favicon) sobreviva entre execucoes (R40.2, task 91).
2. `vendor_runtime_assets()` baixa (so na primeira vez - ficam cacheados em
   `.cache/pygbag-runtime/`) os arquivos do runtime WebAssembly que o
   `pygbag` busca do CDN em tempo de execucao no navegador (interprete
   CPython+pygame-ce compilado, nao o codigo do jogo em si) - achado real da
   task 90 (R40.3 falhando) e o motivo desta task (R40.2, R40.5 no design.md
   secao 51).
3. `inline_assets()`, funcao pura sem dependencia de `pygbag` real, reescreve o
   `index.html` resultante embutindo em base64 cada asset binario local
   referenciado (incluindo os vendorizados no passo 2) e cada `<script
   src=...>` local como texto inline, e falha o build (R40.5) se sobrar
   alguma referencia a arquivo local externo.

Uso:
    uv run python scripts/build_web.py
    uv run python scripts/build_web.py --output dist/BlockyBee.html
"""

from __future__ import annotations

import argparse
import base64
import mimetypes
import re
import shutil
import subprocess
import sys
import urllib.request
from collections.abc import Callable
from pathlib import Path

import pygbag

ROOT = Path(__file__).resolve().parent.parent
STAGE_ENTRIES = ("main.py", "src", "assets")
DEFAULT_OUTPUT = ROOT / "dist" / "BlockyBee.html"
STAGE_DIR = ROOT / ".cache" / "pygbag-stage"
RUNTIME_CACHE_DIR = ROOT / ".cache" / "pygbag-runtime"

# Exclui esquema absoluto (http(s)://, //) e destinos que nao sao arquivo
# (ancora #, mailto:, javascript:, ja embutido data:) - so o que sobra e mesmo
# uma referencia a arquivo local.
_NOT_LOCAL = r"https?://|//|data:|#|mailto:|javascript:"
_LOCAL_ATTR_REF = re.compile(rf'\b(?:src|href)="(?!{_NOT_LOCAL})([^"]+)"')
_SCRIPT_SRC_TAG = re.compile(
    rf'<script\b(?P<pre>[^>]*?)\ssrc="(?!{_NOT_LOCAL})(?P<src>[^"]+)"(?P<post>[^>]*)>\s*</script>',
    re.IGNORECASE,
)
_LINK_HREF_TAG = re.compile(
    rf'<link\b(?P<pre>[^>]*?)\shref="(?!{_NOT_LOCAL})(?P<href>[^"]+)"(?P<post>[^>]*)>',
    re.IGNORECASE,
)

_FETCH_SHIM = """<script id="build-web-fetch-shim">
(() => {{
  const embedded = {{{entries}}};
  // Decodifica delegando ao decoder nativo (C++) de URI `data:` do proprio
  // navegador em vez de um loop JS byte a byte (Uint8Array.from + atob) -
  // para os ~20 MiB do runtime vendorizado (task 91) o loop trava a aba por
  // dezenas de segundos; `data:` e quase instantaneo.
  const embeddedDataUri = (name) => {{
    const el = document.getElementById(embedded[name]);
    return "data:application/octet-stream;base64," + el.textContent.trim();
  }};

  const originalFetch = window.fetch.bind(window);
  window.fetch = (input, init) => {{
    const url = typeof input === "string" ? input : input.url;
    const name = url.split("/").pop().split("?")[0];
    if (Object.prototype.hasOwnProperty.call(embedded, name)) {{
      return originalFetch(embeddedDataUri(name));
    }}
    return originalFetch(input, init);
  }};

  // O carregador classico de pacote do Emscripten (`main.data`) usa
  // XMLHttpRequest, nao fetch() - sem isso ele tenta uma requisicao real
  // pro caminho relativo calculado a partir da URL da pagina e falha com
  // "File not found" (achado real da task 91).
  const originalXhrOpen = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function (method, url, ...rest) {{
    const name = String(url).split("/").pop().split("?")[0];
    const resolved = Object.prototype.hasOwnProperty.call(embedded, name) ? embeddedDataUri(name) : url;
    return originalXhrOpen.call(this, method, resolved, ...rest);
  }};
}})();
</script>
"""


def _safe_id(filename: str) -> str:
    return "asset-" + re.sub(r"[^A-Za-z0-9]+", "-", filename).strip("-")


def inline_assets(html: str, asset_dir: Path, *, force_embed: frozenset[str] = frozenset()) -> str:
    """Embute em base64 todo asset local referenciado pelo HTML do pygbag.

    Substitui `<script src="...">`/`<link href="...">` locais por texto/`data:`
    inline (R40.1), e qualquer outro arquivo binario local só referenciado por
    nome (ex.: o pacote de codigo+assets que o carregador do pygbag busca via
    `fetch`/`platform.fopen`) por um bloco `<script>` base64 mais um shim de
    `fetch()` que resolve pelo nome do arquivo, sem reescrever o texto que faz
    a chamada original (R40.2). `force_embed` cobre o caso do runtime
    WebAssembly vendorizado (task 91): nomes como `main.wasm` só existem como
    texto dentro do `main.js` buscado dinamicamente pelo proprio navegador,
    nunca no `index.html` do `pygbag`, entao a heuristica de "nome aparece
    como texto solto no HTML" não os encontra sozinha. Levanta `SystemExit`
    se sobrar referencia a arquivo local externo apos o processamento
    (R40.5) - falhar aqui e preferivel a publicar um arquivo que parece
    unico mas ainda depende de rede.
    """
    local_files = {p.name: p for p in asset_dir.iterdir() if p.is_file()}

    def _inline_script(match: re.Match[str]) -> str:
        filename = Path(match.group("src")).name
        if filename not in local_files:
            return match.group(0)
        content = local_files[filename].read_text(encoding="utf-8")
        return f"<script{match.group('pre')}{match.group('post')}>{content}</script>"

    html = _SCRIPT_SRC_TAG.sub(_inline_script, html)

    def _inline_link(match: re.Match[str]) -> str:
        filename = Path(match.group("href")).name
        if filename not in local_files:
            return match.group(0)
        data = local_files[filename].read_bytes()
        mime = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        data_uri = f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"
        return f'<link{match.group("pre")} href="{data_uri}"{match.group("post")}>'

    html = _LINK_HREF_TAG.sub(_inline_link, html)

    to_embed = sorted(
        name for name in local_files if name != "index.html" and (name in force_embed or f'"{name}"' in html)
    )
    if to_embed:
        entries_js = ", ".join(f'"{name}": "{_safe_id(name)}"' for name in to_embed)
        asset_blocks = "\n".join(
            f'<script type="application/octet-stream;base64" id="{_safe_id(name)}">'
            f"{base64.b64encode(local_files[name].read_bytes()).decode('ascii')}</script>"
            for name in to_embed
        )
        injection = _FETCH_SHIM.format(entries=entries_js) + asset_blocks
        if "<head>" in html:
            html = html.replace("<head>", "<head>" + injection, 1)
        elif "<body>" in html:
            html = html.replace("<body>", "<body>" + injection, 1)
        else:
            html = injection + html

    leftover = [match.group(0) for match in _LOCAL_ATTR_REF.finditer(html)]
    if leftover:
        raise SystemExit(
            f"build_web: referencia a arquivo local externo restante apos inline_assets (R40.5): {leftover!r}"
        )
    return html


# Runtime WebAssembly vendorizado (R40.2, R40.5 - design.md secao 51, task 91)
# ------------------------------------------------------------------------
#
# `pygbag` NAO empacota o interprete CPython+pygame-ce compilado para WASM -
# por padrao ele e buscado do CDN do proprio projeto a cada carregamento da
# pagina no navegador (achado real da task 90, nao hipotese: R40.3 falhando,
# ~21,9 MiB em 14 requisicoes). Esta lista foi obtida empiricamente (task 91,
# mesmo metodo das tasks 85/88/90: Chrome real via CDP, captura de rede,
# partida completa jogada com sucesso) contra o build real deste projeto -
# nao e generica, esta pinada a esta combinacao exata de versoes.
#
# Origem: https://pygame-web.github.io/cdn/ (projeto pygame-web/pygbag, MIT).
# Versao: pygbag 0.9.3 / Python 3.12 / pygame-ce 2.5.7 (a mesma resolvida em
# `uv.lock`). Tamanho total observado: ~21,9 MiB (dominado por `main.wasm`
# 13,4 MiB e `main.data` 6,7 MiB - o interprete CPython e a biblioteca padrao
# compilados para WASM, não o código do jogo).
#
# NAO inclui `browserfs.min.js`: o `<script src=...>` que o template do
# `pygbag` gera para ele aponta pra um arquivo que nao existe mais no CDN
# (404 real, confirmado por `curl` - nao HEAD, que poderia mascarar; o corpo
# da resposta e a pagina de erro padrao do GitHub Pages). Ja e uma referencia
# morta no build de hoje (silenciosamente ignorada pelo navegador, sem
# quebrar o jogo - mesmo achado da task 90), entao nao ha nada pra vendorizar
# ali; `_strip_dead_browserfs_script` remove a tag em vez de tentar embutir
# um arquivo que nao existe.
_PYGBAG_CDN = "https://pygame-web.github.io/cdn/"
_PYGBAG_VERSION = "0.9.3"
_RUNTIME_MANIFEST = (
    f"{_PYGBAG_VERSION}/pythons.js",
    "vtx.js",
    "vt/xterm.css",
    "vt/xterm.js",
    "vt/xterm-addon-image.js",
    f"{_PYGBAG_VERSION}/cpython312/main.js",
    f"{_PYGBAG_VERSION}/cpython312/main.data",
    f"{_PYGBAG_VERSION}/cpython312/main.wasm",
    f"{_PYGBAG_VERSION}/empty.ogg",
    f"{_PYGBAG_VERSION}/cpythonrc.py",
    f"index-{_PYGBAG_VERSION}-cp312.json",
    "cp312/pygame_ce-2.5.7-cp312-cp312-wasm32_bi_emscripten.whl",
)
_DEAD_BROWSERFS_SCRIPT = re.compile(
    r'<script\b[^>]*\ssrc="https://pygame-web\.github\.io/cdn/[^"]*browserfs\.min\.js"[^>]*>\s*</script>',
    re.IGNORECASE,
)
# `pythons.js` e o unico `<script src=...>` do template do pygbag cujo
# conteudo entre as tags NAO e descartavel: e codigo Python real (o bootstrap
# `custom_site()`, comentado via `#<!-- ... -->` so pra nunca ser executado
# como JS pelo navegador, ja que a tag tem `src`) que o proprio `pythons.js`
# le de volta via a propriedade `.text` do elemento `<script>` (achado real
# da task 91, depois de um primeiro build travar em "Downloading..." pra
# sempre: `.text` devolve o conteudo do elemento independente do atributo
# `src`, entao esse "conteudo morto" e na verdade o dado de entrada do
# interprete). Por isso so o ATRIBUTO `src` e reescrito - pra uma URI `data:`
# com o `pythons.js` vendorizado - nunca o corpo da tag; `_SCRIPT_SRC_TAG`
# generico de `inline_assets` nao serve aqui porque so casa tags vazias.
# Captura so a ABERTURA da tag (ate o primeiro `>`), nunca o corpo - precisa
# tambem inserir um `<script>` novo ANTES dela (ver `_inline_pythons_js`).
_PYTHONS_JS_OPEN_TAG = re.compile(
    r'<script\b(?P<pre>[^>]*?)\ssrc="https://pygame-web\.github\.io/cdn/[^"]*pythons\.js"(?P<post>[^>]*)>'
)


def _download(url: str, dest: Path) -> None:
    """Baixa `url` para `dest`, criando o diretorio pai se preciso."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, dest)


def vendor_runtime_assets(
    cache_dir: Path, download: Callable[[str, Path], None] = _download
) -> dict[str, Path]:
    """Garante uma copia local de cada arquivo do runtime WebAssembly.

    So acessa rede para arquivos ainda nao presentes em `cache_dir` - numa
    segunda execucao com o mesmo `cache_dir` (o default e persistente em
    `.cache/pygbag-runtime/`, fora do controle de versao) nenhum download
    acontece (R40.2). Falha alto se a versao do `pygbag` instalada nao bater
    com a que este manifesto foi validado contra (task 91) - o nome de
    arquivo do runtime muda por versao (ex.: `cpython312/`), entao seguir com
    um manifesto desatualizado baixaria silenciosamente o arquivo errado ou
    simplesmente 404aria.
    """
    if pygbag.__version__ != _PYGBAG_VERSION:
        raise SystemExit(
            f"build_web: pygbag instalado ({pygbag.__version__}) difere do manifesto de runtime "
            f"vendorizado ({_PYGBAG_VERSION}) - revalide _RUNTIME_MANIFEST (task 91) contra um build real "
            "antes de atualizar essa constante."
        )
    vendored: dict[str, Path] = {}
    for relative in _RUNTIME_MANIFEST:
        dest = cache_dir / relative
        if not dest.is_file():
            download(_PYGBAG_CDN + relative, dest)
        vendored[Path(relative).name] = dest
    return vendored


def _data_uri(mime: str, data: bytes) -> str:
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


def _patch_vtx_js(vtx_js: str, xterm_js: bytes, xterm_addon: bytes, xterm_css: bytes) -> str:
    """Substitui a resolucao de `xterm.js`/`xterm-addon-image.js`/`xterm.css`.

    `vtx.js` normalmente monta essas tres URLs a partir de
    `window.Module.config.cdn` (ou de um fallback fixo para o CDN real do
    `pygbag` se isso nao estiver definido ainda). Nenhum dos dois caminhos
    passa por `window.fetch()` - `import()` de modulo ES e o `<link>` de CSS
    que `vtx.js` cria via `document.createElement` carregam recursos
    diretamente, sem o shim de `inline_assets` conseguir interceptar - entao
    so vendorizar os arquivos nao bastava (achado real da task 91). Troca as
    tres linhas por URIs `data:` diretas dos arquivos ja vendorizados.
    """
    vtx_js = vtx_js.replace('xterm_cdn + "xterm.js"', f'"{_data_uri("text/javascript", xterm_js)}"')
    vtx_js = vtx_js.replace(
        'xterm_cdn + "xterm-addon-image.js"', f'"{_data_uri("text/javascript", xterm_addon)}"'
    )
    vtx_js = vtx_js.replace("xterm_cdn + css", f'"{_data_uri("text/css", xterm_css)}"')
    return vtx_js


def _patch_pythons_js(pythons_js: str, vtx_js: str, empty_ogg: bytes) -> str:
    """Substitui dois pontos de `pythons.js` que dependem de `config.cdn`.

    1. `import("../vtx.js")`, resolvido relativo a URL do proprio
       `pythons.js`. Depois que essa URL vira uma URI `data:` (ver
       `_inline_pythons_js`), esse caminho relativo nao tem mais hierarquia
       pra resolver contra, e o `import()` lanca `TypeError: Failed to
       resolve module specifier` (achado real da task 91). Um especificador
       `data:` absoluto nao depende de resolucao relativa.
    2. `new Audio(config.cdn+"empty.ogg")`, o "desbloqueio" de audio que
       espera o primeiro gesto do usuario (R38.3) - `config.cdn` sozinho ja
       foi contornado pra `executable` via `window.config` pre-definido (ver
       `_inline_pythons_js`), mas essa expressao concatena `config.cdn` com
       um sufixo DIFERENTE ("empty.ogg", nao "cpython312/main.js"), entao um
       `window.config.cdn` fixo não bastaria - e `new Audio(...).play()` e
       uma carga de midia nativa, que tambem nao passa por
       `window.fetch()`. Sem isso o boot trava para sempre repetindo "**
       MEDIA USER ACTION REQUIRED **" a cada retry (achado real da task 91,
       nao e de fato esperar um gesto: `config.cdn` corrompido faz o
       `Audio.play()` falhar sempre, gesto nenhum resolve).
    """
    vtx_js_uri = _data_uri("text/javascript", vtx_js.encode("utf-8"))
    pythons_js = pythons_js.replace('import("../vtx.js")', f'import("{vtx_js_uri}")')
    empty_ogg_uri = _data_uri("audio/ogg", empty_ogg)
    pythons_js = pythons_js.replace('config.cdn+"empty.ogg"', f'"{empty_ogg_uri}"')
    return pythons_js


def _inline_pythons_js(html: str, content: str, *, main_js: bytes) -> str:
    """Reescreve o script de `pythons.js` para rodar sem nenhuma rede.

    Preserva o corpo da tag intacto - ver comentario de `_PYTHONS_JS_SRC`
    sobre por que esse corpo nao pode ser descartado nem reescrito (R40.2,
    task 91). O proprio `pythons.js` se auto-descobre em `auto_start()`
    varrendo `document.getElementsByTagName('script')` e comparando
    `script.src.search("pythons.js") >= 0` - uma URI `data:` pura nao contem
    esse texto, entao `pythons.js` nunca se reconhece e o boot trava para
    sempre em "Downloading..." (achado real da task 91, silencioso: sem
    excecao, sem requisicao de rede, so nunca avanca). O fragmento
    `#pythons.js` no final da URI e inerte para o navegador (nao faz parte
    dos dados decodificados) mas mantem a substring que essa autodescoberta
    exige.

    Um `<script>` extra e inserido logo antes, pre-definindo `window.config`
    com dois valores:

    - `executable`, ja resolvido para o `main.js` vendorizado: sem isso,
      `pythons.js` calcula `config.executable` concatenando `config.cdn`
      (que cai no mesmo fallback baseado em `url.split(...)` quebrado pela
      URI `data:` do proprio script) com `cpython312/main.js`, e carrega o
      resultado via `jsimport()` - um `<script src=...>` de verdade, criado
      via DOM, que tambem nao passa por `window.fetch()` (achado real da
      task 91). Pre-definir `executable` (usado com `||`, então nunca
      recalculado) evita essa camada de URL quebrada.
    - `cdn`, fixado em `"./"`: os poucos outros lugares que ainda concatenam
      `config.cdn` com um nome de arquivo (ex.: `cpythonrc.py`, via
      `fetch()`) passam a montar uma URL relativa valida de verdade
      (`"./cpythonrc.py"`), que o shim de `fetch()` de `inline_assets`
      intercepta pelo nome do arquivo - sem depender do mesmo fallback
      quebrado (task 91). Nao cobre `new Audio(config.cdn+"empty.ogg")`
      porque isso e midia nativa, nunca passa por `fetch()`; esse caso e
      corrigido a parte em `_patch_pythons_js`.
    """
    main_js_uri = _data_uri("text/javascript", main_js)
    config_seed = f'<script>window.config = {{"cdn": "./", "executable": "{main_js_uri}"}};</script>'
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
    data_uri = f"data:text/javascript;base64,{encoded}#pythons.js"

    def _rewrite_open_tag(match: re.Match[str]) -> str:
        return config_seed + f'<script{match.group("pre")} src="{data_uri}"{match.group("post")}>'

    return _PYTHONS_JS_OPEN_TAG.sub(_rewrite_open_tag, html, count=1)


def _strip_dead_browserfs_script(html: str) -> str:
    """Remove o `<script src=...browserfs.min.js>` do template do `pygbag`.

    Esse arquivo nao existe mais no CDN (404 real, task 91) - deixar a tag
    intacta manteria uma requisicao de rede real (ainda que sempre falhe)
    quando o `.html` final for aberto, violando R40.3 por um arquivo que
    nunca teve conteudo pra vendorizar em primeiro lugar.
    """
    return _DEAD_BROWSERFS_SCRIPT.sub("", html)


def _stage() -> Path:
    """Copia `main.py` + `src/` + `assets/` para um diretorio isolado e persistente.

    Fica em `.cache/pygbag-stage/`, fora do controle de versao. Isolado
    porque `pygbag --build` empacota a arvore inteira a partir do
    diretorio do `main.py` informado - sem isso ele arrastaria `.venv`/
    `build` junto (achado da task 85). Persistente (nao um tempdir) porque o
    proprio `pygbag` mantem seu cache de template/favicon dentro de
    `build/web-cache/`, ao lado de `main.py` - reusar o mesmo diretorio entre
    execucoes e o que permite a esse cache sobreviver e evitar as duas
    requisicoes de rede que `pygbag --build` faria a cada execucao (R40.2,
    task 91). Cada chamada apaga e recopia so `STAGE_ENTRIES`, preservando o
    `build/` gerado pelo `pygbag` ao lado.
    """
    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    for name in STAGE_ENTRIES:
        source, dest = ROOT / name, STAGE_DIR / name
        if dest.is_dir():
            shutil.rmtree(dest)
        elif dest.exists():
            dest.unlink()
        if source.is_dir():
            shutil.copytree(source, dest)
        else:
            shutil.copy2(source, dest)
    return STAGE_DIR


def _pygbag_build(main_py: Path) -> Path:
    """Roda `pygbag --build` e devolve o diretorio com o `index.html` gerado."""
    subprocess.run([sys.executable, "-m", "pygbag", "--build", str(main_py)], check=True)
    return main_py.parent / "build" / "web"


def build(output: Path) -> None:
    """Roda o pipeline completo e escreve o `.html` final em `output`."""
    stage = _stage()
    web_dir = _pygbag_build(stage / "main.py")

    vendored = vendor_runtime_assets(RUNTIME_CACHE_DIR)

    # `empty.ogg` fica nos dois lugares: o desbloqueio de audio (R38.3) cria
    # um <audio> nativo direto (nunca passa por window.fetch(), corrigido a
    # parte em _patch_pythons_js), mas o proprio jogo tambem pode buscar o
    # mesmo arquivo via fetch() (confirmado na captura de rede da task 91) -
    # esse segundo caso continua coberto pelo force_embed generico abaixo.
    empty_ogg = vendored["empty.ogg"].read_bytes()

    # Os outros quatro sao embutidos via URI `data:` direto no texto de
    # `pythons.js`/`vtx.js` (ver `_patch_pythons_js`/`_patch_vtx_js`/
    # `_inline_pythons_js`), nunca buscados por `window.fetch()` - nao
    # sobram como `<script>` separado pro `force_embed` genérico tratar.
    vtx_js = _patch_vtx_js(
        vendored.pop("vtx.js").read_text(encoding="utf-8"),
        vendored.pop("xterm.js").read_bytes(),
        vendored.pop("xterm-addon-image.js").read_bytes(),
        vendored.pop("xterm.css").read_bytes(),
    )
    pythons_js = _patch_pythons_js(vendored.pop("pythons.js").read_text(encoding="utf-8"), vtx_js, empty_ogg)
    main_js = vendored.pop("main.js").read_bytes()

    # O resto (main.wasm/main.data/wheel/cpythonrc.py/empty.ogg/index json) e
    # buscado via `window.fetch()` em tempo de execucao (confirmado
    # empiricamente, task 91) - o shim generico de `inline_assets` cobre.
    for path in vendored.values():
        shutil.copy2(path, web_dir / path.name)

    html = (web_dir / "index.html").read_text(encoding="utf-8")
    html = _strip_dead_browserfs_script(html)
    html = _inline_pythons_js(html, pythons_js, main_js=main_js)
    final_html = inline_assets(html, web_dir, force_embed=frozenset(vendored))

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(final_html, encoding="utf-8")
    print(f"build web salvo em {output} ({output.stat().st_size / 1024:.0f} KiB)")


def main() -> None:
    """CLI: gera o `.html` unico a partir do codigo-fonte (R40.2)."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"caminho do .html final (default: {DEFAULT_OUTPUT.relative_to(ROOT)})",
    )
    args = parser.parse_args()
    build(args.output)


if __name__ == "__main__":
    main()
