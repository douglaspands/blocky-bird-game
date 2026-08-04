"""Ponto de entrada do Blocky Bee."""

from src.game import Game


def main() -> None:
    """Cria o jogo e roda o laço principal até a janela fechar."""
    Game().run()


if __name__ == "__main__":
    main()
