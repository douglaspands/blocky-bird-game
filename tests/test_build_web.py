"""Testes de `inline_assets`/vendorizacao do runtime (R40.1, R40.2, R40.5,
design.md secao 51).

So funcoes puras sao testadas aqui, com fixtures sinteticas que reproduzem os
padroes de referencia local que um `index.html` real do `pygbag` contem
(`<script src=...>`, `<link href=...>` do icone, e um arquivo binario so
referenciado por nome dentro de outro `<script>`, como o `platform.fopen(...)`
do carregador buscando o pacote de codigo+assets) - a execucao real do
`pygbag --build` e o download real do runtime WebAssembly ficam para a
verificacao manual das tasks 90/91, caras demais e dependentes de rede para
rodar em toda execucao da suite.
"""

import base64
from pathlib import Path

import pytest

import scripts.build_web as build_web
from scripts.build_web import (
    _ensure_utf8_declared_early,
    _inline_pythons_js,
    _patch_pythons_js,
    _patch_vtx_js,
    _strip_dead_browserfs_script,
    inline_assets,
    vendor_runtime_assets,
)


def test_inline_assets_embeds_local_script_text_and_drops_the_src_attribute(tmp_path):
    (tmp_path / "app.js").write_text("console.log('oi');", encoding="utf-8")
    html = '<html><head><script src="app.js"></script></head><body></body></html>'

    result = inline_assets(html, tmp_path)

    assert 'src="app.js"' not in result
    assert "<script>console.log('oi');</script>" in result


def test_inline_assets_preserves_other_script_attributes_when_inlining(tmp_path):
    (tmp_path / "app.js").write_text("1;", encoding="utf-8")
    html = '<html><head><script type="module" src="app.js" async></script></head></html>'

    result = inline_assets(html, tmp_path)

    assert 'src="app.js"' not in result
    assert 'type="module"' in result
    assert "async" in result
    assert "1;" in result


def test_inline_assets_turns_a_local_icon_link_into_a_data_uri(tmp_path):
    png_bytes = b"\x89PNG\r\n\x1a\nfake-icon-bytes"
    (tmp_path / "favicon.png").write_bytes(png_bytes)
    html = '<html><head><link rel="icon" href="favicon.png" sizes="16x16"></head></html>'

    result = inline_assets(html, tmp_path)

    assert 'href="favicon.png"' not in result
    expected_uri = f"data:image/png;base64,{base64.b64encode(png_bytes).decode('ascii')}"
    assert expected_uri in result
    assert 'rel="icon"' in result and 'sizes="16x16"' in result


def test_inline_assets_embeds_a_binary_asset_referenced_only_by_name_via_a_fetch_shim(tmp_path):
    """Reproduz o padrao real do pygbag: o pacote tar.gz nao aparece como
    `<script src=...>`/`<link href=...>`, so como string literal dentro de
    outro bloco de script (o carregador busca por `platform.fopen(nome)`).
    """
    archive_bytes = b"PK\x03\x04fake-archive-payload"
    (tmp_path / "bundle.tar.gz").write_bytes(archive_bytes)
    html = (
        "<html><head></head><body>"
        '<script id="site">fetch("bundle.tar.gz").then(r => r.arrayBuffer());</script>'
        "</body></html>"
    )

    result = inline_assets(html, tmp_path)

    assert base64.b64encode(archive_bytes).decode("ascii") in result
    assert "window.fetch" in result
    # a chamada original nao e reescrita - o shim resolve pelo nome do arquivo
    assert 'fetch("bundle.tar.gz")' in result


def test_inline_assets_leaves_absolute_and_cdn_references_untouched(tmp_path):
    """CDN externo (runtime WASM) fica fora do escopo de R40.5 - vendorizar
    isso e a task 91, nao esta task."""
    html = '<html><head><script src="https://pygame-web.github.io/cdn/pythons.js"></script></head></html>'

    result = inline_assets(html, tmp_path)

    assert result == html


def test_inline_assets_raises_systemexit_when_a_local_reference_is_left_unresolved(tmp_path):
    """Nenhum arquivo `missing.js` existe em `asset_dir` - a referencia nao tem
    como ser embutida, e o build precisa falhar alto em vez de publicar um
    `.html` que parece unico mas ainda depende de um arquivo externo (R40.5)."""
    html = '<html><head><script src="missing.js"></script></head></html>'

    with pytest.raises(SystemExit, match=r"missing\.js"):
        inline_assets(html, tmp_path)


