"""Qualidade adaptativa: medicao, histerese, persistencia e o que NAO muda (R29).

O teste central deste arquivo nao e nenhum dos que medem FPS — e o que afirma que os
tres niveis jogam o mesmo jogo (R29.3). Um sistema que se ajusta sozinho e util; um que
se ajusta e, de quebra, muda a dificuldade, destrui a comparabilidade dos recordes que
R24 garante.
"""

import json
import random

import pygame
import pytest

from src import config, quality, viewport
from src.game import Game, GameState
from src.quality import DROP_FPS, RISE_FPS, RISE_WINDOW_FRAMES, WINDOW_FRAMES, Level, Quality
from tests.fakes import FakeRenderer

SIXTY = 1000 / 60
"""Duracao de um quadro a 60 FPS, em milissegundos."""

FORTY = 1000 / 40
THIRTY = 1000 / 30


@pytest.fixture
def seeded_pipes():
    """Semeia o sorteio das aberturas e devolve uma funcao que o repoe.

    A abertura da coluna vem do `random` global (`pipes._spawn`), entao duas partidas
    so sao comparaveis se nascerem da mesma semente. O estado anterior e devolvido no
    fim: semear e global, e deixar a semente para tras mudaria o cenario de todos os
    testes seguintes."""
    state = random.getstate()

    def seed() -> None:
        random.seed(6406400)

    seed()
    yield seed
    random.setstate(state)


def _feed(adaptive: Quality, frame_ms: float, frames: int, *, playing: bool = True) -> None:
    """Alimenta a medicao com `frames` quadros de mesma duracao."""
    for _ in range(frames):
        adaptive.frame(frame_ms, playing)


# --- medicao e queda de nivel (R29.1, R29.2) --------------------------------------


def test_a_new_game_starts_at_full_quality():
    assert Quality().level is Level.ALTO
    assert Quality().settings.mobs is True


def test_sustained_low_frame_rate_drops_a_level():
    """R29.2: o aparelho nao da conta, e o jogo desliga decoracao em vez de engasgar."""
    adaptive = Quality()

    _feed(adaptive, FORTY, WINDOW_FRAMES)

    assert adaptive.level is Level.MEDIO


def test_the_drop_needs_the_whole_window_and_not_a_single_frame():
    """Um quadro ruim nao decide nada: a janela ainda nem fechou."""
    adaptive = Quality()

    _feed(adaptive, FORTY, WINDOW_FRAMES - 1)

    assert adaptive.level is Level.ALTO


