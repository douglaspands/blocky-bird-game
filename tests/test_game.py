import pygame

from src import config, render, viewport
from src import score as score_module
from src.config import PIPE_W
from src.game import Game, GameState
from tests.fakes import FakeRenderer


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


# --- persistencia do recorde fora do frame (task 60, R27.5) ------------------------


def _writes(monkeypatch) -> list[int]:
    """Registra cada gravacao em disco do recorde, deixando-a acontecer de verdade.

    Espionar `score.save_highscore` — e nao so olhar o arquivo — e o que separa "nao
    gravou" de "gravou o mesmo valor duas vezes": R27.5 e sobre a *chamada de sistema*
    dentro do frame, nao sobre o conteudo do arquivo.
    """
    written: list[int] = []
    original = score_module.save_highscore

    def spy(highscore: int, path=None) -> None:
        written.append(highscore)
        original(highscore, path)

    monkeypatch.setattr(score_module, "save_highscore", spy)
    return written


def _beat_the_record(game: Game) -> None:
    """Poe a abelha logo depois da primeira coluna e roda um frame: +1 ponto."""
    pipe = game.pipes.pipes[0]
    game.bird.pos.x = pipe.x + PIPE_W + 1
    game.bird.pos.y = pipe.gap_y
    game.bird.vel_y = 0
    game.update()


def _crash(game: Game) -> None:
    """Deixa a abelha cair ate bater no chao, levando a partida ao GAME_OVER."""
    frames = 0
    while game.state == GameState.JOGANDO and frames < 2000:
        game.update()
        frames += 1
    assert game.state == GameState.GAME_OVER


def test_beating_the_record_while_playing_does_not_touch_the_disk(monkeypatch):
    """O coracao de R27.5: gravar arquivo e chamada de sistema sincrona, e a cauda de
    latencia dela nao depende do jogo. Em JOGANDO ela sai do frame."""
    written = _writes(monkeypatch)
    game = _make_game()
    game._flap_action()

    _beat_the_record(game)

    assert game.score == 1
    assert game.highscore == 1  # o recorde ja subiu na memoria
    assert written == []  # mas nada foi para o disco
    assert score_module.load_highscore() == 0


def test_no_disk_write_happens_during_a_whole_played_round(monkeypatch):
    """A mesma regra ao longo de uma partida inteira, e nao so no frame que pontua:
    R27.5 proibe escrita em disco *enquanto* o estado e JOGANDO."""
    written = _writes(monkeypatch)
    game = _make_game()
    game._flap_action()
    for _ in range(6):
        _beat_the_record(game)
        game.pipes.pipes[0].scored = False  # forca a proxima passagem a pontuar de novo

    assert game.score >= 6, "ancora: a partida pontuou de verdade"
    assert game.state == GameState.JOGANDO
    assert written == []


def test_reaching_game_over_writes_the_record(monkeypatch):
    """O fim da partida e o primeiro dos dois momentos em que a gravacao acontece."""
    written = _writes(monkeypatch)
    game = _make_game()
    game._flap_action()
    _beat_the_record(game)
    assert written == []  # ancora: ate aqui nada tinha sido gravado

    _crash(game)

    assert written == [game.highscore]
    assert score_module.load_highscore() == game.highscore


def test_going_to_the_background_writes_a_pending_record(monkeypatch):
    """O segundo momento, e o que preserva a garantia de R4.3/R16.4: o Android avisa
    antes de encerrar, e o aviso chega como `APP_WILLENTERBACKGROUND`."""
    written = _writes(monkeypatch)
    game = _make_game()
    game._flap_action()
    _beat_the_record(game)
    assert written == []

    pygame.event.post(pygame.event.Event(pygame.APP_WILLENTERBACKGROUND))
    game.handle_events()

    assert written == [1]
    assert score_module.load_highscore() == 1
    assert game.state == GameState.PAUSADO  # e continua pausando, como antes (R16.1)


def test_going_to_the_background_while_paused_still_writes(monkeypatch):
    """A gravacao nao pode ficar pendurada no estado JOGANDO: quem pausou depois de
    bater o recorde e so entao trocou de app perderia o recorde."""
    written = _writes(monkeypatch)
    game = _make_game()
    game._flap_action()
    _beat_the_record(game)
    game._toggle_pause()
    assert game.state == GameState.PAUSADO

    pygame.event.post(pygame.event.Event(pygame.APP_WILLENTERBACKGROUND))
    game.handle_events()

    assert written == [1]


def test_going_to_the_background_without_a_new_record_writes_nothing(monkeypatch):
    """Sem recorde novo nao ha o que gravar — nem na ida para segundo plano."""
    written = _writes(monkeypatch)
    game = _make_game()
    game.highscore = 50
    game._flap_action()
    _beat_the_record(game)
    assert game.score == 1  # abaixo do recorde: nada ficou pendente

    pygame.event.post(pygame.event.Event(pygame.APP_WILLENTERBACKGROUND))
    game.handle_events()

    assert written == []