def test_inline_assets_ignores_anchors_and_non_file_href_schemes(tmp_path):
    """Ancoras/`mailto:`/`javascript:` nao sao arquivo local - nao podem
    disparar falso positivo na checagem final (R40.5)."""
    html = '<html><body><a href="#status">status</a><a href="mailto:oi@example.com">email</a></body></html>'

    result = inline_assets(html, tmp_path)

    assert result == html


def test_inline_assets_ignores_a_local_file_never_referenced_by_name(tmp_path):
    """Sem `force_embed`, um arquivo presente no diretorio mas nunca citado
    (nem como `src=`/`href=`, nem como texto solto) fica de fora - a
    heuristica de deteccao por texto simplesmente nao o encontra."""
    (tmp_path / "main.wasm").write_bytes(b"\x00asm-fake-bytes")
    html = "<html><head></head><body></body></html>"

    result = inline_assets(html, tmp_path)

    assert base64.b64encode(b"\x00asm-fake-bytes").decode("ascii") not in result


def test_inline_assets_force_embed_embeds_a_file_never_referenced_by_name(tmp_path):
    """`force_embed` cobre o caso do runtime vendorizado (task 91): `main.wasm`
    nunca aparece como texto solto no `index.html` do `pygbag` - so dentro do
    `main.js` buscado dinamicamente pelo navegador - entao a heuristica de
    texto sozinha nunca o embutiria."""
    (tmp_path / "main.wasm").write_bytes(b"\x00asm-fake-bytes")
    html = "<html><head></head><body></body></html>"

    result = inline_assets(html, tmp_path, force_embed=frozenset({"main.wasm"}))

    assert base64.b64encode(b"\x00asm-fake-bytes").decode("ascii") in result
    assert "window.fetch" in result


def test_inline_pythons_js_rewrites_only_the_src_attribute_to_a_data_uri():
    """O corpo da tag NAO e codigo morto: e o bootstrap Python (`custom_site`)
    que o proprio `pythons.js` le de volta via `script.text`, independente do
    atributo `src` - descartar esse corpo trava o carregamento em
    "Downloading..." pra sempre (achado real da task 91). So o atributo
    `src` vira uma URI `data:`; o corpo da tag fica intacto."""
    html = (
        '<html><script src="https://pygame-web.github.io/cdn/0.9.3/pythons.js" type=module id="site">'
        "#<!--\nimport embed\nasyncio.run(custom_site())\n--></script>"
        '<head><iframe src="https://pygame-web.github.io/cdn/0.9.3/empty.html"></iframe></head></html>'
    )

    result = _inline_pythons_js(html, "console.log('pythons.js real');", main_js=b"main.js bytes")

    assert 'src="https://pygame-web.github.io/cdn/0.9.3/pythons.js"' not in result
    assert "import embed" in result
    assert "asyncio.run(custom_site())" in result
    encoded = base64.b64encode(b"console.log('pythons.js real');").decode("ascii")
    assert f'src="data:text/javascript;base64,{encoded}#pythons.js"' in result
    assert 'src="https://pygame-web.github.io/cdn/0.9.3/empty.html"' in result


def test_inline_pythons_js_src_keeps_the_module_name_substring_for_self_discovery():
    """`pythons.js` acha seu proprio `<script>` em `auto_start()` varrendo
    todos os scripts da pagina e testando `script.src.search("pythons.js") >=
    0` - sem esse fragmento a URI `data:` nunca contem o texto procurado, e o
    boot trava silenciosamente (sem excecao, sem requisicao de rede) - achado
    real da task 91."""
    html = (
        '<html><script src="https://pygame-web.github.io/cdn/0.9.3/pythons.js" type=module id="site">'
        "</script></html>"
    )

    result = _inline_pythons_js(html, "1;", main_js=b"main.js bytes")

    src = result.split('src="')[1].split('"')[0]
    assert src.endswith("pythons.js")


