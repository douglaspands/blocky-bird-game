"""Disciplina de alocacao por frame e ajuste do coletor (R27.3, design secao 36).

O que estas duas tasks entregam nao se ve na tela nem na tabela do
`scripts/benchmark.py`: um retangulo que deixa de nascer sessenta vezes por segundo
some tao rapido quanto e criado, entao a memoria transitoria medida por
`tracemalloc` (a marca d'agua de um frame) nem se mexe. O que muda e a *quantidade*
de objetos criados, e e ela que estes testes contam.

A contagem sai de uma subclasse de `pygame.Rect` posta no lugar do proprio
`pygame.Rect` durante o frame medido: todo modulo do jogo constroi retangulos por
`pygame.Rect(...)`, entao trocar o atributo do modulo enxerga todos de uma vez sem
que nenhum deles precise saber que esta sendo medido.
"""

import random
from typing import ClassVar

import pygame
import pytest

from src import config, ui
from src.bird import Bird
from src.config import BLOCK, GROUND_H, HITBOX_SCALE, PIPE_W
from src.game import Game, GameState
from src.ground import Ground
from src.particles import Particle, ParticleSystem
from src.pipes import PipeManager, PipePair
from tests.fakes import FakeRenderer

RECT_BUDGET = 64
"""Teto declarado de `pygame.Rect` construidos num frame de JOGANDO (R27.3).

Medido em 61, exatos e iguais em todos os frames da janela de medicao, no canvas
960x720 do desktop com duas colunas em cena. De onde vem cada um: 18 do
`render._dest_rect` (um por draw call), 22 dos mobs, 11 das faixas derivadas do
viewport e 10 dos recortes de decor, colunas, chao e HUD. Nenhum vem mais das
hitboxes, das metades das colunas nem das listas de simulacao — e isso que a task 58
tirou do caminho, e o teste-ancora abaixo mede quantos eram (80).

A folga de tres e para variacao de plataforma, nao para regressao: 19 retangulos
separam o teto do numero da v2."""

MEASURED_FRAMES = 20
"""Frames da janela de medicao. Fixo porque o resultado tem que ser reproduzivel."""

SEED = 20250731
"""Semente do `random` global, de onde sai a abertura de cada coluna (`pipes._spawn`).

Sem ela a cena medida seria outra a cada execucao — outro numero de colunas, outra
altura de abertura — e um teto apertado viraria teste instavel."""


# --- contagem de retangulos por frame ---------------------------------------------


class _CountingRect(pygame.Rect):
    """`pygame.Rect` que anota cada construcao numa lista compartilhada."""

    _tally: ClassVar[list[int]] = [0]

    def __init__(self, *args: object) -> None:
        """Conta e delega, sem mudar em nada a geometria resultante."""
        _CountingRect._tally[0] += 1
        super().__init__(*args)


def _rects_per_frame(game: Game, monkeypatch: pytest.MonkeyPatch, *, draw: bool = True) -> float:
    """Media de `pygame.Rect` construidos por frame, sobre a janela de medicao."""
    with monkeypatch.context() as patched:
        patched.setattr(pygame, "Rect", _CountingRect)
        _CountingRect._tally[0] = 0
        for _ in range(MEASURED_FRAMES):
            _autopilot(game)
            game.update()
            if draw:
                game.draw()
        return _CountingRect._tally[0] / MEASURED_FRAMES


def _autopilot(game: Game) -> None:
    """Mira a abertura da coluna mais proxima, para a partida medida nao terminar."""
    ahead = [pipe for pipe in game.pipes.pipes if pipe.x + PIPE_W > game.bird.pos.x]
    target = ahead[0].gap_y if ahead else config.play().centery
    if game.bird.pos.y > target:
        game.bird.flap()


