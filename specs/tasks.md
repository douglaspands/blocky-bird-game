# Plano de Implementação — Blocky Bird

Tarefas incrementais; cada uma referencia os requisitos que atende. Executar em ordem — cada tarefa deixa o jogo executável.

- [x] **1. Esqueleto do projeto e loop básico**
  Inicializar o projeto com `uv init` (`pyproject.toml` com `pygame>=2.5` e `pytest` como dev; `uv sync`), criar estrutura de `src/`, `config.py` com constantes e `main.py`/`game.py` com janela 480×720, clock 60 FPS e loop de eventos que fecha com o X da janela. Validar `uv run main.py`. _(R9)_

- [x] **2. Texturas procedurais base**
  Implementar `textures.py`: gerador de bloco 16×16 com ruído + paletas `dirt`, `grass_side`, `stone`, e sprite da abelha; escala pixel-perfect para 48 px. Tela de teste exibindo os blocos. _(R7.1, R7.2)_

- [x] **3. Bird com física e animação**
  Implementar `bird.py`: gravidade, flap por ESPAÇO/↑/mouse, clamp no topo, rotação subida/queda, animação de asas. _(R1)_

- [x] **4. Obstáculos**
  Implementar `pipes.py`: spawn com abertura aleatória, movimento, remoção fora da tela, renderização como pilha de blocos com bloco de borda na abertura. _(R2)_

- [x] **5. Colisão e chão**
  Chão rolante de blocos; hitbox 85%; colisão pássaro×coluna e pássaro×chão encerra a rodada (por ora, reinicia direto). _(R3.1, R3.5, R7.3)_

- [x] **6. Máquina de estados e UI**
  Implementar `GameState` (PRONTO/JOGANDO/PAUSADO/GAME_OVER) e `ui.py`: tela inicial com idle bobbing, pausa com ESC/P, tela de game over com reinício, fonte pixelada com sombra. _(R6, R3.3, R3.4, R7.5)_

- [x] **7. Pontuação e recorde**
  Implementar `score.py`: +1 por coluna ultrapassada, HUD, persistência em `highscore.json` com fallback para arquivo ausente/corrompido, exibição do recorde no game over. _(R4)_

- [x] **8. Biomas e progressão de dificuldade**
  Implementar `biome.py`: os 3 biomas com thresholds 0/10/25, parâmetros de velocidade/abertura, texturas `cobblestone`/`netherrack`/`obsidian`, fade de céu ≤ 1 s e banner com nome do bioma. _(R5, R2.5)_

- [x] **9. Decoração de fundo com parallax**
  Duas camadas parallax por bioma: nuvens/colinas, estalactites/minérios, lava/pilares. _(R7.4)_

- [x] **10. Partículas**
  Implementar `particles.py` e disparar burst na colisão com cores da textura atingida. _(R3.2)_

- [x] **11. Áudio sintetizado**
  Implementar `sounds.py`: flap, score, hit, portal; tecla M para mudo; degradação graciosa sem mixer. Integrar aos eventos. _(R8, R3.2)_

- [x] **11b. Suporte a controle de Xbox**
  Implementar `input.py` (`InputManager`): mapear teclado/mouse/joystick para ações abstratas (A → voar/reiniciar, Start → pausar, Y → mudo), inicialização via `pygame.joystick` e hotplug com `JOYDEVICEADDED`/`JOYDEVICEREMOVED`. Refatorar os estados para consumir ações. _(R10)_

- [x] **12. Calibração de gameplay**
  Playtest e ajuste fino de `GRAVITY`, `FLAP_IMPULSE`, `PIPE_SPACING`, aberturas e velocidades por bioma até a curva de dificuldade ficar justa. _(R5.3, R9.1)_

- [x] **13. Testes e verificação final**
  Testes unitários (física, pipes, score, biomas, persistência) via `uv run pytest` com `SDL_VIDEODRIVER=dummy`; checklist manual cobrindo cada critério R1–R9; README curto com instruções de execução via `uv`. _(R9.3, todos)_

## Tarefas adicionais (pós-lançamento)

Pedidos feitos via chat após a conclusão do plano original (tasks 1–13). Cada uma
segue o mesmo padrão: implementação, validação (testes automatizados e/ou inspeção
visual) e commit.

