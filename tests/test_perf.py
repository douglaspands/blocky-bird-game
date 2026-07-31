"""Testes da instrumentacao de desempenho (R30.1, R30.2)."""

import pygame

from src import perf, pixelfont
from src.game import Game


def test_enabled_desligado_por_padrao(monkeypatch):
    """Sem a variavel de ambiente, a instrumentacao fica desligada (R30.2)."""
    monkeypatch.delenv(perf.ENV_VAR, raising=False)
    assert perf.enabled() is False


def test_enabled_trata_vazio_e_zero_como_desligado(monkeypatch):
    """Valores vazio e "0" nao ligam a instrumentacao — evita ligar sem querer."""
    for valor in ("", "0"):
        monkeypatch.setenv(perf.ENV_VAR, valor)
        assert perf.enabled() is False


def test_enabled_ligado_com_qualquer_outro_valor(monkeypatch):
    """Qualquer outro valor liga, para que `BLOCKY_PERF=1` e `BLOCKY_PERF=true` funcionem."""
    for valor in ("1", "true", "sim"):
        monkeypatch.setenv(perf.ENV_VAR, valor)
        assert perf.enabled() is True


def test_media_movel_sem_amostras_e_zero():
    """A media comeca em zero, sem divisao por zero na primeira leitura."""
    media = perf._MovingAverage(4)
    assert media.average == 0.0


def test_media_movel_antes_de_encher_a_janela():
    """Antes de encher, a media considera so as amostras vistas — nao os zeros do buffer."""
    media = perf._MovingAverage(10)
    media.add(2.0)
    media.add(4.0)
    assert media.average == 3.0


def test_media_movel_descarta_a_amostra_mais_antiga():
    """Com a janela cheia, a amostra mais antiga sai ao entrar uma nova."""
    media = perf._MovingAverage(3)
    for valor in (10.0, 10.0, 10.0):
        media.add(valor)
    assert media.average == 10.0
    media.add(1.0)  # expulsa o primeiro 10.0
    assert media.average == 7.0


def test_fps_derivado_da_duracao_do_frame():
    """16.0 ms por frame equivalem a ~62.5 FPS."""
    profiler = perf.FrameProfiler()
    for _ in range(5):
        profiler.frame(16.0)
    assert profiler.fps == 1000.0 / 16.0


def test_fps_zero_sem_amostras():
    """Sem frames medidos, o FPS e zero em vez de erro de divisao."""
    assert perf.FrameProfiler().fps == 0.0


def test_end_update_e_end_draw_medem_intervalos_separados():
    """Cada `end_*` fecha sua propria etapa; nenhuma medicao entra na outra."""
    profiler = perf.FrameProfiler()
    profiler.begin()
    profiler.end_update()
    profiler.end_draw()
    assert profiler.update_ms >= 0.0
    assert profiler.draw_ms >= 0.0


def test_lines_usa_apenas_glifos_existentes():
    """A sobreposicao nao pode conter caractere sem glifo, que sairia como espaco em branco."""
    profiler = perf.FrameProfiler()
    profiler.frame(16.7)
    profiler.backend = "gpu-accelerated"
    for linha in profiler.lines():
        for caractere in linha.upper():
            assert caractere in pixelfont.GLYPHS, f"glifo ausente para {caractere!r}"


def test_draw_overlay_desenha_no_canto_superior_esquerdo():
    """A sobreposicao ocupa o canto superior esquerdo, sem cobrir o centro da tela."""
    surface = pygame.Surface((480, 720))
    surface.fill((0, 0, 0))
    profiler = perf.FrameProfiler()
    profiler.frame(16.0)

    perf.draw_overlay(surface, profiler)

    assert surface.get_at((0, 0))[:3] == (0, 0, 0), "margem preservada"
    canto = pygame.Rect(0, 0, 160, 80)
    assert any(
        surface.get_at((x, y))[:3] != (0, 0, 0)
        for x in range(canto.left, canto.right, 2)
        for y in range(canto.top, canto.bottom, 2)
    ), "nada foi desenhado no canto"
    assert surface.get_at((240, 400))[:3] == (0, 0, 0), "o centro da tela nao pode ser tocado"


def test_game_sem_profiler_por_padrao(monkeypatch):
    """Sem `BLOCKY_PERF`, o Game nem instancia o profiler (R30.2)."""
    monkeypatch.delenv(perf.ENV_VAR, raising=False)
    assert Game().profiler is None


def test_game_com_profiler_quando_ligado(monkeypatch):
    """Com `BLOCKY_PERF` ligado, o Game passa a instrumentar o loop."""
    monkeypatch.setenv(perf.ENV_VAR, "1")
    assert isinstance(Game().profiler, perf.FrameProfiler)