@pytest.fixture
def flying_game() -> Game:
    """Partida em curso, com colunas em cena, caches quentes e a colisao de verdade.

    Tres decisoes que o teto apertado exige:

    - **A colisao fica ligada.** `Game._collision_texture` le cinco retangulos por
      coluna e era o maior consumidor dos que a task 58 tornou persistentes. Um duble
      que a desliga — como o do `scripts/benchmark.py` — mediria o frame sem
      justamente a parte que mudou.
    - **O renderizador e o de verdade, nao o `FakeRenderer`.** O duble registra cada
      chamada e copia o retangulo recebido: contar sobre ele seria medir o instrumento
      junto com o jogo (+16 por frame, medidos).
    - **Os ultimos frames do aquecimento tambem desenham.** Construir uma imagem nova
      custa dezenas de retangulos de uma vez (`textures`), e um cache frio jogaria esse
      pico para dentro da janela de medicao.
    """
    random.seed(SEED)
    game = Game()
    game.state = GameState.JOGANDO
    # 220 frames: a coluna seguinte so nasce quando a primeira anda `PIPE_SPACING`, e a
    # primeira so e descartada mais adiante — antes disso a cena ainda esta enchendo.
    for index in range(220):
        _autopilot(game)
        game.update()
        if index >= 190:
            game.draw()
    assert game.state is GameState.JOGANDO, "o piloto automatico deveria manter a partida viva"
    assert len(game.pipes.pipes) >= 2, "ancora: ha colunas em cena para os retangulos contarem"
    return game


def test_a_playing_frame_stays_within_the_rect_budget(
    flying_game: Game, monkeypatch: pytest.MonkeyPatch
) -> None:
    """O teste central da task 58: um frame de JOGANDO nao passa do teto declarado."""
    assert _rects_per_frame(flying_game, monkeypatch) <= RECT_BUDGET


