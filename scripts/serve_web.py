"""Builda o jogo web e serve o resultado localmente, para testar no navegador.

Wrapper fino sobre `build_web.build()`: gera `dist/BlockyBee.html` (a menos que
`--no-build` seja passado) e sobe um servidor HTTP local na pasta de saída -
abrir o arquivo direto via `file://` nao reflete como o GitHub Pages serve o
jogo, e algumas ferramentas de depuração do navegador (rede, console) exigem
uma origem http(s) real.

Uso:
    uv run python scripts/serve_web.py
    uv run python scripts/serve_web.py --port 8000 --no-build
"""

from __future__ import annotations

import argparse
import contextlib
import functools
import http.server
from pathlib import Path

from build_web import DEFAULT_OUTPUT, build


def serve(output: Path, port: int) -> None:
    """Sobe um servidor HTTP local na pasta de `output`, bloqueando ate Ctrl+C."""
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(output.parent))
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as httpd:
        url = f"http://127.0.0.1:{port}/{output.name}"
        print(f"servindo {output.parent} em {url} (Ctrl+C para parar)")
        with contextlib.suppress(KeyboardInterrupt):
            httpd.serve_forever()


def main() -> None:
    """CLI: builda (opcional) e serve o `.html` do jogo web localmente."""
    parser = argparse.ArgumentParser(description=__doc__)
    default_hint = DEFAULT_OUTPUT.relative_to(DEFAULT_OUTPUT.parent.parent)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"caminho do .html a servir (default: {default_hint})",
    )
    parser.add_argument("--port", type=int, default=8000, help="porta local do servidor (default: 8000)")
    parser.add_argument("--no-build", action="store_true", help="pula o build, so serve o arquivo existente")
    args = parser.parse_args()

    if not args.no_build:
        build(args.output)
    elif not args.output.is_file():
        raise SystemExit(f"serve_web: {args.output} nao existe - rode sem --no-build primeiro")

    serve(args.output, args.port)


if __name__ == "__main__":
    main()
