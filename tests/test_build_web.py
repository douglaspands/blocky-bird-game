"""Testes de `inline_assets` (R40.1, R40.2, R40.5, design.md secao 51).

So a funcao pura e testada aqui, com fixtures sinteticas que reproduzem os tres
padroes de referencia local que um `index.html` real do `pygbag` contem
(`<script src=...>`, `<link href=...>` do icone, e um arquivo binario so
referenciado por nome dentro de outro `<script>`, como o `platform.fopen(...)`
do carregador buscando o pacote de codigo+assets) - a execucao real do
`pygbag --build` fica para a verificacao manual da task 90, cara demais e
dependente de rede para rodar em toda execucao da suite.
"""

import base64

import pytest

from scripts.build_web import inline_assets


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
