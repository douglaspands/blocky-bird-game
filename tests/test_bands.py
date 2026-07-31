"""Faixas decorativas: o jogo desloca para dentro da area jogavel, e o que sobra
vira ceu, chao e paredes de terra (R23.4, R24.1-R24.5, R25.1, R25.2, R25.5, R25.7)."""

import pygame
import pytest

from src import config, decor, textures, ui
from src.bands import SideBands
from src.biome import BIOMES, BiomeManager
from src.bird import Bird
from src.config import BLOCK, GAP_MARGIN, GROUND_H
from src.game import Game, GameState
from src.ground import Ground
from src.pipes import PipeManager
from src.viewport import PLAY_H, PLAY_W, compute

PHONE = (1080, 2400)  # canvas 480x1067: ceu de 251px, chao extra de 96px
WIDE = (1920, 1080)  # canvas 1280x720: faixas laterais de 400px
SQUARE_2_3 = (PLAY_W, PLAY_H)  # sem faixa nenhuma — a geometria da v2


def _use(screen: tuple[int, int]) -> pygame.Rect:
    """Ativa o canvas daquela tela e devolve a area jogavel."""
    config.set_viewport(compute(*screen))
    return config.play()


def test_the_phone_canvas_really_has_both_bands():
    """Ancora dos demais testes: se esta tela deixasse de gerar faixa, eles passariam
    por vacuidade."""
    play = _use(PHONE)
    assert config.viewport().canvas == (480, 1067)
    assert (play.top, play.bottom) == (251, 971)
    assert config.viewport().sky_band.height == 251
    assert config.viewport().ground_band.height == 96


def test_bird_ceiling_is_the_play_top_not_the_canvas_top():
    """A faixa de ceu e decorativa: nao pode dar espaco extra para voar (R24.5)."""
    play = _use(PHONE)
    bird = Bird(play.x, play.top + 10)
    bird.vel_y = -50
    bird.update()
    assert bird.pos.y == play.top
    assert bird.vel_y == 0


def test_bird_ceiling_on_a_2_3_canvas_is_the_v2_ceiling():
    _use(SQUARE_2_3)
    bird = Bird(100, 10)
    bird.vel_y = -50
    bird.update()
    assert bird.pos.y == 0


def test_fall_is_identical_in_both_canvases():
    """Nenhuma constante de fisica depende da tela (R24.2): a trajetoria medida a
    partir do topo da area jogavel e a mesma nas duas proporcoes.

    As velocidades batem bit a bit (nao dependem da posicao); as alturas batem a
    menos de epsilon de float, porque somar o mesmo delta a 200 ou a 451 arredonda
    diferente — e diferenca de representacao, nao de fisica."""
    speeds: list[list[float]] = []
    heights: list[list[float]] = []
    for screen in (SQUARE_2_3, PHONE):
        play = _use(screen)
        bird = Bird(play.x, play.top + 200)
        bird.flap()
        frames = [(bird.update(), (bird.vel_y, bird.pos.y - play.top))[1] for _ in range(120)]
        speeds.append([v for v, _ in frames])
        heights.append([y for _, y in frames])
    assert speeds[0] == speeds[1]
    assert heights[0] == pytest.approx(heights[1])


def test_gap_is_always_inside_the_play_area():
    """Com faixa de ceu, `GAP_MARGIN` sozinho deixaria a abertura cair na decoracao,
    fora do alcance da abelha."""
    play = _use(PHONE)
    gap_size = 160
    pm = PipeManager(gap_size, "dirt", "grass_side")
    for _ in range(200):
        pm.update(3.0, gap_size, "dirt", "grass_side")
    assert len(pm.pipes) > 1
    for pipe in pm.pipes:
        assert play.top + GAP_MARGIN <= pipe.gap_y <= config.ground_y() - GAP_MARGIN
        assert pipe.gap_y - gap_size / 2 >= play.top
        assert pipe.gap_y + gap_size / 2 <= config.ground_y()


def test_pipes_are_discarded_at_the_play_left_edge():
    play = _use((1920, 1080))  # canvas 1280x720: area jogavel comeca em x=400
    assert play.left == 400
    pm = PipeManager(160, "dirt", "grass_side")
    pm.pipes[0].x = play.left + 1
    pm.update(0.0, 160, "dirt", "grass_side")
    assert pm.pipes and pm.pipes[0].x == play.left + 1

    pm.pipes[0].x = play.left - config.PIPE_W - 1
    pm.update(0.0, 160, "dirt", "grass_side")
    assert all(p.x >= play.left - config.PIPE_W for p in pm.pipes)


