import random

import pygame
import pytest

from src import config, perf, render, viewport
from src import score as score_module
from src.config import BLOCK, FPS, PIPE_W
from src.game import MAX_FRAME_MS, MAX_STEPS, STEP_MS, Game, GameState
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


def test_starts_with_no_last_score():
    """Primeira vez: nenhuma partida terminou ainda nesta execucao (R36.2)."""
    game = _make_game()
    assert game.last_score is None


def _play_to_game_over(game) -> None:
    game._flap_action()
    frames = 0
    while game.state == GameState.JOGANDO and frames < 2000:
        game.update()
        frames += 1
    assert game.state == GameState.GAME_OVER


def test_last_score_is_captured_when_returning_from_game_over():
    """A pontuacao da partida que acabou vira `last_score` so quando o jogador volta
    para PRONTO, e o `reset()` dessa transicao nao apaga o valor gravado (R36.1)."""
    game = _make_game()
    _play_to_game_over(game)
    finished_score = game.score

    game._flap_action()  # GAME_OVER -> PRONTO

    assert game.state == GameState.PRONTO
    assert game.last_score == finished_score
    assert game.score == 0  # a partida nova comeca zerada, como sempre


def test_last_score_does_not_survive_a_fresh_game_instance():
    """R36.3: e memoria de sessao — uma nova instancia (o analogo mais proximo de um
    reinicio do aplicativo neste ambiente) comeca sem nenhuma partida anterior."""
    game = _make_game()
    _play_to_game_over(game)
    game._flap_action()  # GAME_OVER -> PRONTO
    assert game.last_score is not None

    assert _make_game().last_score is None


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

    # forca fim de jogo para testar GAME_OVER -> PRONTO. Contra o CHAO, e nao contra a
    # coluna: a abertura e sorteada, e uma que caia bem no alto deixa a metade de cima
    # com altura quase zero — a abelha em y=0 passaria sem colidir, e o teste
    # dependeria do sorteio (e, portanto, da ordem da suite).
    game.bird.pos.y = config.ground_y() + BLOCK
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


# --- timestep fixo (task 63, R28) -------------------------------------------------


def _count_steps(game: Game, monkeypatch) -> list[int]:
    """Troca `update` por um contador que ainda simula: conta sem mudar o que roda."""
    steps: list[int] = []
    original = game.update

    def counted() -> None:
        steps.append(1)
        original()

    monkeypatch.setattr(game, "update", counted)
    return steps


def test_a_sixty_fps_frame_advances_exactly_one_step(monkeypatch):
    """O caso normal, e o que mantem o jogo identico ao da v2 (R28.1, R28.4)."""
    game = _make_game()
    steps = _count_steps(game, monkeypatch)

    assert game.simulate(STEP_MS) == 1
    assert len(steps) == 1


def test_a_thirty_fps_frame_advances_two_steps():
    """O jogo nao fica em camera lenta num aparelho que so entrega metade dos quadros:
    o frame dura o dobro, e ele compra dois passos (R28.2)."""
    game = _make_game()

    assert game.simulate(1000 / 30) == 2


def test_the_remainder_of_a_frame_is_carried_and_not_thrown_away(monkeypatch):
    """`Clock.tick` devolve inteiros: a 60 FPS reais alternam 16 e 17 ms, e nenhum dos
    dois e um passo exato de 16,67. Descartar a sobra faria o jogo correr devagar num
    aparelho que nao perdeu quadro nenhum — o acumulador e o que impede isso."""
    game = _make_game()
    steps = _count_steps(game, monkeypatch)

    assert game.simulate(16) == 0, "16 ms nao chegam a um passo de 16,67"
    assert game.simulate(16) == 1, "mas os 32 ms dos dois frames sim: o primeiro nao se perdeu"

    for _ in range(58):
        game.simulate(16)

    # 60 frames de 16 ms sao 960 ms de tempo real, que compram 57 passos e sobram 10 ms
    assert len(steps) == int(960 / STEP_MS)
    assert game.accumulator == pytest.approx(960 - 57 * STEP_MS)


def test_a_long_stall_is_clamped_instead_of_becoming_a_leap():
    """Um app que volta do segundo plano devolve um delta de segundos. Sem o corte, o
    jogo *pularia* para frente — a abelha atravessaria a tela entre dois quadros
    (R28.3)."""
    game = _make_game()

    assert game.simulate(5000) == MAX_STEPS
    assert game.accumulator == 0.0


