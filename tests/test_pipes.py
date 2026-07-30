from src import config
from src.config import GAP_MARGIN, GROUND_H, PIPE_SPACING, PIPE_W, SCREEN_H, SCREEN_W
from src.pipes import PipeManager


def test_initial_spawn_is_at_right_edge():
    pm = PipeManager(160, "dirt", "grass_side")
    assert len(pm.pipes) == 1
    assert pm.pipes[0].x == SCREEN_W


def test_gap_is_within_safe_margins():
    pm = PipeManager(160, "dirt", "grass_side")
    pipe = pm.pipes[0]
    assert GAP_MARGIN <= pipe.gap_y <= SCREEN_H - GROUND_H - GAP_MARGIN


def test_new_pipe_freezes_current_gap_size_and_textures():
    pm = PipeManager(160, "dirt", "grass_side")
    assert pm.pipes[0].gap_size == 160
    assert pm.pipes[0].block_main == "dirt"
    assert pm.pipes[0].block_edge == "grass_side"


def test_update_moves_pipes_left_by_speed():
    pm = PipeManager(160, "dirt", "grass_side")
    start_x = pm.pipes[0].x
    pm.update(2.5, 160, "dirt", "grass_side")
    assert pm.pipes[0].x == start_x - 2.5


def test_spawns_new_pipe_at_fixed_spacing():
    pm = PipeManager(160, "dirt", "grass_side")
    while len(pm.pipes) < 2:
        pm.update(2.5, 160, "dirt", "grass_side")
    assert pm.pipes[1].x - pm.pipes[0].x == PIPE_SPACING


def test_existing_pipe_keeps_old_biome_params_after_biome_change():
    pm = PipeManager(160, "dirt", "grass_side")
    first_pipe = pm.pipes[0]
    pm.update(3.0, 145, "stone", "cobblestone")
    assert first_pipe.gap_size == 160
    assert first_pipe.block_main == "dirt"
    assert first_pipe.block_edge == "grass_side"


def test_new_pipe_uses_new_biome_params():
    pm = PipeManager(160, "dirt", "grass_side")
    while len(pm.pipes) < 2:
        pm.update(3.0, 145, "stone", "cobblestone")
    assert pm.pipes[1].gap_size == 145
    assert pm.pipes[1].block_main == "stone"
    assert pm.pipes[1].block_edge == "cobblestone"


def test_pipe_removed_once_fully_off_screen():
    pm = PipeManager(160, "dirt", "grass_side")
    first_pipe = pm.pipes[0]
    frames = 0
    while first_pipe in pm.pipes and frames < 5000:
        pm.update(2.5, 160, "dirt", "grass_side")
        frames += 1
    assert first_pipe not in pm.pipes
    assert first_pipe.x + PIPE_W < 0


def test_gap_size_and_margin_scale_with_dynamic_screen_height(monkeypatch):
    """Aparelho em retrato com mais altura jogavel real (task 39) nao pode ganhar
    espaco de reacao extra de graca — abertura e margem escalam na mesma
    proporcao que SCREEN_H em relacao a BASE_SCREEN_H."""
    monkeypatch.setattr(config, "SCREEN_H", config.BASE_SCREEN_H * 2)

    pm = PipeManager(160, "dirt", "grass_side")
    pipe = pm.pipes[0]

    assert pipe.gap_size == 320
    scaled_margin = GAP_MARGIN * 2
    assert scaled_margin <= pipe.gap_y <= config.SCREEN_H - GROUND_H - scaled_margin