def test_ground_line_sits_on_the_play_bottom_not_the_canvas_bottom():
    play = _use(PHONE)
    assert config.ground_y() == play.bottom - GROUND_H
    assert config.ground_y() < config.screen_h() - GROUND_H  # sobra faixa de chao


def test_ground_fills_the_decorative_band_below_the_play_area():
    """A fileira extra e consequencia direta do canvas mais alto: `Ground.draw` ja
    enche de `ground_y()` ate a base do canvas (R25.1)."""
    _use(PHONE)
    surface = pygame.Surface(config.viewport().canvas)
    surface.fill((0, 0, 0))
    Ground().draw(surface, textures.generate_all(BLOCK), "dirt", "grass_side")
    band = config.viewport().ground_band
    assert surface.get_at((BLOCK, band.centery))[:3] != (0, 0, 0)
    assert surface.get_at((BLOCK, config.screen_h() - 1))[:3] != (0, 0, 0)


def test_hud_score_moves_into_the_sky_band():
    """Com faixa de ceu, a pontuacao sai da area de jogo e vai para ela (R25.7)."""
    play = _use(PHONE)
    center = ui.hud_score_center()
    assert center == (play.centerx, config.viewport().sky_band.centery)
    assert center[1] < play.top


def test_hud_score_stays_in_the_play_area_without_a_sky_band():
    """Numa tela 2:3 cai exatamente onde caia na v2 (nao-regressao)."""
    _use(SQUARE_2_3)
    assert ui.hud_score_center() == (PLAY_W // 2, ui.HUD_SCORE_MARGIN)


def test_hud_score_does_not_split_a_short_sky_band():
    """Celular 16:9: a faixa tem 37px e nao comporta o texto — melhor ficar inteiro
    na area de jogo do que metade em cada lado."""
    play = _use((1080, 1920))
    assert config.viewport().sky_band.height == 37
    assert ui.hud_score_center() == (play.centerx, play.top + ui.HUD_SCORE_MARGIN)


def test_mute_icon_sits_in_the_sky_band_when_it_fits():
    _use(PHONE)
    rect = ui.mute_icon_rect()
    assert config.viewport().sky_band.contains(rect)
    assert rect.right == config.screen_w() - ui.MUTE_ICON_MARGIN


def test_mute_icon_drops_into_the_play_area_when_the_band_is_too_short():
    play = _use((1080, 1920))
    assert ui.mute_icon_rect().top == play.top + ui.MUTE_ICON_MARGIN


def test_mute_icon_on_a_2_3_canvas_is_where_it_was_in_v2():
    _use(SQUARE_2_3)
    assert ui.mute_icon_rect() == pygame.Rect(PLAY_W - 14 - 40, 14, 40, 40)


def test_state_screens_are_anchored_to_the_play_area(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ready/pausa/game over acompanham a area jogavel: numa tela muito alongada,
    ancorar no canvas jogaria os textos para dentro da faixa de ceu."""
    play = _use((1080, 2800))
    assert play.top > 0
    centers: list[tuple[int, int]] = []
    original = ui.draw_text

    def spy(surf, text, center, base_size=12, color=(255, 255, 255)):
        centers.append(center)
        original(surf, text, center, base_size=base_size, color=color)

    monkeypatch.setattr(ui, "draw_text", spy)
    surface = pygame.Surface(config.viewport().canvas)
    ui.draw_ready_screen(surface, 10)
    ui.draw_paused_overlay(surface)
    ui.draw_game_over_screen(surface, 3, 10)

    assert centers
    for _, y in centers:
        assert play.top <= y <= play.bottom


# --- Faixas laterais (task 47) ------------------------------------------------


def _drawn_band(screen: tuple[int, int], biome_index: int = 0) -> pygame.Surface:
    """Desenha as faixas laterais sobre um fundo conhecido e devolve o canvas."""
    _use(screen)
    surface = pygame.Surface(config.viewport().canvas)
    surface.fill((255, 0, 255))  # magenta: qualquer pixel remanescente denuncia buraco
    SideBands().draw(surface, textures.generate_all(BLOCK), BIOMES[biome_index])
    return surface


def test_pipe_spawns_at_the_play_right_edge():
    """Na borda da area jogavel, nao do canvas: e o que iguala o tempo de reacao em
    qualquer proporcao (R24.3)."""
    play = _use(WIDE)
    assert play.right < config.screen_w()
    assert PipeManager(160, "dirt", "grass_side").pipes[0].x == play.right


def test_time_from_spawn_to_bird_is_the_same_in_both_canvases():
    """O jogador nao pode ganhar tempo de reacao por jogar numa tela mais larga
    (R24.3)."""
    frames = []
    for screen in (SQUARE_2_3, WIDE):
        play = _use(screen)
        pm = PipeManager(160, "dirt", "grass_side")
        bird_x = play.x + play.width // 4
        count = 0
        while pm.pipes[0].x > bird_x:
            pm.pipes[0].x -= 2.5
            count += 1
        frames.append(count)
    assert frames[0] == frames[1]


@pytest.mark.parametrize("biome_index", range(len(BIOMES)), ids=[b.id for b in BIOMES])
def test_side_band_is_opaque_over_its_whole_height(biome_index):
    """Opacidade nao e enfeite: e o mecanismo que esconde a coluna que ainda nao
    entrou na area jogavel (R24.4)."""
    surface = _drawn_band(WIDE, biome_index)
    vp = config.viewport()
    for band in (vp.left_band, vp.right_band):
        assert band.width > 0
        for y in range(0, band.height, 17):
            for x in (band.left, band.centerx, band.right - 1):
                assert surface.get_at((x, y))[:3] != (255, 0, 255)


def test_side_bands_are_absent_on_a_2_3_canvas():
    """Sem sobra horizontal nao ha o que cobrir — e o desenho nao pode inventar."""
    surface = _drawn_band(SQUARE_2_3)
    assert surface.get_at((0, 0))[:3] == (255, 0, 255)
    assert surface.get_at((PLAY_W - 1, PLAY_H - 1))[:3] == (255, 0, 255)


def test_band_ground_line_matches_the_play_ground_line():
    """A fileira de borda cai exatamente em `ground_y()`, para a terra parecer
    continua de uma borda a outra."""
    surface = _drawn_band(WIDE)
    tex = textures.generate_all(BLOCK)["grass_side"]
    band_x = config.viewport().left_band.centerx
    for dy in range(0, BLOCK, 7):
        assert surface.get_at((band_x, config.ground_y() + dy))[:3] == tex.get_at((band_x % BLOCK, dy))[:3]


def test_side_bands_hide_a_pipe_that_has_not_entered_the_play_area(monkeypatch: pytest.MonkeyPatch) -> None:
    """R24.4 por inteiro: a coluna nasce em `play.right`, cai dentro da faixa
    direita, e nenhum pixel dela sobrevive ao desenho da faixa.

    A segunda metade do teste desliga a faixa e confirma que sem ela a coluna
    apareceria — sem isso o teste passaria mesmo que a coluna nunca tivesse sido
    desenhada ali, e nao provaria nada sobre a oclusao."""
    game = Game()
    config.set_viewport(compute(*WIDE))
    game.viewport = config.viewport()
    game.screen = pygame.Surface(game.viewport.canvas)
    game.reset()
    game.state = GameState.JOGANDO

    pipe = game.pipes.pipes[0]
    assert pipe.x == game.viewport.play.right  # a coluna esta mesmo sob a faixa
    band = game.viewport.right_band
    samples = [(x, y) for y in range(0, band.height, 13) for x in range(band.left, band.right, 11)]

    def frame(pipes: list) -> pygame.Surface:
        game.pipes.pipes = pipes
        game.draw()
        return game.screen.copy()

    covered, covered_empty = frame([pipe]), frame([])
    assert all(covered.get_at(p) == covered_empty.get_at(p) for p in samples)

    monkeypatch.setattr(SideBands, "draw", lambda *args, **kwargs: None)
    naked, naked_empty = frame([pipe]), frame([])
    assert any(naked.get_at(p) != naked_empty.get_at(p) for p in samples)


def test_sky_parallax_and_ground_span_the_whole_canvas_width():
    """Ceu, parallax e chao vao de borda a borda mesmo onde a faixa lateral vai
    cobri-los, para nao haver emenda visivel (R25.5)."""
    _use(WIDE)
    canvas_w = config.screen_w()
    surface = pygame.Surface(config.viewport().canvas)
    surface.fill((255, 0, 255))
    BiomeManager().draw_background(surface)
    decor.DecorManager().draw(surface, "overworld")
    Ground().draw(surface, textures.generate_all(BLOCK), "dirt", "grass_side")
    for x in (0, canvas_w // 2, canvas_w - 1):
        assert surface.get_at((x, 10))[:3] != (255, 0, 255)  # ceu
        assert surface.get_at((x, config.ground_y() + 10))[:3] != (255, 0, 255)  # chao
