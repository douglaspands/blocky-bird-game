"""Calcula a escala/letterbox que ajusta a resolucao logica fixa a uma janela real.

Nunca corta a imagem (R14.3). Ao contrario do zoom/corte (`cover`: cresce ate cobrir a janela inteira,
cortando o excedente de um dos eixos — usado ate a task 40), aqui a escala
usada e sempre a MENOR das duas (`fit`: encolhe ate caber inteiro na janela),
sobrando barra (letterbox/pillarbox) no eixo que nao bate — a mesma conta que
`pygame.SCALED` ja faz internamente para o mouse; `FINGERDOWN` chega sem essa
conversao pronta, entao `input.py` reaproveita esta funcao para desfaze-la
(task 41).
"""


def fit_scale(canvas_w: int, canvas_h: int, window_w: int, window_h: int) -> tuple[float, float, float]:
    """Calcula a escala e os offsets de letterbox de um canvas numa janela.

    Retorna `(escala, offset_x, offset_y)` para desenhar um canvas
    `canvas_w x canvas_h` inteiro dentro de uma janela `window_w x window_h`,
    sem cortar nada. Os offsets sao sempre >= 0 (a barra sobra, centralizada,
    nunca falta). Dados invalidos devolvem escala 1 sem deslocamento (nunca
    deveria ocorrer com uma janela real).
    """
    if canvas_w <= 0 or canvas_h <= 0 or window_w <= 0 or window_h <= 0:
        return 1.0, 0.0, 0.0

    scale = min(window_w / canvas_w, window_h / canvas_h)
    offset_x = (window_w - canvas_w * scale) / 2
    offset_y = (window_h - canvas_h * scale) / 2
    return scale, offset_x, offset_y
