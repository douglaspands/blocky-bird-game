"""Calcula o canvas real a usar no `set_mode`, adaptado ao aspecto do aparelho (R14.3).

`pygame.SCALED` distribui a resolucao logica base (480x720) proporcionalmente
dentro da janela real, sobrando letterbox/pillarbox quando o aspecto do
aparelho difere do aspecto base — relatado como faixa preta nas laterais no
Galaxy S20 FE. Para preencher a tela sem distorcer nem cortar UI, este modulo
calcula um canvas maior que a base, esticando so o eixo que sobraria como
barra, ate a proporcao do canvas bater exatamente com a do aparelho. A area
jogavel (480x720) continua fixa — quem consome este calculo (`game.py`)
desenha o mundo/UI numa subsurface centralizada desse tamanho, e so as
camadas de fundo (ceu/parallax) se estendem pelo canvas inteiro.
"""


def adapted_canvas_size(base_w: int, base_h: int, device_w: int, device_h: int) -> tuple[int, int]:
    """Estica exatamente um dos eixos da base ate a proporcao bater com a do aparelho.

    Aparelho mais estreito/alongado que a base (a maioria dos celulares Android
    modernos) -> estica a altura. Aparelho mais largo que a base (ex.: Android TV
    16:9 em paisagem) -> estica a largura. Aparelho com dados invalidos ou com a
    proporcao exatamente igual a base -> devolve a base sem alteracao.
    """
    if device_w <= 0 or device_h <= 0:
        return base_w, base_h

    device_aspect = device_w / device_h
    base_aspect = base_w / base_h

    if device_aspect < base_aspect:
        return base_w, round(base_w / device_aspect)
    if device_aspect > base_aspect:
        return round(base_h * device_aspect), base_h
    return base_w, base_h
