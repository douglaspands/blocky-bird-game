"""Testes das funcoes puras do benchmark headless (R30.3, R30.4).

A execucao completa do benchmark nao e testada aqui de proposito: ela roda centenas
de frames de cinco cenarios e levaria mais que a suite inteira. O que se testa e a
estatistica, que e onde um erro passaria despercebido e contaminaria a comparacao
antes/depois de todas as tasks de otimizacao.
"""

from scripts.benchmark import Result, percentile


def test_percentile_lista_vazia():
    """Cenario sem amostras devolve 0.0 em vez de estourar."""
    assert percentile([], 0.5) == 0.0


def test_percentile_amostra_unica():
    """Com uma amostra so, qualquer percentil e ela mesma."""
    assert percentile([7.5], 0.95) == 7.5


def test_percentile_mediana():
    """A mediana de uma lista impar e o elemento do meio, independente da ordem de entrada."""
    assert percentile([3.0, 1.0, 2.0], 0.5) == 2.0


def test_percentile_interpola_entre_vizinhos():
    """Entre duas amostras, o percentil e interpolado linearmente."""
    assert percentile([0.0, 10.0], 0.5) == 5.0
    assert percentile([0.0, 10.0], 0.25) == 2.5


def test_percentile_p95_pega_a_cauda():
    """O p95 reflete a cauda que a mediana esconde: e para isso que ele existe no benchmark.

    Com 10% das amostras ruins, a mediana continua otima e o p95 acusa o problema —
    exatamente o engasgo periodico que a media mascararia.
    """
    samples = [1.0] * 90 + [100.0] * 10
    assert percentile(samples, 0.5) == 1.0
    assert percentile(samples, 0.95) > 1.0


def test_percentile_nao_altera_a_lista_recebida():
    """A ordenacao e interna: chamar duas vezes com a mesma lista da o mesmo resultado."""
    samples = [3.0, 1.0, 2.0]
    percentile(samples, 0.5)
    assert samples == [3.0, 1.0, 2.0]


def test_result_formata_linha_de_tabela_markdown():
    """A linha sai pronta para colar na tabela da secao 30 do design.md."""
    linha = Result("JOGANDO cave", 3.375, 5.7261, 81.4, 3.04).as_row()
    assert linha == "| JOGANDO cave | 3.38 | 5.73 | 81 | 3.0 |"
    assert linha.startswith("|") and linha.endswith("|")
