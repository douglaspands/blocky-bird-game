from src import score as score_module
from src.config import PIPE_W
from src.game import Game, GameState


def _make_game():
    return Game()


def test_starts_in_pronto_state():
    game = _make_game()
    assert game.state == GameState.PRONTO


def test_flap_in_pronto_transitions_to_jogando():
    game = _make_game()
    game._flap_action()
    assert game.state == GameState.JOGANDO


def test_score_increments_once_per_pipe():
    game = _make_game()
    game._flap_action()
    pipe = game.pipes.pipes[0]
    game.bird.pos.x = pipe.x + PIPE_W + 1
    game.bird.pos.y = pipe.gap_y
    game.bird.vel_y = 0

    game.update()
    assert game.score == 1
    assert pipe.scored is True

    game.update()
    assert game.score == 1


def test_collision_with_ground_ends_round():
    game = _make_game()
    game._flap_action()
    frames = 0
    while game.state == GameState.JOGANDO and frames < 2000:
        game.update()
        frames += 1
    assert game.state == GameState.GAME_OVER
    assert len(game.particles.particles) > 0


def test_pause_toggle_freezes_physics():
    game = _make_game()
    game._flap_action()
    game._toggle_pause()
    assert game.state == GameState.PAUSADO
    bird_y_before = game.bird.pos.y
    pipe_x_before = game.pipes.pipes[0].x
    game.update()
    assert game.bird.pos.y == bird_y_before
    assert game.pipes.pipes[0].x == pipe_x_before


def test_highscore_saved_incrementally_mid_round():
    """O recorde deve ser gravado no instante em que e superado, nao so no
    GAME_OVER — um encerramento abrupto do app (Android) nao pode perder o
    recorde ja alcancado em uma partida ainda em curso (R4.3, R16.4)."""
    game = _make_game()
    game._flap_action()
    assert game.highscore == 0

    pipe = game.pipes.pipes[0]
    game.bird.pos.x = pipe.x + PIPE_W + 1
    game.bird.pos.y = pipe.gap_y
    game.bird.vel_y = 0

    game.update()
    assert game.score == 1
    assert game.highscore == 1
    assert game.state == GameState.JOGANDO  # a rodada ainda nao terminou

    # ja deve estar em disco, nao so na memoria do objeto Game
    assert score_module.load_highscore() == 1


def test_highscore_not_saved_again_below_record():
    game = _make_game()
    game._flap_action()
    game.highscore = 50
    game.score = 3

    pipe = game.pipes.pipes[0]
    game.bird.pos.x = pipe.x + PIPE_W + 1
    game.bird.pos.y = pipe.gap_y
    game.bird.vel_y = 0

    game.update()  # score vira 4, ainda abaixo do recorde de 50
    assert game.score == 4
    assert game.highscore == 50
    assert score_module.load_highscore() == 0  # nada foi gravado


def test_flap_in_game_over_resets_to_pronto():
    game = _make_game()
    game._flap_action()
    frames = 0
    while game.state == GameState.JOGANDO and frames < 2000:
        game.update()
        frames += 1
    assert game.state == GameState.GAME_OVER

    game._flap_action()
    assert game.state == GameState.PRONTO
    assert game.score == 0
