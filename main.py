"""Ponto de entrada do Blocky Bee."""

import asyncio

# Sem uso direto: o pre-carregador de dependencias do pygbag e lexico e nao
# transitivo (so varre este arquivo, nao segue "from src.game import Game" ate
# achar o "import pygame" real em game.py/render.py) - sem esta linha, o wheel
# do pygame-ce nunca e buscado sob Emscripten (achado da spike da task 85).
import pygame  # noqa: F401

from src.game import Game


def main() -> None:
    """Cria o jogo e roda o laço principal até a janela fechar."""
    asyncio.run(Game().run())


if __name__ == "__main__":
    main()