def test_the_record_is_written_once_and_not_again(monkeypatch):
    """Depois do GAME_OVER a marca de pendente cai: ir para segundo plano em seguida
    nao repete a gravacao."""
    written = _writes(monkeypatch)
    game = _make_game()
    game._flap_action()
    _beat_the_record(game)
    _crash(game)
    assert len(written) == 1

    pygame.event.post(pygame.event.Event(pygame.APP_WILLENTERBACKGROUND))
    game.handle_events()

    assert len(written) == 1


def test_leaving_the_loop_writes_a_record_from_an_abandoned_round(monkeypatch):
    """Fechar a janela (ou sair com BACK) durante uma partida em que o recorde caiu:
    sem esta gravacao, o recorde iria embora com o processo."""
    written = _writes(monkeypatch)
    # `run()` encerra o pygame ao sair, e a suite compartilha uma unica sessao entre
    # todos os testes: sem este duble, o encerramento aqui derrubaria os subsistemas
    # dos testes seguintes.
    monkeypatch.setattr(pygame, "quit", lambda: None)
    game = _make_game()
    game._flap_action()
    _beat_the_record(game)
    game.running = False

    game.run()  # o laco nao roda nenhum frame; so a saida

    assert written == [1]
    assert score_module.load_highscore() == 1


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


def test_renderer_uses_the_computed_canvas():
    """O renderizador e criado com o canvas logico, nao com a area jogavel: a janela
    padrao do desktop e 960x720, mais larga que os 480x720 de mundo, para as
    faixas laterais aparecerem sem redimensionar nada (R23.7). O `config` passa a
    resolver as dimensoes pelo viewport ativo (task 45)."""
    game = _make_game()
    assert game.viewport.canvas == viewport.DESKTOP_WINDOW
    assert game.renderer.size == (config.screen_w(), config.screen_h())
    assert game.viewport.play.size == (viewport.PLAY_W, viewport.PLAY_H)


def test_the_game_draws_a_whole_frame_through_the_renderer():
    """Nenhum modulo de desenho recebe mais uma `Surface`: o frame inteiro sai em
    chamadas do renderizador, e termina publicado (R26.4)."""
    game = _make_game()
    game.renderer = FakeRenderer(game.viewport.canvas)
    game.draw()

    fake = game.renderer
    assert fake.calls[-1] == ("present",)
    assert fake.drawn("sky"), "o gradiente de ceu do bioma"
    assert fake.drawn("bee"), "a abelha rotacionada"
    assert fake.drawn("mute_icon"), "o botao de mudo"
    assert fake.drawn("band"), "as faixas laterais do canvas 960x720"


def test_the_side_bands_are_drawn_after_the_pipes():
    """A ordem e o mecanismo de R24.4: a faixa e opaca e tem que cobrir a coluna que
    ainda nao entrou na area jogavel (design secao 32.6)."""
    game = _make_game()
    game.renderer = FakeRenderer(game.viewport.canvas)
    game.draw()

    kinds = [key for key, _ in game.renderer.draws]
    is_pipe = [isinstance(key, tuple) and key[0] in ("pipe_top", "pipe_bottom") for key in kinds]
    assert any(is_pipe), "ancora: ha coluna nesta tela para a faixa cobrir"
    last_pipe = max(i for i, pipe in enumerate(is_pipe) if pipe)
    first_band = min(i for i, key in enumerate(kinds) if isinstance(key, tuple) and key[0] == "band")
    assert first_band > last_pipe


def test_bird_starts_inside_the_play_area(monkeypatch):
    """A abelha nasce a um quarto da largura e no meio da ALTURA JOGAVEL — num
    celular alongado, o canvas jogaria o ponto de partida para dentro da faixa de
    ceu (R24.1, R25.1)."""
    monkeypatch.setattr("src.viewport.is_android", lambda: True)
    monkeypatch.setattr(pygame.display, "get_desktop_sizes", lambda: [(1080, 2400)])
    game = _make_game()
    play = game.viewport.play
    assert (game.bird.pos.x, game.bird.pos.y) == (play.x + play.width // 4, play.y + play.height // 2)
    assert play.contains(game.bird.rect)


def test_android_display_is_fullscreen_at_native_resolution(monkeypatch):
    """No Android o display vai a tela cheia na resolucao nativa (R23.3), e o canvas
    recebe a proporcao do aparelho — o que elimina a barra preta nos quatro lados da
    v2 (R23.1) sem mexer na area jogavel (R24.1)."""
    monkeypatch.setattr("src.viewport.is_android", lambda: True)
    monkeypatch.setattr("src.game.is_android", lambda: True)
    monkeypatch.setattr(pygame.display, "get_desktop_sizes", lambda: [(1080, 2400)])

    created: list[tuple] = []
    original = render.create

    def spy(canvas, window, **kwargs):
        created.append((canvas, window, kwargs))
        return original(canvas, window, **kwargs)

    monkeypatch.setattr(render, "create", spy)
    game = _make_game()

    assert game.viewport.canvas == (480, 1067)
    assert game.viewport.play.size == (viewport.PLAY_W, viewport.PLAY_H)
    canvas, window, kwargs = created[0]
    assert canvas == (480, 1067)
    assert window == (1080, 2400)  # a janela e a tela nativa do aparelho
    assert kwargs["fullscreen"] is True
