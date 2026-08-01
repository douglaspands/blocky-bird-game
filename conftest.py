import gc
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest


@pytest.fixture(scope="session", autouse=True)
def _pygame_session():
    pygame.init()
    yield
    pygame.quit()


@pytest.fixture(autouse=True)
def _isolate_cwd(tmp_path, monkeypatch):
    """Evita que testes leiam/gravem highscore.json na raiz real do projeto.

    storage.save_dir() no desktop resolve para a raiz do projeto via __file__
    (nao mais o cwd), entao so o chdir nao basta desde a v2 — monkeypatcha
    save_dir() direto para o tmp_path do teste."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("src.storage.save_dir", lambda: tmp_path)


@pytest.fixture(autouse=True)
def _reset_viewport():
    """Game define o viewport ativo globalmente ao criar o display (960x720 no
    desktop). Sem este reset, o canvas de um teste vazaria para o proximo — os
    testes de unidade assumem o canvas 2:3, identico a area jogavel."""
    from src import config, viewport

    config.set_viewport(viewport.compute(viewport.PLAY_W, viewport.PLAY_H))


@pytest.fixture(autouse=True)
def _reset_gc():
    """Desfaz o `perf.tune_gc()` que todo `Game()` executa (task 59).

    `gc.freeze()` e permanente e global: sem este reset, cada um dos ~150 `Game()` da
    suite mandaria para a geracao permanente tudo que estivesse vivo naquele instante —
    inclusive o lixo ciclico dos testes anteriores, que entao nunca mais seria
    recolhido. O jogo quer exatamente esse efeito (constroi tudo uma vez e vive ate o
    fim); um processo de teste que cria e joga fora centenas de jogos, nao."""
    default_threshold = gc.get_threshold()
    yield
    gc.unfreeze()
    gc.set_threshold(*default_threshold)


@pytest.fixture(autouse=True)
def _reset_event_filter():
    """Desfaz o `input.configure_event_filter()` que todo `Game()` executa (task 61).

    O filtro e global e permanente, como o `gc.freeze()` acima: sem este reset, o
    primeiro `Game()` da suite passaria a bloquear eventos para todos os testes
    seguintes — inclusive um teste futuro que precise postar um tipo que o jogo nao
    consome, que falharia por um motivo sem relacao nenhuma com ele."""
    yield
    pygame.event.set_allowed(None)


@pytest.fixture(autouse=True)
def _reset_display():
    """pygame.SCALED exige um renderer SDL, e o driver dummy so permite um por
    processo — sem isso, o 2o+ set_mode(SCALED) do processo falha com
    'failed to create renderer' (varios testes criam Game() cada um; ver
    design.md secao 20.2)."""
    # antes de trocar o display: um renderizador de GPU orfao de um teste anterior so e
    # destruido numa passada do coletor ciclico, e se ela cair *depois* do
    # `display.init()` abaixo, o `Window.__del__` dele derruba a janela nova — o SDL
    # reaproveita os ponteiros. Recolher aqui destroi cada um ainda com o seu proprio
    # display vivo. Mesmo cuidado que `scripts/benchmark.py::_stop_counting` documenta;
    # passou a importar quando `Game.__init__` ganhou o `gc.collect()` de `tune_gc()`.
    gc.collect()
    pygame.display.quit()
    pygame.display.init()
