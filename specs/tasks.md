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

- [ ] **13. Testes e verificação final**
  Testes unitários (física, pipes, score, biomas, persistência) via `uv run pytest` com `SDL_VIDEODRIVER=dummy`; checklist manual cobrindo cada critério R1–R9; README curto com instruções de execução via `uv`. _(R9.3, todos)_

## Checklist de verificação manual (task 13)

- [ ] Flap responde a ESPAÇO, ↑, clique e botão A do controle (R1.1, R10.3)
- [ ] Start pausa, Y muta; conectar/desconectar controle durante o jogo não trava (R10.2, R10.3)
- [ ] Jogo funciona normalmente sem controle conectado (R10.5)
- [ ] Pássaro não morre no teto, morre no chão e nas colunas (R1.4, R3.1)
- [ ] Ponto único por coluna, com som (R4.1)
- [ ] Recorde sobrevive a reinício do jogo (R4.3, R4.4)
- [ ] Biomas trocam em 10 e 25 pontos com fade e banner (R5)
- [ ] Pausa/despausa com ESC/P; reinício após game over (R6)
- [ ] Partículas na colisão (R3.2); mudo com M (R8.3)
- [ ] 60 FPS estáveis; inicia com `uv run main.py` após `uv sync` (R9)