def test_a_stall_leaves_no_debt_for_the_next_frame():
    """Guardar o atraso irrecuperavel seria a mesma espiral, so que mais lenta: o
    frame seguinte comecaria ja devendo e pediria o teto de novo, indefinidamente."""
    game = _make_game()
    game.simulate(5000)

    assert game.simulate(STEP_MS) == 1, "o frame seguinte volta ao ritmo normal"


# o menor valor da lista e 84 ms, e nao os 83,33 exatos de `MAX_STEPS * STEP_MS`: na
# igualdade a soma de cinco decrementos de 16,666... cai um ulp abaixo do quinto passo
# e o teto nao e batido. Nao e defeito — e a fronteira em ponto flutuante, e afirmar
# sobre ela seria afirmar sobre o arredondamento, nao sobre o requisito.
@pytest.mark.parametrize("frame_ms", [84.0, 100.0, MAX_FRAME_MS, 1000.0, 60_000.0])
def test_no_frame_duration_can_advance_more_than_the_ceiling(frame_ms):
    """A propriedade que R28.3 realmente pede, dita sobre qualquer duracao: nenhum
    frame, por mais longo que seja, faz o jogo pular. Um minuto parado avanca o mesmo
    que 83 ms."""
    game = _make_game()

    assert game.simulate(frame_ms) == MAX_STEPS
    assert game.accumulator == 0.0


def test_the_two_defences_are_consistent_and_the_inner_one_binds_first():
    """R28.3 pede o corte do tempo decorrido; R28.2 pede o teto de passos. Hoje o teto
    morde primeiro — 5 passos sao 83 ms, bem abaixo dos 250 ms do corte —, e portanto e
    ele que cumpre os dois: batido o teto, o atraso restante e descartado de qualquer
    forma. O corte de tempo e a rede que passa a valer se o teto subir, e este teste e
    o que avisa quando isso acontecer, em vez de deixar as duas constantes se
    contradizerem em silencio."""
    assert MAX_STEPS * STEP_MS < MAX_FRAME_MS


def test_the_number_of_steps_per_frame_has_a_ceiling():
    """R28.2: se um passo passar a custar mais que 1/60 s, cada frame pediria mais
    passos do que consegue rodar. O teto e o que faz o jogo continuar respondendo."""
    game = _make_game()

    for _ in range(10):
        assert game.simulate(MAX_FRAME_MS) == MAX_STEPS


def _snapshot(game: Game) -> tuple:
    """Estado observavel de uma partida: fisica, obstaculos, animacao e progressao.

    R28.4 fala das tres coisas — fisica, temporizadores de animacao e progressao de
    biomas —, entao as tres entram aqui. Comparar so a posicao da abelha deixaria
    passar um laco que rodasse o numero certo de passos com a animacao fora de fase.
    """
    return (
        game.state,
        game.bird.pos.x,
        game.bird.pos.y,
        game.bird.vel_y,
        game.bird.angle,
        game.bird.frame,
        game.bird.rect.topleft,
        tuple((pipe.x, pipe.gap_y, pipe.scored) for pipe in game.pipes.pipes),
        game.score,
        game.biome.current.id,
        game.biome.fade_timer,
        game.biome.banner_timer,
        game.ground.offset,
        game.decor.far_scrolled,
        game.decor.near_scrolled,
        game.mobs.scrolled,
        game.mobs.frame,
        len(game.particles.particles),
    )


def _autopilot(game: Game) -> None:
    """Voa quando a abelha esta abaixo da abertura da proxima coluna.

    Um roteiro cego (flapar a cada N passos) morreria na primeira coluna e a partida
    acabaria antes de exercitar spawn, pontuacao e troca de bioma. Este e uma funcao do
    estado, entao os dois lacos so tomam a mesma decisao enquanto estiverem mesmo no
    mesmo estado — se um divergir, o roteiro diverge junto e a comparacao final
    denuncia."""
    if game.state != GameState.JOGANDO:
        return
    ahead = [pipe for pipe in game.pipes.pipes if pipe.x + PIPE_W >= game.bird.pos.x]
    target = ahead[0].gap_y if ahead else config.play().centery
    if game.bird.pos.y > target:
        game.bird.flap()


