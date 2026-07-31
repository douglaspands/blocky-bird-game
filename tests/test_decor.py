"""Parallax de fundo, verificado pelas chamadas de desenho (R7.4, R25.5)."""

from src import config
from src.decor import _LAYERS, DecorManager
from src.viewport import compute
from tests.fakes import FakeRenderer


def _all_rects(renderer: FakeRenderer):
    """Retangulos de tudo que foi desenhado, seja preenchimento ou imagem."""
    return [rect for _, rect in renderer.fills] + [rect for _, rect in renderer.draws]


def test_draw_tiles_across_the_whole_canvas_width():
    """Numa tela mais larga que a area jogavel, o parallax tem que ladrilhar ate a
    borda do canvas — parar nos 480px de mundo deixaria a extensao vazia (R25.5)."""
    for decor_id in _LAYERS:
        renderer = FakeRenderer((1280, 720))
        DecorManager().draw(renderer, decor_id)
        rects = _all_rects(renderer)
        assert rects, decor_id
        assert max(r.right for r in rects) > 1280 - 220, decor_id  # chegou perto da borda
        assert min(r.left for r in rects) <= 0, decor_id  # comecou antes dela


def test_draw_anchors_ground_relative_decor_to_the_play_area():
    """Colinas, poças de lava e pilares assentam na linha do chao da area jogavel, nao
    na base do canvas — senao afundariam na faixa decorativa de baixo (R25.1)."""
    config.set_viewport(compute(1080, 2400))
    ground_y = config.ground_y()
    assert ground_y < config.screen_h() - 96  # ha faixa de chao abaixo

    for decor_id in ("overworld", "nether"):
        renderer = FakeRenderer(config.viewport().canvas)
        DecorManager().draw(renderer, decor_id)
        near_rects = [r for r in _all_rects(renderer) if r.bottom > config.play().centery]
        assert near_rects, decor_id
        # a camada proxima assenta na linha do chao, e nunca desce ate a base do canvas
        assert max(r.bottom for r in near_rects) == ground_y, decor_id


def test_non_rectangular_shapes_become_reusable_images():
    """Estalactite (triangulo) e poça de lava (elipse) nao cabem num `fill`.

    Viram imagem chaveada pelo tamanho sorteado, entao o numero de imagens
    construidas fica muito abaixo do numero de formas desenhadas."""
    for decor_id, tag in (("cave", "stalactite"), ("nether", "lava_pool")):
        renderer = FakeRenderer((1280, 720))
        manager = DecorManager()
        for _ in range(40):
            manager.update(3.0)
            manager.draw(renderer, decor_id)
        drawn = renderer.drawn(tag)
        assert len(drawn) > len(renderer._images), decor_id