def test_a_simulation_step_builds_no_rectangle_at_all(
    flying_game: Game, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A forma mais nitida do que a task 58 entrega: o passo de simulacao — fisica,
    rolamento, pontuacao, colisao — nao constroi nem um retangulo. Nao e um teto com
    folga, e zero."""
    assert _rects_per_frame(flying_game, monkeypatch, draw=False) == 0


def _v2_bird_rect(bird: Bird) -> pygame.Rect:
    """A `property` que existia em `Bird`, reproduzida literalmente."""
    full = pygame.Rect(round(bird.pos.x), round(bird.pos.y), bird.size, bird.size)
    hitbox_size = round(bird.size * HITBOX_SCALE)
    rect = pygame.Rect(0, 0, hitbox_size, hitbox_size)
    rect.center = full.center
    return rect


def _v2_top_rect(pipe: PipePair) -> pygame.Rect:
    """A `property` que existia em `PipePair`, reproduzida literalmente."""
    bottom = round(pipe.gap_y - pipe.gap_size / 2)
    return pygame.Rect(round(pipe.x), 0, PIPE_W, bottom)


def _v2_bottom_rect(pipe: PipePair) -> pygame.Rect:
    """A `property` que existia em `PipePair`, reproduzida literalmente."""
    top = round(pipe.gap_y + pipe.gap_size / 2)
    return pygame.Rect(round(pipe.x), top, PIPE_W, config.ground_y() - top)


def _v2_ground_rect(ground: Ground) -> pygame.Rect:
    """A `property` que existia em `Ground`, reproduzida literalmente."""
    return pygame.Rect(0, config.ground_y(), config.screen_w(), GROUND_H)


def _restore_the_v2_properties(monkeypatch: pytest.MonkeyPatch) -> None:
    """Poe as quatro `property` de volta no lugar dos atributos persistentes.

    Trocar as classes, e nao os modulos, faz a partida inteira — colisao *e* desenho —
    voltar ao caminho antigo de uma vez, e e o que permite medir o "antes" sem manter
    uma copia do codigo da v2 por perto.

    Os dois detalhes que a fidelidade da medicao exige: o setter descarta (a `property`
    da v2 nao tinha um, e sem ele os construtores quebrariam), e os `sync_*` viram
    nada. Sem neutraliza-los a contagem sairia inflada em 16 por frame — eles leriam a
    `property` so para mexer num retangulo que ninguem mais veria, um custo que a v2
    nunca pagou.
    """
    discard = lambda self, value: None  # noqa: E731 - o setter tem que existir e nao fazer nada
    nothing = lambda self: None  # noqa: E731
    monkeypatch.setattr(Bird, "rect", property(_v2_bird_rect, discard))
    monkeypatch.setattr(PipePair, "top_rect", property(_v2_top_rect, discard))
    monkeypatch.setattr(PipePair, "bottom_rect", property(_v2_bottom_rect, discard))
    # `raising=False` porque `Ground.rect` e atributo de instancia, sem descritor de
    # classe para substituir; a `property` e um descritor de dados e vence o `__dict__`.
    monkeypatch.setattr(Ground, "rect", property(_v2_ground_rect, discard), raising=False)
    monkeypatch.setattr(Bird, "sync_rect", nothing)
    monkeypatch.setattr(PipePair, "sync_rects", nothing)
    monkeypatch.setattr(Ground, "sync_rect", nothing)


def test_the_v2_properties_would_blow_the_budget(flying_game: Game, monkeypatch: pytest.MonkeyPatch) -> None:
    """Ancora dos dois testes acima: sem ela, o teto poderia estar folgado demais para
    pegar uma regressao. Com as `property` de volta sao 80 por frame, contra 61."""
    _restore_the_v2_properties(monkeypatch)
    assert _rects_per_frame(flying_game, monkeypatch) > RECT_BUDGET


def test_the_v2_simulation_step_built_fifteen_rectangles(
    flying_game: Game, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ancora do "zero": o passo de simulacao le mesmo esses retangulos todos.

    Sao 3 pelo chao (a hitbox custava dois, o chao um) mais 6 por coluna — a hitbox
    relida a cada `colliderect`, duas vezes por coluna, mais as duas metades."""
    _restore_the_v2_properties(monkeypatch)
    assert _rects_per_frame(flying_game, monkeypatch, draw=False) == 3 + 6 * len(flying_game.pipes.pipes)


def test_the_collision_check_builds_no_rectangle_at_all(
    flying_game: Game, monkeypatch: pytest.MonkeyPatch
) -> None:
    """O mesmo zero, isolado no metodo onde a maior parte da queda aconteceu."""
    with monkeypatch.context() as patched:
        patched.setattr(pygame, "Rect", _CountingRect)
        _CountingRect._tally[0] = 0
        flying_game._collision_texture()
        assert _CountingRect._tally[0] == 0


# --- retangulos persistentes: o mesmo objeto de frame a frame ----------------------


def test_the_bird_keeps_one_hitbox_object_for_its_whole_life() -> None:
    """Nao e so "menos alocacao": e o mesmo objeto, entao quem guardar a referencia
    continua enxergando a abelha de agora."""
    bird = Bird(100, 200)
    hitbox = bird.rect
    for _ in range(30):
        bird.update()
    assert bird.rect is hitbox
    assert hitbox.centery == round(bird.pos.y) + bird.size // 2


def test_the_idle_bob_also_moves_the_hitbox() -> None:
    """PRONTO nao chama `update`, e a flutuacao mexe na posicao do mesmo jeito."""
    bird = Bird(100, 300)
    for _ in range(10):
        bird.update_idle()
    assert bird.rect.centery == round(bird.pos.y) + bird.size // 2


@pytest.mark.parametrize("y", [0.0, 100.4, 100.5, 100.6, 359.9, 719.0])
def test_the_hitbox_is_exactly_where_the_v2_property_put_it(y: float) -> None:
    """A otimizacao nao pode mover a hitbox um pixel que seja — inclusive nos
    arredondamentos de meio pixel, onde `round(pos) + size // 2` e
    `round(pos + size / 2)` poderiam divergir."""
    bird = Bird(37.5, y)
    assert tuple(bird.rect) == tuple(_v2_bird_rect(bird))


def test_the_pipe_keeps_its_two_rectangles_across_the_scroll() -> None:
    """As duas metades acompanham o `x` sem trocar de objeto."""
    manager = PipeManager(160, "dirt", "grass_side")
    pipe = manager.pipes[0]
    top, bottom = pipe.top_rect, pipe.bottom_rect

    manager.update(2.5, 160, "dirt", "grass_side")

    assert pipe.top_rect is top and pipe.bottom_rect is bottom
    assert top.x == bottom.x == round(pipe.x)


@pytest.mark.parametrize("gap_y", [200.0, 360.0, 543.0])
def test_the_pipe_rectangles_match_the_v2_properties(gap_y: float) -> None:
    """A geometria das duas metades e a mesma de antes, abertura por abertura."""
    pipe = PipePair(123.7, gap_y, 160, "dirt", "grass_side")
    assert tuple(pipe.top_rect) == tuple(_v2_top_rect(pipe))
    assert tuple(pipe.bottom_rect) == tuple(_v2_bottom_rect(pipe))


def test_a_resize_moves_the_pipe_rectangles_to_the_new_ground_line() -> None:
    """A metade de baixo termina em `ground_y()`, que anda quando a janela muda de
    proporcao — e ha frames desenhados antes do proximo passo de simulacao."""
    game = Game()
    pipe = game.pipes.pipes[0]

    game.apply_resize((1080, 2400))

    assert config.ground_y() == pipe.bottom_rect.bottom
    assert tuple(pipe.bottom_rect) == tuple(_v2_bottom_rect(pipe))


def test_a_resize_moves_the_ground_rectangle_too() -> None:
    """Mesma razao, para a faixa de colisao do chao."""
    game = Game()

    game.apply_resize((1080, 2400))

    assert tuple(game.ground.rect) == tuple(_v2_ground_rect(game.ground))


def test_the_ground_keeps_one_rectangle_across_the_scroll() -> None:
    """O chao rola sem trocar o retangulo de colisao de objeto."""
    ground = Ground()
    rect = ground.rect
    for _ in range(20):
        ground.update(3.0)
    assert ground.rect is rect
    assert tuple(rect) == (0, config.ground_y(), config.screen_w(), GROUND_H)


def test_the_pipe_list_drops_two_neighbours_that_leave_together() -> None:
    """A remocao no lugar tem que aguentar duas colunas vizinhas saindo no mesmo frame.

    Nao acontece no jogo — as colunas sao espacadas de `PIPE_SPACING` e saem uma de
    cada vez —, e foi exatamente por isso que a versao errada do laco (a que avanca o
    indice mesmo depois de apagar, e portanto pula o vizinho) sobreviveu a primeira
    rodada de mutacao. O caso e montado a mao."""
    manager = PipeManager(160, "dirt", "grass_side")
    survivor = manager.pipes[0]
    leaving = [PipePair(-1000.0, 300.0, 160, "dirt", "grass_side") for _ in range(2)]
    manager.pipes[:0] = leaving  # as duas na frente, uma colada na outra
    assert all(pipe.off_screen() for pipe in leaving)  # ancora: as duas estao mesmo fora

    manager.update(2.5, 160, "dirt", "grass_side")

    assert manager.pipes == [survivor]


# --- listas estaveis ---------------------------------------------------------------


def test_the_pipe_list_is_never_rebuilt() -> None:
    """A compreensao de lista que estava aqui construia uma lista por frame para
    descartar uma coluna a cada ~90. O objeto agora atravessa a partida inteira,
    inclusive os frames que criam e os que descartam colunas."""
    manager = PipeManager(160, "dirt", "grass_side")
    pipes = manager.pipes
    seen_spawn = seen_discard = False

    for _ in range(400):
        before = list(manager.pipes)
        manager.update(2.5, 160, "dirt", "grass_side")
        seen_spawn = seen_spawn or len(manager.pipes) > len(before)
        seen_discard = seen_discard or any(pipe not in manager.pipes for pipe in before)
        assert manager.pipes is pipes

    assert seen_spawn and seen_discard, "ancora: a partida medida criou e descartou colunas"


def test_the_discard_still_drops_exactly_the_pipes_that_left() -> None:
    """A remocao no lugar tem que filtrar o mesmo que a compreensao filtrava — nem uma
    coluna a mais, nem uma a menos."""
    manager = PipeManager(160, "dirt", "grass_side")
    for _ in range(400):
        manager.update(2.5, 160, "dirt", "grass_side")
        assert [pipe for pipe in manager.pipes if pipe.off_screen()] == []
    assert len(manager.pipes) >= 2


def test_the_particle_list_is_never_rebuilt() -> None:
    """Mesma regra do gerenciador de colunas, no sistema de particulas."""
    system = ParticleSystem()
    particles = system.particles
    system.particles.extend(Particle((10, 10), (0, 0), lifetime, 4, (1, 2, 3)) for lifetime in (2, 30, 5))

    for _ in range(40):
        system.update()
        assert system.particles is particles

    assert system.particles == []


@pytest.mark.parametrize(
    "lifetimes",
    [(3, 1, 4, 1, 5, 2), (4, 1, 1, 5), (1, 1, 1, 9), (9, 1, 1, 1)],
    ids=["intercaladas", "duas-no-meio", "tres-no-comeco", "tres-no-fim"],
)
def test_the_particles_die_in_their_own_order(lifetimes: tuple[int, ...]) -> None:
    """As particulas de uma explosao tem tempos de vida sorteados, entao morrem
    embaralhadas — a remocao no lugar precisa aguentar buracos no meio da lista.

    Duas escolhas que a rodada de mutacao ditou. Os casos com mortes *vizinhas*: a
    versao errada do laco (a que avanca o indice mesmo depois de apagar) pula o
    vizinho, e uma lista onde nenhum par de mortas encosta nao a incomoda. E a
    conferencia **a cada passo**, e nao so no fim: a que ficou para tras e apagada no
    passo seguinte, entao dois `update()` seguidos escondem o erro atras da correcao.
    """
    system = ParticleSystem()
    system.particles.extend(Particle((0, 0), (0, 0), life, 4, (1, 2, 3)) for life in lifetimes)
    born = list(system.particles)

    for step in range(1, max(lifetimes) + 2):
        system.update()
        alive = [p for p, life in zip(born, lifetimes, strict=True) if life > step]
        assert system.particles == alive, f"apos {step} passo(s)"

    assert system.particles == []


class _FillSpy(FakeRenderer):
    """Renderizador que guarda o proprio objeto recebido em `fill`, sem copia-lo.

    O `FakeRenderer` copia (`pygame.Rect(rect)`) para que os testes de desenho possam
    comparar geometria sem medo de mutacao posterior. Aqui a identidade e justamente o
    que esta em jogo, entao a copia atrapalha."""

    def __init__(self) -> None:
        """Cria o espiao com a lista de retangulos recebidos."""
        super().__init__()
        self.filled: list[pygame.Rect] = []

    def fill(self, color: object, rect: pygame.Rect) -> None:
        """Guarda a referencia exata que o chamador passou."""
        self.filled.append(rect)


def test_the_particle_draws_from_a_rectangle_it_keeps() -> None:
    """Eram 16 retangulos por frame na tela de GAME_OVER, um por particula.

    A afirmacao e de identidade, e nao de geometria: um `draw` que construa um
    retangulo novo com as coordenadas certas passaria em qualquer teste de posicao."""
    system = ParticleSystem()
    particle = Particle((100, 100), (1.0, 0.0), 30, 6, (200, 100, 50))
    system.particles.append(particle)
    rect = particle.rect
    spy = _FillSpy()

    system.update()
    system.draw(spy)

    assert particle.rect is rect
    assert spy.filled == [rect]
    assert spy.filled[0] is rect, "o desenho usa o retangulo da particula, e nao uma copia"
    assert rect.center == (round(particle.pos.x), round(particle.pos.y))


# --- __slots__ ---------------------------------------------------------------------


@pytest.mark.parametrize("cls", [Bird, PipePair, Particle], ids=["bird", "pipe", "particle"])
def test_the_small_data_classes_have_no_instance_dict(cls: type) -> None:
    """`__slots__` de verdade: se um campo escapar da lista, o `__dict__` volta e o
    ganho some sem ninguem notar."""
    assert "__dict__" not in dir(cls)
    assert hasattr(cls, "__slots__")


def test_the_slots_cover_every_field_the_constructor_sets() -> None:
    """Um campo fora da lista levantaria `AttributeError` na construcao — este teste
    existe para que isso apareca aqui, e nao no primeiro frame do jogo."""
    bird = Bird(10, 20)
    pipe = PipePair(10.0, 300.0, 160, "dirt", "grass_side")
    particle = Particle((0, 0), (0, 0), 10, 4, (1, 2, 3))
    for obj in (bird, pipe, particle):
        with pytest.raises(AttributeError):
            obj.campo_que_nao_existe = 1  # ty: ignore[invalid-assignment]


# --- texto: medicao uma vez por forma ----------------------------------------------


def test_fit_scale_measures_each_shape_only_once(monkeypatch: pytest.MonkeyPatch) -> None:
    """O laco de medicao rodava por linha por frame, sempre com os mesmos argumentos."""
    ui._FIT_SCALE_CACHE.clear()
    calls = [0]
    original = ui._text_width

    def counted(n_chars: int, scale: int) -> int:
        calls[0] += 1
        return original(n_chars, scale)

    monkeypatch.setattr(ui, "_text_width", counted)

    ui._fit_scale("ESPACO / CLIQUE PARA VOAR", 4)
    first = calls[0]
    for _ in range(60):
        ui._fit_scale("ESPACO / CLIQUE PARA VOAR", 4)

    assert first > 0, "ancora: a primeira chamada mede mesmo"
    assert calls[0] == first


def test_fit_scale_still_shrinks_what_does_not_fit() -> None:
    """O cache nao pode mudar a resposta: texto longo continua encolhendo, curto nao."""
    ui._FIT_SCALE_CACHE.clear()
    long_text = "ESPACO / CLIQUE PARA REINICIAR"
    assert ui._fit_scale(long_text, 6) < 6
    assert ui._fit_scale(long_text, 6) < 6  # de novo, agora pelo cache
    assert ui._fit_scale("0", 6) == 6


def test_fit_scale_answers_by_length_and_not_by_content() -> None:
    """A fonte e monoespacada, entao a chave e o comprimento — e e isso que mantem o
    cache pequeno com uma pontuacao que sobe de 0 a 999."""
    ui._FIT_SCALE_CACHE.clear()
    ui._fit_scale("123", 6)
    ui._fit_scale("456", 6)
    assert len(ui._FIT_SCALE_CACHE) == 1


def test_fit_scale_reacts_to_a_narrower_play_area(monkeypatch: pytest.MonkeyPatch) -> None:
    """O limite entra na chave: um cache indexado so por (comprimento, escala)
    devolveria a resposta da tela anterior."""
    ui._FIT_SCALE_CACHE.clear()
    text = "BLOCKY BEE"
    wide = ui._fit_scale(text, 6)
    monkeypatch.setattr(ui, "max_text_w", lambda: 40)
    assert ui._fit_scale(text, 6) < wide


def test_the_block_size_is_the_hitbox_reference() -> None:
    """Ancora dos testes de hitbox: eles usam `size // 2`, que so casa com
    `round(size * HITBOX_SCALE)` porque o bloco e par."""
    assert Bird(0, 0).size == BLOCK
    assert BLOCK % 2 == 0
