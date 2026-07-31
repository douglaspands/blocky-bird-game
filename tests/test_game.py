import pygame

from src import config, viewport
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


def _post_back():
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_AC_BACK))


def test_back_in_pronto_quits():
    game = _make_game()
    _post_back()
    game.handle_events()
    assert game.running is False


def test_back_in_jogando_pauses_without_quitting():
    game = _make_game()
    game._flap_action()
    assert game.state == GameState.JOGANDO
    _post_back()
    game.handle_events()
    assert game.state == GameState.PAUSADO
    assert game.running is True


def test_back_in_pausado_quits():
    game = _make_game()
    game._flap_action()
    game._toggle_pause()
    assert game.state == GameState.PAUSADO
    _post_back()
    game.handle_events()
    assert game.running is False


def test_back_in_game_over_quits():
    game = _make_game()
    game._flap_action()
    frames = 0
    while game.state == GameState.JOGANDO and frames < 2000:
        game.update()
        frames += 1
    assert game.state == GameState.GAME_OVER
    _post_back()
    game.handle_events()
    assert game.running is False


def test_tap_on_mute_icon_toggles_mute_without_side_effects():
    """Tocar no icone de mudo na tela PRONTO nao deve iniciar o jogo, e em
    GAME_OVER nao deve reiniciar a partida (R15.4)."""
    from src import ui

    game = _make_game()
    assert game.sounds.muted is False
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=ui.mute_icon_rect().center))
    game.handle_events()
    assert game.sounds.muted is True
    assert game.state == GameState.PRONTO  # nao voou, nao iniciou a partida


def test_flap_resumes_from_pausado_without_flapping_bird():
    """Sem isso, quem pausa via BACK (sem tecla ESC/P nem botao Start de
    gamepad) fica sem como voltar — essencial p/ controle remoto de TV e p/
    toque no celular (R14.4, R15.5)."""
    game = _make_game()
    game._flap_action()
    game._toggle_pause()
    assert game.state == GameState.PAUSADO
    bird_vel_before = game.bird.vel_y

    game._flap_action()
    assert game.state == GameState.JOGANDO
    assert game.bird.vel_y == bird_vel_before  # nao flapou, so despausou


def test_dpad_left_right_toggle_mute_only_when_pausado():
    game = _make_game()
    game._flap_action()
    assert game.state == GameState.JOGANDO
    assert game.sounds.muted is False

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT))
    game.handle_events()
    assert game.sounds.muted is False  # fora de PAUSADO, D-pad nao muta nada

    game._toggle_pause()
    assert game.state == GameState.PAUSADO
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT))
    game.handle_events()
    assert game.sounds.muted is True

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT))
    game.handle_events()
    assert game.sounds.muted is False


def test_bare_tv_remote_reaches_every_state():
    """Simula um controle remoto de Android TV sem botoes extras: so D-pad
    (setas), botao central (RETURN) e voltar (K_AC_BACK) — sem toque, sem
    tecla M/ESC/P, sem gamepad (R14.4, R15.5)."""

    def press(key):
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))

    game = _make_game()
    assert game.state == GameState.PRONTO

    press(pygame.K_RETURN)  # PRONTO -> JOGANDO
    game.handle_events()
    assert game.state == GameState.JOGANDO

    press(pygame.K_AC_BACK)  # JOGANDO -> PAUSADO
    game.handle_events()
    assert game.state == GameState.PAUSADO

    press(pygame.K_LEFT)  # muta em PAUSADO
    game.handle_events()
    assert game.sounds.muted is True

    press(pygame.K_RETURN)  # PAUSADO -> JOGANDO (despausa)
    game.handle_events()
    assert game.state == GameState.JOGANDO

    # forca fim de jogo para testar GAME_OVER -> PRONTO
    game.bird.pos.x = game.pipes.pipes[0].x
    game.bird.pos.y = 0
    game.bird.vel_y = 0
    game.update()
    assert game.state == GameState.GAME_OVER

    press(pygame.K_RETURN)  # GAME_OVER -> PRONTO
    game.handle_events()
    assert game.state == GameState.PRONTO

    press(pygame.K_AC_BACK)  # PRONTO -> encerra
    game.handle_events()
    assert game.running is False


def test_focus_lost_pauses_during_jogando():
    game = _make_game()
    game._flap_action()
    assert game.state == GameState.JOGANDO
    pygame.event.post(pygame.event.Event(pygame.WINDOWFOCUSLOST))
    game.handle_events()
    assert game.state == GameState.PAUSADO


def test_focus_lost_does_not_auto_resume():
    """Perder o foco de novo enquanto ja pausado nao deve alternar de volta
    para JOGANDO — so um flap/pause explicito do jogador despausa (R16.2)."""
    game = _make_game()
    game._flap_action()
    game._toggle_pause()
    assert game.state == GameState.PAUSADO
    pygame.event.post(pygame.event.Event(pygame.WINDOWFOCUSLOST))
    game.handle_events()
    assert game.state == GameState.PAUSADO


def test_focus_lost_ignored_outside_jogando():
    game = _make_game()
    assert game.state == GameState.PRONTO
    pygame.event.post(pygame.event.Event(pygame.WINDOWFOCUSLOST))
    game.handle_events()
    assert game.state == GameState.PRONTO


def test_app_background_events_also_pause():
    """Cobre os eventos de ciclo de vida do Android, nao so o fallback de
    desktop (R16.1)."""
    game = _make_game()
    game._flap_action()
    assert game.state == GameState.JOGANDO
    pygame.event.post(pygame.event.Event(pygame.APP_WILLENTERBACKGROUND))
    game.handle_events()
    assert game.state == GameState.PAUSADO


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


def test_screen_uses_the_computed_canvas():
    """O display e criado com o canvas logico, nao com a area jogavel: a janela
    padrao do desktop e 960x720, mais larga que os 480x720 de mundo, para as
    faixas laterais aparecerem sem redimensionar nada (R23.7). O `config` passa a
    resolver as dimensoes pelo viewport ativo (task 45)."""
    game = _make_game()
    assert game.viewport.canvas == viewport.DESKTOP_WINDOW
    assert game.screen.get_size() == (config.screen_w(), config.screen_h())
    assert game.viewport.play.size == (viewport.PLAY_W, viewport.PLAY_H)


def test_android_display_is_fullscreen_at_native_resolution(monkeypatch):
    """No Android o display vai a tela cheia na resolucao nativa (R23.3), e o canvas
    recebe a proporcao do aparelho — o que elimina a barra preta nos quatro lados da
    v2 (R23.1) sem mexer na area jogavel (R24.1)."""
    monkeypatch.setattr("src.viewport.is_android", lambda: True)
    monkeypatch.setattr(pygame.display, "get_desktop_sizes", lambda: [(1080, 2400)])
    game = _make_game()
    assert game.viewport.canvas == (480, 1067)
    assert game.viewport.play.size == (viewport.PLAY_W, viewport.PLAY_H)
    assert viewport.display_flags() & pygame.FULLSCREEN