def test_an_isolated_stall_does_not_drop_the_level():
    """O caso que a janela existe para absorver: um travamento de 300 ms no meio de
    dois segundos bons — o coletor de lixo do sistema, uma notificacao, o que for.
    A media cai para ~52 FPS, acima do limiar, e o cenario continua inteiro."""
    adaptive = Quality()

    _feed(adaptive, SIXTY, WINDOW_FRAMES // 2)
    adaptive.frame(300.0, True)
    _feed(adaptive, SIXTY, WINDOW_FRAMES // 2)

    assert adaptive.level is Level.ALTO


def test_the_drop_goes_one_level_at_a_time():
    """Descer direto para BAIXO tiraria o cenario inteiro de um aparelho que talvez
    coubesse no MEDIO."""
    adaptive = Quality()

    _feed(adaptive, THIRTY, WINDOW_FRAMES)
    assert adaptive.level is Level.MEDIO

    _feed(adaptive, THIRTY, WINDOW_FRAMES)
    assert adaptive.level is Level.BAIXO


def test_the_lowest_level_is_the_floor():
    """Sem piso, o nivel viraria numero negativo e a tabela estouraria."""
    adaptive = Quality(Level.BAIXO)

    _feed(adaptive, THIRTY, RISE_WINDOW_FRAMES * 2)

    assert adaptive.level is Level.BAIXO


# --- histerese e subida (R29.4) ---------------------------------------------------


def test_the_rise_needs_a_longer_window_than_the_drop():
    """A assimetria de R29.4: subir cedo demais devolve o engasgo que motivou a
    descida, e o jogador ve o cenario piscando."""
    adaptive = Quality(Level.MEDIO)

    _feed(adaptive, SIXTY, WINDOW_FRAMES)
    assert adaptive.level is Level.MEDIO, "a janela curta nao sobe ninguem"

    _feed(adaptive, SIXTY, RISE_WINDOW_FRAMES - WINDOW_FRAMES)
    assert adaptive.level is Level.ALTO


def test_the_rise_needs_a_comfortable_margin_and_not_just_being_above_the_drop():
    """A faixa morta entre os dois limiares e a histerese propriamente dita: a 54 FPS o
    aparelho nao esta mal o bastante para descer nem bem o bastante para subir."""
    between = 1000 / ((DROP_FPS + RISE_FPS) / 2)
    adaptive = Quality(Level.MEDIO)

    _feed(adaptive, between, RISE_WINDOW_FRAMES * 2)

    assert adaptive.level is Level.MEDIO


def test_a_device_on_the_edge_settles_instead_of_bouncing():
    """O motivo de existir histerese, dito como cenario. Este aparelho roda a 45 FPS no
    ALTO e a 55 no MEDIO — o desligamento da decoracao ajuda, mas nao o bastante.

    55 FPS esta **acima** do limiar de queda: se a subida usasse o mesmo numero, ele
    voltaria ao ALTO, cairia de volta para 45, desceria de novo, e alternaria a cada
    poucos segundos — que e visualmente pior do que ficar no nivel de baixo. A margem
    da subida e o que o faz assentar."""
    adaptive = Quality()
    levels: list[Level] = []

    for _ in range(12):
        measured = 45 if adaptive.level is Level.ALTO else 55
        _feed(adaptive, 1000 / measured, WINDOW_FRAMES)
        levels.append(adaptive.level)

    assert DROP_FPS < 55, "ancora: sem a margem da subida, este aparelho voltaria ao ALTO"
    assert levels == [Level.MEDIO] * 12


def test_the_rise_stops_at_the_top():
    adaptive = Quality()

    _feed(adaptive, SIXTY, RISE_WINDOW_FRAMES * 2)

    assert adaptive.level is Level.ALTO


# --- so JOGANDO alimenta a medicao (R29.1) ----------------------------------------


def test_frames_outside_playing_are_not_measured():
    """A tela PRONTO desenha outra coisa e o GAME_OVER congela o cenario: medir ali
    seria medir outro jogo."""
    adaptive = Quality()

    _feed(adaptive, 1000.0, RISE_WINDOW_FRAMES * 2, playing=False)

    assert adaptive.level is Level.ALTO


def test_a_pause_discards_the_window_instead_of_freezing_it():
    """Se a janela sobrevivesse a pausa, os quadros bons de antes e os de depois se
    somariam com o tempo parado no meio — e o aparelho seria punido por o jogador ter
    trocado de aplicativo."""
    adaptive = Quality()

    _feed(adaptive, FORTY, WINDOW_FRAMES - 1)
    adaptive.frame(SIXTY, False)  # um quadro fora de JOGANDO
    _feed(adaptive, FORTY, 1)

    assert adaptive.level is Level.ALTO


# --- o que os niveis mudam, e o que nao mudam (R29.2, R29.3) ----------------------


def test_each_level_turns_off_more_decoration_than_the_one_above():
    """A ordem de R29.2: primeiro os mobs e a camada distante, depois o parallax
    inteiro. Sempre em ordem crescente de importancia visual."""
    alto, medio, baixo = (quality.SETTINGS[level] for level in (Level.ALTO, Level.MEDIO, Level.BAIXO))

    assert (alto.mobs, alto.far_parallax, alto.near_parallax) == (True, True, True)
    assert (medio.mobs, medio.far_parallax, medio.near_parallax) == (False, False, True)
    assert (baixo.mobs, baixo.far_parallax, baixo.near_parallax) == (False, False, False)
    assert alto.particles > medio.particles > baixo.particles


def test_only_the_lowest_level_drops_the_frame_rate():
    """Desenhar a 30 FPS e a ultima carta, e mesmo ela nao toca na simulacao: os passos
    logicos continuam sendo 60 por segundo (seção 37)."""
    assert quality.SETTINGS[Level.ALTO].render_fps == 60
    assert quality.SETTINGS[Level.MEDIO].render_fps == 60
    assert quality.SETTINGS[Level.BAIXO].render_fps == 30


def _play(game: Game, frames: int) -> tuple:
    """Joga `frames` passos com um roteiro fixo e devolve o que R29.3 protege."""
    game._flap_action()
    for index in range(frames):
        if index % 12 == 0:
            game.bird.flap()
        game.update()
    return (
        game.bird.pos.x,
        game.bird.pos.y,
        game.bird.vel_y,
        game.bird.rect.size,
        game.bird.rect.topleft,
        tuple(
            (pipe.x, pipe.gap_size, pipe.top_rect.height, pipe.bottom_rect.height)
            for pipe in game.pipes.pipes
        ),
        game.score,
        game.state,
    )


@pytest.mark.parametrize("level", list(Level))
def test_the_rules_are_identical_at_every_quality_level(level, seeded_pipes):
    """R29.3, o requisito que este modulo inteiro nao pode violar: velocidade de coluna,
    tamanho de abertura, hitbox e pontuacao sao os mesmos nos tres niveis.

    E o que preserva a comparabilidade dos recordes garantida por R24 — sem isso, um
    aparelho fraco jogaria um jogo mais facil (ou mais dificil) e a tabela de recordes
    deixaria de significar a mesma coisa.
    """
    reference = Game()
    reference.quality = Quality(Level.ALTO)
    expected = _play(reference, 200)

    seeded_pipes()
    game = Game()
    game.quality = Quality(level)
    assert _play(game, 200) == expected


def test_the_particle_count_follows_the_level():
    """A unica grandeza numerica que muda — e ela e puramente visual: as particulas
    nascem *depois* da colisao, e nenhuma delas colide com nada (R3.2)."""
    game = Game()
    game.quality = Quality(Level.BAIXO)
    game._flap_action()
    frames = 0
    while game.state == GameState.JOGANDO and frames < 2000:
        game.update()
        frames += 1

    assert game.state == GameState.GAME_OVER
    assert len(game.particles.particles) == quality.SETTINGS[Level.BAIXO].particles


# --- persistencia (R29.5, R29.6) --------------------------------------------------


def test_the_level_survives_between_sessions(tmp_path):
    path = tmp_path / quality.FILENAME
    quality.save_level(Level.MEDIO, path)

    assert quality.load_level(path) is Level.MEDIO


def test_a_missing_file_means_full_quality(tmp_path):
    """R29.6: sem arquivo, comeca no maximo e redetecta."""
    assert quality.load_level(tmp_path / "nao-existe.json") is Level.ALTO


@pytest.mark.parametrize("content", ["", "{", "[]", '{"level": "TURBO"}', '{"level": null}', '{"nivel": 2}'])
def test_a_corrupted_file_means_full_quality(tmp_path, content):
    """Mesma disciplina de `score.load_highscore`: um arquivo de preferencia quebrado
    nunca pode impedir o jogo de abrir. Comecar no maximo e a unica escolha que se
    corrige sozinha em dois segundos — comecar no minimo ficaria feio para sempre."""
    path = tmp_path / quality.FILENAME
    path.write_text(content, encoding="utf-8")

    assert quality.load_level(path) is Level.ALTO


def test_saving_is_not_allowed_to_crash_the_game(tmp_path):
    """Disco cheio, diretorio somente leitura: engolido, como no recorde (R4.4)."""
    quality.save_level(Level.BAIXO, tmp_path / "sem" / "essa" / "pasta.json")


def test_the_file_is_written_next_to_the_highscore(tmp_path):
    """R29.5 pede o mesmo diretorio gravavel do recorde (R4.5) — no Android, o unico
    lugar onde escrever funciona."""
    from src import score

    quality.save_level(Level.MEDIO)

    assert (tmp_path / quality.FILENAME).exists()
    assert score._default_path().parent == quality._default_path().parent


# --- integracao com o laco e com o desenho ----------------------------------------


WIDE = (1920, 1080)
"""Monitor: canvas 1280x720, com faixas laterais e sem faixa de ceu — e onde os mobs
de `draw_sides` aparecem."""

PHONE = (1080, 2400)
"""Celular alongado: canvas 480x1067, com faixa de ceu e sem faixas laterais — e onde
os mobs de `draw_sky` aparecem.

As duas telas entram no teste porque cada uma exercita um dos dois desenhos de mob.
Numa so, desligar apenas o outro passaria despercebido."""


def _drawn_layers(game: Game, screen: tuple[int, int]) -> tuple[set, bool]:
    """Desenha um frame naquela tela e devolve (camadas de parallax, houve mob)."""
    config.set_viewport(viewport.compute(*screen))
    game.viewport = config.viewport()
    game.renderer = FakeRenderer(game.viewport.canvas)
    game.draw()
    keys = [key for key, _ in game.renderer.draws if isinstance(key, tuple)]
    return ({key[2] for key in keys if key[0] == "decor"}, any(key[0] == "mob" for key in keys))


@pytest.mark.parametrize("screen", [WIDE, PHONE])
@pytest.mark.parametrize(
    ("level", "layers", "has_mobs"),
    [(Level.ALTO, {0, 1}, True), (Level.MEDIO, {1}, False), (Level.BAIXO, set(), False)],
)
def test_the_decoration_disappears_level_by_level(level, layers, has_mobs, screen):
    """R29.2 no frame de verdade: o nivel nao e uma variavel que ninguem le."""
    game = Game()
    game.quality = Quality(level)

    assert _drawn_layers(game, screen) == (layers, has_mobs)


def test_the_game_keeps_the_level_from_the_previous_session():
    """R29.5: os primeiros segundos ruins de um aparelho fraco acontecem uma vez."""
    quality.save_level(Level.BAIXO)

    assert Game().quality.level is Level.BAIXO


def _run_frames(game: Game, frame_ms: float, frames: int, monkeypatch, on_frame=None) -> list[int]:
    """Roda o laco real por `frames` quadros de duracao fixa, sem desenhar nada.

    `on_frame` entra no lugar do desenho, e e o unico jeito de observar o que acontece
    *dentro* do laco: depois que `run()` retorna, a saida ordenada ja descarregou tudo
    que estava pendente."""
    monkeypatch.setattr(pygame, "quit", lambda: None)
    monkeypatch.setattr(game, "draw", on_frame or (lambda: None))
    remaining = [frames]
    requested: list[int] = []

    class _ScriptedClock:
        def tick(self, fps: int = 0) -> float:
            requested.append(fps)
            remaining[0] -= 1
            if remaining[0] <= 0:
                game.running = False
            return frame_ms

    monkeypatch.setattr(game, "clock", _ScriptedClock())
    game.run()
    return requested


def test_the_loop_limits_drawing_to_the_frame_rate_of_the_level(monkeypatch):
    """No nivel BAIXO o relogio passa a pedir 30 quadros — e so o relogio: a simulacao
    continua sendo governada pelo acumulador, a 60 passos logicos por segundo."""
    game = Game()
    game.quality = Quality(Level.BAIXO)

    requested = _run_frames(game, THIRTY, 3, monkeypatch)

    assert requested == [30, 30, 30]


def test_a_bad_frame_rate_outside_playing_never_drops_the_level(monkeypatch):
    """De ponta a ponta: mil quadros pessimos na tela PRONTO nao mexem em nada (R29.1).
    A tela inicial nao e representativa — e ela que fica aberta enquanto o aparelho
    ainda esta abrindo o resto do sistema."""
    game = Game()
    assert game.state == GameState.PRONTO

    _run_frames(game, 100.0, RISE_WINDOW_FRAMES * 2, monkeypatch)

    assert game.quality.level is Level.ALTO


def test_the_level_is_measured_and_dropped_while_playing(monkeypatch):
    """O outro lado: jogando, a mesma taxa ruim derruba o nivel."""
    game = Game()
    game._flap_action()
    monkeypatch.setattr(game, "update", lambda: None)  # a partida nao pode acabar aqui

    _run_frames(game, 100.0, WINDOW_FRAMES + 1, monkeypatch)

    assert game.quality.level is Level.MEDIO


def test_the_new_level_is_not_written_to_disk_inside_the_playing_frame(monkeypatch):
    """R27.5 vale para este arquivo tambem — e aqui ele importa mais: a troca de nivel
    acontece justamente no aparelho que ja esta com dificuldade, e uma escrita sincrona
    ali cairia no pior momento possivel.

    A observacao e feita **de dentro** do laco, um registro por quadro: depois que
    `run()` retorna, a saida ordenada ja gravou o que estava pendente, e "nao gravou
    durante o jogo" seria indistinguivel de "nunca gravou"."""
    written: list[Level] = []
    monkeypatch.setattr(quality, "save_level", lambda level, path=None: written.append(level))
    game = Game()
    game._flap_action()
    monkeypatch.setattr(game, "update", lambda: None)  # a partida nao pode acabar aqui
    per_frame: list[int] = []

    _run_frames(game, 100.0, WINDOW_FRAMES + 10, monkeypatch, on_frame=lambda: per_frame.append(len(written)))

    assert game.quality.level is Level.MEDIO, "ancora: o nivel caiu mesmo durante o laco"
    assert per_frame[-1] == 0, "nenhuma gravacao aconteceu dentro de um quadro de JOGANDO"
    assert written == [Level.MEDIO], "e a gravacao aconteceu na saida do laco"


def test_going_to_the_background_writes_a_pending_level(monkeypatch):
    """O segundo dos tres momentos de gravacao, o mesmo do recorde (task 60): o aviso
    que o Android da antes de poder encerrar o app."""
    written: list[Level] = []
    monkeypatch.setattr(quality, "save_level", lambda level, path=None: written.append(level))
    game = Game()
    game.quality.level = Level.BAIXO
    game.quality.dirty = True

    pygame.event.post(pygame.event.Event(pygame.APP_WILLENTERBACKGROUND))
    game.handle_events()

    assert written == [Level.BAIXO]
    assert game.quality.dirty is False


def test_a_level_that_did_not_change_is_not_written_again(monkeypatch):
    """Sem marca de pendente, todo GAME_OVER reescreveria o mesmo arquivo."""
    written: list[Level] = []
    monkeypatch.setattr(quality, "save_level", lambda level, path=None: written.append(level))
    game = Game()

    pygame.event.post(pygame.event.Event(pygame.APP_WILLENTERBACKGROUND))
    game.handle_events()

    assert written == []


def test_the_level_is_stored_by_name_and_not_by_number():
    """Gravar o inteiro do `IntEnum` amarraria o arquivo a ordem da enumeracao: inserir
    um nivel no meio, um dia, reinterpretaria em silencio o arquivo de todo mundo."""
    quality.save_level(Level.MEDIO)

    assert json.loads(quality._default_path().read_text(encoding="utf-8")) == {"level": "MEDIO"}
