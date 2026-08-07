"""Empacota o jogo como um unico arquivo `.html` autocontido (R40, design secao 51).

Roda em dois passos:

1. `pygbag --build` sobre uma copia isolada do jogo (so `main.py` + `src/` +
   `assets/`, staged num diretorio temporario) - rodar direto na raiz do repo
   empacotaria a arvore inteira, inclusive `.venv` (achado da task 85: sem
   `pygbag.ini`, "Ignored dirs: []").
2. `inline_assets()`, funcao pura sem dependencia de `pygbag` real, reescreve o
   `index.html` resultante embutindo em base64 cada asset binario local
   referenciado e cada `<script src=...>` local como texto inline, e falha o
   build (R40.5) se sobrar alguma referencia a arquivo local externo.

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
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STAGE_ENTRIES = ("main.py", "src", "assets")
DEFAULT_OUTPUT = ROOT / "dist" / "BlockyBee.html"

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
  const originalFetch = window.fetch.bind(window);
  window.fetch = (input, init) => {{
    const url = typeof input === "string" ? input : input.url;
    const name = url.split("/").pop().split("?")[0];
    if (Object.prototype.hasOwnProperty.call(embedded, name)) {{
      const el = document.getElementById(embedded[name]);
      const bytes = Uint8Array.from(atob(el.textContent.trim()), c => c.charCodeAt(0));
      return Promise.resolve(new Response(bytes));
    }}
    return originalFetch(input, init);
  }};
}})();
</script>
"""


def _safe_id(filename: str) -> str:
    return "asset-" + re.sub(r"[^A-Za-z0-9]+", "-", filename).strip("-")


def inline_assets(html: str, asset_dir: Path) -> str:
    """Embute em base64 todo asset local referenciado pelo HTML do pygbag.

    Substitui `<script src="...">`/`<link href="...">` locais por texto/`data:`
    inline (R40.1), e qualquer outro arquivo binario local só referenciado por
    nome (ex.: o pacote de codigo+assets que o carregador do pygbag busca via
    `fetch`/`platform.fopen`) por um bloco `<script>` base64 mais um shim de
    `fetch()` que resolve pelo nome do arquivo, sem reescrever o texto que faz
    a chamada original (R40.2). Levanta `SystemExit` se sobrar referencia a
    arquivo local externo apos o processamento (R40.5) - falhar aqui e
    preferivel a publicar um arquivo que parece unico mas ainda depende de
    rede.
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

    to_embed = sorted(name for name in local_files if name != "index.html" and f'"{name}"' in html)
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


def _stage(tmp_dir: Path) -> Path:
    """Copia so `main.py` + `src/` + `assets/` para um diretorio isolado.

    `pygbag --build` empacota a arvore inteira a partir do diretorio do
    `main.py` informado; sem esse isolamento ele arrastaria `.venv`/`build`
    junto (achado da task 85).
    """
    stage = tmp_dir / "stage"
    stage.mkdir()
    for name in STAGE_ENTRIES:
        source, dest = ROOT / name, stage / name
        if source.is_dir():
            shutil.copytree(source, dest)
        else:
            shutil.copy2(source, dest)
    return stage


def _pygbag_build(main_py: Path) -> Path:
    """Roda `pygbag --build` e devolve o diretorio com o `index.html` gerado."""
    subprocess.run([sys.executable, "-m", "pygbag", "--build", str(main_py)], check=True)
    return main_py.parent / "build" / "web"


def build(output: Path) -> None:
    """Roda o pipeline completo e escreve o `.html` final em `output`."""
    with tempfile.TemporaryDirectory(prefix="blockybee-web-") as tmp:
        stage = _stage(Path(tmp))
        web_dir = _pygbag_build(stage / "main.py")
        html = (web_dir / "index.html").read_text(encoding="utf-8")
        final_html = inline_assets(html, web_dir)

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
