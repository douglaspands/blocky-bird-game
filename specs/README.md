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
| [v1](v1/) | concluída | Implementação completa do jogo, então chamado Blocky Bird (jogo base + biomas, áudio, controle Xbox, executável e CI/CD). Ver [v1/README.md](v1/README.md). |
| [v2](v2/) | concluída | Compatibilidade com Android (celular por toque, sempre em retrato), distribuído como APK instalável direto, sem abandonar o desktop; aumentos de escopo posteriores com conformidade `ruff`/`ty`, calibração de fonte, ícone do aplicativo com a personagem do jogo (tasks 36–37) e, por fim, orientação retrato travada com pillarbox eliminado por letterbox, removendo o suporte a Android TV (task 41). Ver [v2/README.md](v2/README.md). |
| [v3](v3/) | **atual** — em andamento | Renomeia o jogo para **Blocky Bee** e resolve o aproveitamento de tela em todos os sistemas operacionais: tela cheia com canvas lógico na proporção real do aparelho e área jogável fixa em 480×720, sem barra preta e **sem alterar a dificuldade** — o espaço que sobra vira faixa decorativa (céu estendido, terra funda, corte transversal do subsolo e mobs do Minecraft). Traz também render acelerado por GPU por padrão com todo o conteúdo estático pré-renderizado, timestep fixo, qualidade adaptativa, a camada de rigor SDD (docstrings obrigatórias, site de documentação, matriz de rastreabilidade verificada por teste e cobertura mínima no CI) e boas práticas de Git/GitHub (LICENSE, hooks de pre-commit espelhando o gate de CI, Dependabot). Ver [v3/README.md](v3/README.md). |

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
