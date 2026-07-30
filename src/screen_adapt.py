"""Calcula a area jogavel/canvas reais a usar no `set_mode`, adaptados ao aspecto do aparelho (R14.3).

`pygame.SCALED` distribui a resolucao logica passada ao `set_mode` proporcionalmente
dentro da janela/tela real, sobrando letterbox/pillarbox quando o aspecto do canvas
difere do aspecto real. Este modulo decide, a partir do aspecto do aparelho, qual dos
dois mecanismos usar — cada um resolvido numa funcao pura, consumida por `game.py`:

- **Paisagem** (aparelho mais largo que a base 480x720 — Android TV 16:9):
  `adapted_canvas_size` estica a largura do canvas de FUNDO ate a proporcao bater
  exatamente; a area jogavel continua fixa em 480x720 (calibracao da task 12
  intocada), so o fundo (ceu/parallax) se estende pela largura extra. Comportamento
  das tasks 35/38, inalterado pela task 39.
- **Retrato** (aparelho mais estreito/alongado que a base, ou com a mesma proporcao —
  a esmagadora maioria dos celulares Android, e o desktop no tamanho de janela
  padrao): `portrait_height` devolve a altura JOGAVEL real (nao decorativa) que bate
  exatamente com a proporcao do aparelho, largura sempre fixa em 480. Task 35
  esticava a altura tambem nesse caso, mas so como fundo decorativo (revertido pela
  task 38 — a faixa extra "flutuando" acima do mundo jogavel confundia o
  entendimento do jogo). A task 39 retoma a ideia, mas certo: a altura extra vira
  area jogavel de verdade (pipes, chao e teto do passaro acompanham), eliminando o
  pillarbox sem inventar decoracao nem cortar nada. Ver design.md secao 20.1.3.
"""


def adapted_canvas_size(base_w: int, base_h: int, device_w: int, device_h: int) -> tuple[int, int]:
    """Estica a largura da base ate a proporcao bater com aparelhos em paisagem
    mais largos que a base (ex.: Android TV 16:9). Aparelhos em retrato (mais
    estreitos/alongados que a base, a maioria dos celulares), com dados
    invalidos, ou com a proporcao exatamente igual a base -> devolve a base
    sem alteracao (o caso retrato e tratado por `portrait_height`, nao aqui).
    """
    if device_w <= 0 or device_h <= 0:
        return base_w, base_h

    device_aspect = device_w / device_h
    base_aspect = base_w / base_h

    if device_aspect > base_aspect:
        return round(base_h * device_aspect), base_h
    return base_w, base_h


def portrait_height(base_w: int, base_h: int, device_w: int, device_h: int) -> int:
    """Devolve a altura jogavel real para aparelhos em retrato (mais estreitos/
    alongados que a base, ou com a mesma proporcao) — a largura logica continua
    fixa em `base_w`, e a altura acompanha exatamente a proporcao do aparelho,
    eliminando letterbox/pillarbox sem estender fundo (task 39).

    Aparelhos mais largos que a base (paisagem, ex. Android TV), ou com dados
    invalidos, devolvem `base_h` sem alteracao — esse caso e tratado por
    `adapted_canvas_size`, nao por esta funcao.
    """
    if device_w <= 0 or device_h <= 0:
        return base_h

    if device_w / device_h >= base_w / base_h:
        return base_h

    return round(base_w * device_h / device_w)