def _scripted_round(game: Game, steps: int, advance) -> None:
    """Mesma partida roteirizada nos dois lacos, jogada pelo mesmo piloto automatico."""
    game._flap_action()
    for _ in range(steps):
        _autopilot(game)
        advance()


@pytest.fixture
def seeded():
    """Devolve o sorteio global ao estado anterior no fim do teste.

    Semear `random` e global e permanente. Sem esta devolucao, todo teste posterior
    passaria a receber a mesma sequencia de aberturas de coluna — o que e pior do que
    parece: um teste que depende de onde a abertura caiu passaria ou falharia conforme
    a *ordem* da suite."""
    state = random.getstate()
    yield
    random.setstate(state)


def test_sixty_fps_reproduces_the_v2_frame_loop_exactly(seeded):
    """R28.4, o requisito que justifica `update()` nao ter mudado uma linha: a 60 FPS
    o laco novo tem que produzir o mesmo jogo que o antigo, e nao um parecido.

    As duas partidas nascem da mesma semente porque a abertura da coluna e sorteada
    (`pipes._spawn`); sem isso a comparacao seria entre dois cenarios diferentes. E a
    semente e reposta antes de cada partida, e nao so antes de cada `Game()`: as
    colunas que nascem *durante* a partida tambem saem do sorteio global."""
    random.seed(20260801)
    stepped = _make_game()
    random.seed(20260801)
    per_frame = _make_game()

    assert _snapshot(stepped) == _snapshot(per_frame), "ancora: as duas partidas comecam iguais"

    random.seed(20260802)
    _scripted_round(stepped, 2000, lambda: stepped.simulate(STEP_MS))
    random.seed(20260802)
    _scripted_round(per_frame, 2000, per_frame.update)

    assert _snapshot(stepped) == _snapshot(per_frame)
    # ancoras: a partida foi longa o bastante para exercitar as tres coisas que R28.4
    # nomeia — fisica, animacao e progressao de bioma —, e nao so os primeiros frames
    assert stepped.state == GameState.JOGANDO
    assert stepped.score >= 10
    assert stepped.biome.current.id == "cave"


def _run_frames(game: Game, frames, monkeypatch) -> list[int]:
    """Roda `run()` por exatamente `len(frames)` frames, com o relogio ditado aqui.

    Devolve o FPS pedido a cada `tick`, que e como se verifica que o laco continua
    limitando a taxa de desenho."""
    monkeypatch.setattr(pygame, "quit", lambda: None)
    remaining = list(frames)
    requested: list[int] = []

    class _ScriptedClock:
        """Relogio ditado pelo teste. Substitui o objeto inteiro, e nao so o `tick`:
        os atributos de `pygame.time.Clock` sao somente leitura."""

        def tick(self, fps: int = 0) -> float:
            requested.append(fps)
            frame_ms = remaining.pop(0)
            if not remaining:
                game.running = False
            return frame_ms

    monkeypatch.setattr(game, "clock", _ScriptedClock())
    game.renderer = FakeRenderer(game.viewport.canvas)
    game.run()
    return requested


def test_the_loop_simulates_from_the_clock_and_draws_once_per_frame(monkeypatch):
    """A separacao que a task inteira existe para fazer: quatro passos de simulacao em
    dois quadros desenhados. E o `tick` continua governando a taxa de desenho."""
    game = _make_game()
    steps = _count_steps(game, monkeypatch)
    draws: list[int] = []
    monkeypatch.setattr(game, "draw", lambda: draws.append(1))

    requested = _run_frames(game, [1000 / 30, 1000 / 30], monkeypatch)

    assert len(steps) == 4
    assert len(draws) == 2
    assert requested == [FPS, FPS]


def test_the_profiler_measures_the_simulation_and_not_a_single_update(monkeypatch):
    """Com a sobreposicao ligada, o tempo de `update` reportado tem que ser o do frame
    inteiro — dois passos num frame de 30 FPS custam o dobro de um, e e isso que o
    jogador sente."""
    monkeypatch.setenv(perf.ENV_VAR, "1")
    game = _make_game()
    assert game.profiler is not None
    steps = _count_steps(game, monkeypatch)
    monkeypatch.setattr(game, "draw", lambda: None)

    _run_frames(game, [1000 / 30, 1000 / 30], monkeypatch)

    assert len(steps) == 4
    assert game.profiler.update_ms > 0


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
