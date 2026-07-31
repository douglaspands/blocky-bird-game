# Matriz de rastreabilidade — v3

Uma linha por critério de aceitação de [`requirements.md`](requirements.md), ligando o
requisito à seção de [`design.md`](design.md) que o resolve, à task de
[`tasks.md`](tasks.md) que o implementa e ao(s) teste(s) que o comprovam.

O documento é vigiado por `tests/test_traceability.py`, que falha o build quando um critério
de aceitação não aparece aqui ou quando esta matriz referencia um teste inexistente (R32.2,
R32.3). É o que impede a matriz de envelhecer em silêncio.

> **Em construção — task 67.** A matriz é preenchida ao fim da v3, quando os testes que ela
> referencia já existem. Preenchê-la antes produziria referências a testes ainda não escritos,
> que é exatamente a condição que `tests/test_traceability.py` (task 68) trata como erro.

| Critério | Design | Task | Testes |
|---|---|---|---|
| _a preencher_ | | | |