def test_inline_pythons_js_prepends_a_config_seed_script_with_the_executable_data_uri():
    """`pythons.js` calcula `config.executable` concatenando `config.cdn` -
    quebrado pelo mesmo fallback baseado em `url.split(...)` afetado pela URI
    `data:` do proprio script - com `cpython312/main.js`, e carrega o
    resultado via `jsimport()`, um `<script src=...>` criado via DOM que nao
    passa por `window.fetch()` (achado real da task 91). Pre-definir
    `window.config.executable` (usado com `||`, nunca recalculado) evita essa
    segunda camada de URL quebrada."""
    html = (
        '<html><script src="https://pygame-web.github.io/cdn/0.9.3/pythons.js" type=module></script></html>'
    )

    result = _inline_pythons_js(html, "1;", main_js=b"\x00main.js bytes")

    encoded = base64.b64encode(b"\x00main.js bytes").decode("ascii")
    expected_seed = (
        f'<script>window.config = {{"cdn": "./", '
        f'"executable": "data:text/javascript;base64,{encoded}"}};</script>'
    )
    assert expected_seed in result
    assert result.index(expected_seed) < result.index('src="data:text/javascript;base64,')


def test_patch_vtx_js_replaces_the_three_xterm_resolutions_with_data_uris():
    """`vtx.js` normalmente resolve `xterm.js`/`xterm-addon-image.js`/
    `xterm.css` a partir de `window.Module.config.cdn` (ou de um fallback
    fixo pro CDN real) - nem `import()` de modulo ES nem o `<link>` de CSS
    que `vtx.js` cria via DOM passam por `window.fetch()`, entao vendorizar
    os arquivos sozinho nao bastava (achado real da task 91)."""
    vtx_js = (
        'await import(xterm_cdn + "xterm.js")\n'
        'await import(xterm_cdn + "xterm-addon-image.js")\n'
        'cssref.setAttribute("href", xterm_cdn + css)\n'
    )

    result = _patch_vtx_js(vtx_js, b"xterm-js-bytes", b"xterm-addon-bytes", b"xterm-css-bytes")

    assert "xterm_cdn" not in result
    js_encoded = base64.b64encode(b"xterm-js-bytes").decode("ascii")
    addon_encoded = base64.b64encode(b"xterm-addon-bytes").decode("ascii")
    css_encoded = base64.b64encode(b"xterm-css-bytes").decode("ascii")
    assert f'import("data:text/javascript;base64,{js_encoded}")' in result
    assert f'import("data:text/javascript;base64,{addon_encoded}")' in result
    assert f'cssref.setAttribute("href", "data:text/css;base64,{css_encoded}")' in result


def test_patch_pythons_js_replaces_the_relative_vtx_import_with_a_data_uri():
    """`pythons.js` importa `vtx.js` via `import("../vtx.js")`, resolvido
    relativo a URL do proprio `pythons.js` - depois que essa URL vira uma URI
    `data:` (sem hierarquia pra resolver `../` contra), esse import lanca
    `TypeError: Failed to resolve module specifier` (achado real da task
    91). Um especificador `data:` absoluto nao depende de resolucao
    relativa."""
    pythons_js = 'const { WasmTerminal } = await import("../vtx.js")'

    result = _patch_pythons_js(pythons_js, "console.log('vtx.js real');", b"empty-ogg-bytes")

    assert 'import("../vtx.js")' not in result
    encoded = base64.b64encode(b"console.log('vtx.js real');").decode("ascii")
    assert f'import("data:text/javascript;base64,{encoded}")' in result


def test_patch_pythons_js_replaces_the_audio_unlock_expression_with_a_data_uri():
    """`new Audio(config.cdn+"empty.ogg").play()` e midia nativa - nunca passa
    por `window.fetch()`, e `config.cdn` cai no mesmo fallback quebrado pela
    URI `data:` do proprio `pythons.js` - sem esse patch o desbloqueio de
    audio (R38.3) falha pra sempre e o boot trava repetindo "** MEDIA USER
    ACTION REQUIRED **" (achado real da task 91: nao e falta de gesto, e
    `config.cdn` corrompido)."""
    pythons_js = 'MM_play( {auto:1, test:1, media: new Audio(config.cdn+"empty.ogg")} , 1)'

    result = _patch_pythons_js(pythons_js, "1;", b"empty-ogg-bytes")

    assert 'config.cdn+"empty.ogg"' not in result
    encoded = base64.b64encode(b"empty-ogg-bytes").decode("ascii")
    assert f'new Audio("data:audio/ogg;base64,{encoded}")' in result