- [x] **14. Correção de bug: hitbox das colunas maior que o sprite**
  `PIPE_W` (78 px) não batia com a largura realmente desenhada em `pipes.py` (`BLOCK`, 48 px), deixando uma faixa de colisão invisível de 30 px além do bloco visível — o pássaro colidia antes de tocar a coluna. Corrigido definindo `PIPE_W = BLOCK` em `config.py`. _(R3.1, R3.5)_

- [x] **15. Decoração quadriculada (nuvens/colinas blocky)**
  Nuvens e colinas do Overworld usavam `pygame.draw.ellipse`, destoando da estética voxel do resto do jogo. Substituídas por formas quadriculadas (pilhas de retângulos, com variantes seedadas por slot de parallax) em `decor.py`. _(R7.1, R7.4)_

- [x] **16. Créditos dos criadores**
  Nova constante `CREDITS` em `config.py` ("por Douglas e Pedro"), exibida na tela PRONTO logo abaixo do título e incluída no título da janela. _(R11)_

- [x] **17. Recorde em destaque na tela inicial**
  Exibe "RECORDE: N" no rodapé da tela PRONTO (texto dourado, sem caixa/contorno — iteração final após testar uma variante com painel), acima do chão, para aumentar a expectativa de bater o recorde antes de começar a partida. _(R12)_

- [x] **18. Executável standalone (PyInstaller)**
  `BlockyBird.spec` (onefile, sem console) permite gerar `dist/BlockyBird.exe` / `dist/BlockyBird` com `uv run pyinstaller BlockyBird.spec`, sem exigir Python nem `uv` na máquina de destino. `pyinstaller` adicionado como dependência de dev. _(R13.1)_

- [x] **19. CI/CD de release (GitHub Actions)**
  `.github/workflows/release.yml`: ao publicar uma Release com tag no GitHub, builda o executável para Windows e Linux (matriz de jobs) e anexa aos assets da release como `BlockyBird-windows-<tag>.zip` e `BlockyBird-linux-<tag>.tar.bz2` via `softprops/action-gh-release`. _(R13.2)_

## Checklist de verificação manual (task 13 + tarefas adicionais)

Itens marcados `[x]` foram validados automaticamente (suíte `pytest` ou scripts de
verificação usados durante o desenvolvimento das tasks 1–19), não por um humano
jogando de fato. Recomenda-se uma passada manual real antes de publicar, em especial
para os itens de áudio e controle físico (marcados abaixo), que dependem de
percepção humana e de hardware que não está disponível neste ambiente.

- [x] Flap responde a ESPAÇO, ↑, clique e botão A do controle (R1.1, R10.3) — testado com eventos simulados; botão A do controle não testado com hardware real
- [x] Start pausa, Y muta; conectar/desconectar controle durante o jogo não trava (R10.2, R10.3) — hotplug testado com joystick simulado, não com controle físico
- [x] Jogo funciona normalmente sem controle conectado (R10.5)
- [x] Pássaro não morre no teto, morre no chão e nas colunas (R1.4, R3.1); colisão com coluna só ocorre no bloco visível (R3.1, task 14)
- [x] Ponto único por coluna, com som (R4.1) — som verificado via chamada de `play()`, qualidade sonora não avaliada por ouvido humano
- [x] Recorde sobrevive a reinício do jogo (R4.3, R4.4)
- [x] Biomas trocam em 10 e 25 pontos com fade e banner (R5); nuvens/colinas do Overworld são quadriculadas, não elipses (R7.1, R7.4, task 15)
- [x] Pausa/despausa com ESC/P; reinício após game over (R6)
- [x] Partículas na colisão (R3.2); mudo com M (R8.3)
- [x] 60 FPS estáveis (~4.6 ms/frame médio, calibração da task 12); inicia com `uv run main.py` após `uv sync` (R9)
- [x] Créditos ("por Douglas e Pedro") visíveis na tela PRONTO e no título da janela (R11)
- [x] Recorde exibido no rodapé da tela PRONTO, acima do chão (R12)
- [x] `uv run pyinstaller BlockyBird.spec` gera um executável que abre com duplo clique, sem Python instalado (R13.1) — testado localmente no Windows; build Linux não testado neste ambiente (sem Linux disponível)
- [ ] Publicar uma Release de teste no GitHub e confirmar que os assets `BlockyBird-windows-<tag>.zip` e `BlockyBird-linux-<tag>.tar.bz2` aparecem automaticamente (R13.2) — workflow não pôde ser executado ponta a ponta neste ambiente (sem Docker acessível); validado apenas via `act --list` (sintaxe/gatilho) e execução manual do comando de build
