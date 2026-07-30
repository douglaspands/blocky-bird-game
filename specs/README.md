# Specs — versionamento

Os documentos de spec-driven development (SDD) deste projeto vivem em pastas de
versão: `v1/`, `v2/`, `v3/`... Cada pasta é **completa e autocontida** — tem seu
próprio `requirements.md`, `design.md` e `tasks.md` refletindo o estado inteiro
do jogo naquele momento, não só o que mudou naquela versão.

A pasta de maior número é sempre a versão **atual**. Versões anteriores nunca são
editadas depois de concluídas — ficam como histórico.

## Versões

| Versão | Status | Descrição |
|---|---|---|
| [v1](v1/) | concluída | Implementação completa do Blocky Bird (jogo base + biomas, áudio, controle Xbox, executável e CI/CD). Ver [v1/README.md](v1/README.md). |

## Criando uma nova versão

Quando uma nova funcionalidade for pedida depois que a versão atual estiver
concluída:

1. Criar `specs/vN/` (N = número seguinte).
2. Copiar `requirements.md`, `design.md` e `tasks.md` da versão anterior para a
   nova pasta como ponto de partida.
3. Atualizar os três documentos para refletir a nova funcionalidade — novos
   requisitos (`R14`, `R15`... continuando a numeração), seção de design
   correspondente, e uma nova tarefa (ou tarefas) em `tasks.md`.
4. Criar `vN/README.md` (mesmo formato do [v1/README.md](v1/README.md)) com uma
   breve descrição do que a versão entrega.
5. Adicionar a nova versão na tabela acima.
6. Não editar as pastas de versões anteriores.