def test_strip_dead_browserfs_script_removes_the_tag():
    """`browserfs.min.js` 404 real no CDN do `pygbag` (task 91) - a tag e
    removida em vez de vendorizada, pra nao deixar uma requisicao de rede
    (ainda que sempre falhe) no `.html` final (R40.3)."""
    html = (
        "<html><head>"
        '<script src="https://pygame-web.github.io/cdn/0.9.3//browserfs.min.js"></script>'
        "</head><body>conteudo</body></html>"
    )

    result = _strip_dead_browserfs_script(html)

    assert "browserfs.min.js" not in result
    assert "conteudo" in result


def test_ensure_utf8_declared_early_inserts_meta_charset_right_after_the_html_tag():
    """`pythons.js` roda `if (document.characterSet.toLowerCase() !== "utf-8")
    alert(...)` no boot - o `<meta charset="UTF-8">` que o `pygbag` ja gera
    fica la longe, depois do `<script>` inline gigante de `pythons.js`
    (dezenas de MiB em base64 apos `inline_assets`), muito alem dos 1024
    bytes que o pre-scan de encoding do HTML5 examina, entao o navegador
    nunca o ve a tempo (achado real, task 98: reproduzido abrindo
    `dist/BlockyBee.html` no Chrome). A tag precisa cair logo apos `<html>`,
    antes de qualquer `<script>`, pra entrar na janela de pre-scan."""
    html = '<html lang="en-us"><script>console.log("boot");</script><head></head></html>'

    result = _ensure_utf8_declared_early(html)

    assert result.index('<meta charset="utf-8">') < result.index("<script>")
    assert result.startswith('<html lang="en-us"><meta charset="utf-8">')


def test_ensure_utf8_declared_early_only_touches_the_first_html_tag():
    """So a abertura real de `<html>` conta - nao um `<html>` que aparece,
    por exemplo, dentro de texto/comentario embutido mais adiante."""
    html = "<html><body>texto com &lt;html&gt; escapado</body></html>"

    result = _ensure_utf8_declared_early(html)

    assert result.count('<meta charset="utf-8">') == 1
    assert "&lt;html&gt;" in result


def test_vendor_runtime_assets_downloads_only_files_missing_from_the_cache(tmp_path, monkeypatch):
    """Uma segunda execucao com o mesmo diretorio de cache nao acessa rede
    (R40.2) - so os arquivos ainda ausentes disparam `download`."""
    monkeypatch.setattr(build_web.pygbag, "__version__", build_web._PYGBAG_VERSION)
    already_cached = build_web._RUNTIME_MANIFEST[0]
    (tmp_path / already_cached).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / already_cached).write_bytes(b"ja-esta-no-cache")

    downloaded = []

    def fake_download(url, dest):
        downloaded.append(url)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"baixado-agora")

    vendored = vendor_runtime_assets(tmp_path, download=fake_download)

    assert len(downloaded) == len(build_web._RUNTIME_MANIFEST) - 1
    assert all(build_web._PYGBAG_CDN + already_cached not in url for url in downloaded)
    assert (tmp_path / already_cached).read_bytes() == b"ja-esta-no-cache"
    assert set(vendored) == {Path(entry).name for entry in build_web._RUNTIME_MANIFEST}


def test_vendor_runtime_assets_raises_systemexit_on_pygbag_version_mismatch(tmp_path, monkeypatch):
    """Um `pygbag` instalado com versao diferente da que o manifesto foi
    validado contra tem que falhar alto, nunca baixar silenciosamente o
    arquivo errado (task 91)."""
    monkeypatch.setattr(build_web.pygbag, "__version__", "9.9.9")

    def fail_if_called(url, dest):
        raise AssertionError("nao deveria tentar baixar com versao incompativel")

    with pytest.raises(SystemExit, match=r"9\.9\.9"):
        vendor_runtime_assets(tmp_path, download=fail_if_called)
