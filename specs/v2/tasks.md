# Plano de Implementação — Blocky Bird

Tarefas incrementais; cada uma referencia os requisitos que atende. Executar em ordem — cada tarefa deixa o jogo executável.

**Estado desta versão:** as tasks 1–19 são o histórico já concluído na v1 (mantidas aqui para o documento ser autocontido). As tasks **20–30 são o trabalho da v2** (Android) e estão pendentes.

As tasks 20–25 são todas implementáveis e testáveis **no desktop**, deliberadamente antes de mexer na cadeia de build Android — assim o risco de empacotamento (task 27, ver design seção 24.1) fica isolado no fim, e cada task anterior é verificável de imediato.

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

## Tarefas adicionais da v1 (pós-plano original)

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

---

## Tarefas da v2 — Android (pendentes)

Fase 1 — mudanças no jogo, testáveis no desktop (tasks 20–25). Fase 2 — cadeia de build e distribuição Android (tasks 26–30).

- [x] **20. Fonte bitmap própria, sem dependência do sistema**
  Implementar `pixelfont.py`: glifos 5×7 desenhados por código para `A-Z`, `0-9`, `:`, `/`, `!`, `-` e espaço, com `render(text, scale, color)` e cache. Trocar o `SysFont("couriernew")` de `ui.py` por essa fonte, preservando a sombra dura e a hierarquia de tamanhos das telas atuais. Validar visualmente que PRONTO, HUD, PAUSADO e GAME_OVER continuam legíveis e centralizados. _(R7.6, R7.5, R14.5)_
  **Ajuste feito na implementação:** a fonte bitmap é proporcionalmente mais larga que a `SysFont` antiga — mapear `base_size` direto para escala fixa estourava a largura da tela em 3 textos reais (`BLOCKY BIRD` 585px, `ESPACO / CLIQUE PARA VOAR` 745px, `ESPACO / CLIQUE PARA REINICIAR` 716px, todos > 480px). Adicionado `ui._fit_scale()`: reduz a escala automaticamente até o texto caber em `SCREEN_W - 40`, verificado para todas as strings reais do jogo.

- [x] **21. Resolução lógica escalável com letterbox**
  Passar `pygame.SCALED | pygame.RESIZABLE` no `set_mode` e verificar que o jogo mantém proporção ao redimensionar a janela (barras nas laterais/topo, sem distorção nem deslocamento do gameplay). Confirmar que o clique do mouse continua batendo com o que se vê.
  **Atenção — quebra conhecida:** `SCALED` sob `SDL_VIDEODRIVER=dummy` só permite um `set_mode` por processo, e `tests/test_game.py` cria `Game()` em 6 testes, então a suíte quebra sem ajuste. Incluir nesta task a fixture de `pygame.display.quit()` + `init()` no `conftest.py` (solução já verificada, ver design seção 20.2) e deixar a suíte passando. _(R9.1, R14.3)_
  **Validado:** janela real redimensionada para 900×500 (bem diferente de 480×720) mostrou pillarbox correto, sem distorção. Tradução de coordenada do mouse confirmada por instrumentação direta (script que registra `event.pos`): clique na coordenada lógica alvo `(5,5)` numa janela com offset de pillarbox de 202px foi reportado por `pygame` como `pos=(5, 5)` — exatamente `client_x - offset_x`; clique na barra preta (fora da área lógica) reportou `pos=(-101, 360)`, coordenada negativa fora da faixa válida, confirmando que o `pygame.SCALED` já entrega tudo em espaço lógico sem esforço adicional.

- [x] **22. Armazenamento do recorde por plataforma + gravação incremental**
  Implementar `storage.py` (`is_android()`, `save_dir()`) e apontar `score.py` para ele; mudar a gravação do recorde para o instante em que o score ultrapassa o recorde, em vez de só no GAME_OVER. Testes para os dois caminhos de plataforma e para a gravação incremental. _(R4.3, R4.5, R16.3, R16.4)_
  **Ajustes feitos na implementação:**
  - `score.py` resolve o caminho padrão dentro do corpo da função (`_default_path()`), não como valor de default de parâmetro (`path: Path = HIGHSCORE_PATH`) — um default de parâmetro é calculado uma única vez na importação do módulo, o que "congelaria" `storage.save_dir()` e tornaria o comportamento impossível de testar via monkeypatch (ou de reagir a uma mudança de plataforma em runtime).
  - Por consequência, a fixture `_isolate_cwd` do `conftest.py` (que já isolava `highscore.json` via `chdir`) precisou de um `monkeypatch.setattr("src.storage.save_dir", lambda: tmp_path)` — `storage.save_dir()` no desktop resolve a raiz do projeto via `__file__`, não mais o cwd, então só o `chdir` não bastava. Confirmado que sem esse ajuste os testes voltavam a escrever `highscore.json` na raiz real do projeto.
  - Essa mesma fixture autouse, por sua vez, impedia testar a implementação **real** de `storage.save_dir()` em `tests/test_storage.py` — resolvido chamando `monkeypatch.undo()` no início desses testes especificamente, revertendo a proteção só ali.
  - Validado fora do pytest também: rodando o jogo de verdade, o `highscore.json` é gravado na raiz real do projeto assim que o score ultrapassa o recorde, ainda em JOGANDO (antes de qualquer colisão).

- [x] **23. Entrada por toque e botão BACK**
  Tratar `FINGERDOWN` em `input.py` com conversão de coordenada normalizada → espaço lógico (desfazendo o letterbox), `K_AC_BACK` como ação `back`, e o desvio por estado no `Game` (pausa em JOGANDO, encerra fora dele). Adicionar o ícone de mudo tocável no canto da tela. Testar com eventos sintéticos, incluindo toque nas barras (deve ser ignorado). _(R15.1, R15.2, R15.3, R15.4)_
  **Ajuste feito na implementação:** o design previa só `FINGERDOWN` fazendo hit-test do ícone de mudo, mas o próprio design nota que o SDL sintetiza `MOUSEBUTTONDOWN` a partir do toque real — sem tratamento, tocar no ícone no Android dispararia `flap` *também* pelo evento de mouse sintético. Unificado num `_handle_tap()` compartilhado, usado tanto por `MOUSEBUTTONDOWN` (que já chega em coordenadas lógicas via `SCALED`) quanto por `FINGERDOWN` (convertido manualmente). `ui.MUTE_ICON_RECT` foi colocado em `ui.py` (onde o ícone é desenhado) e importado por `input.py` para o hit-test, mantendo desenho e geometria juntos.

- [x] **24. Pausa automática ao perder foco (ciclo de vida)**
  Tratar `APP_WILLENTERBACKGROUND`/`APP_DIDENTERBACKGROUND` (e `WINDOWFOCUSLOST` como fallback de desktop) como ação `focus_lost`, levando JOGANDO → PAUSADO e nunca retomando sozinho. Testável no desktop com alt-tab. _(R16.1, R16.2)_
  **Validado por evento sintético (`pytest`), não por alt-tab real:** a lógica (JOGANDO→PAUSADO ao perder foco, sem retomada automática, ignorado fora de JOGANDO, cobrindo tanto `WINDOWFOCUSLOST` quanto `APP_WILLENTERBACKGROUND`) está coberta por 4 testes com eventos postados diretamente. A tentativa de reproduzir com uma janela real e alt-tab neste ambiente (troca de foco via `SetForegroundWindow`) ficou inconclusiva — o pássaro chegou a GAME_OVER por simplesmente não receber nenhum flap durante os segundos do teste, independente do evento de foco ter disparado ou não; não há como isolar as duas causas de fora do processo sem instrumentação adicional. Como o código testado é exatamente o mesmo caminho que um alt-tab real percorre, considero a lógica coberta, mas recomendo uma checagem manual rápida (abrir o jogo, voar, alt-tab, voltar) antes de publicar.

- [x] **25. Compatibilidade de entrada com Android TV**
  Mapear `K_RETURN`/`K_KP_ENTER` para `flap` (botão central de controle remoto) e adicionar o mudo por D-pad ←/→ no overlay de PAUSADO, com a dica escrita na tela. Revisar que todo estado é alcançável sem toque e sem teclado completo. _(R14.4, R15.4, R15.5)_
  **Bug real encontrado na revisão de alcançabilidade (o próprio ponto que esta task pedia para checar):** `_flap_action()` não tratava `PAUSADO`, e o BACK em `PAUSADO` encerra o jogo (não despausa) — então quem pausasse via BACK (único jeito de pausar num controle remoto básico, sem tecla ESC/P nem botão Start de gamepad) ficava **sem nenhuma forma de despausar**, só de sair. O mesmo valia para quem só usa toque no celular. Corrigido fazendo `_flap_action()` também despausar (sem flapar o pássaro) quando `PAUSADO`. Validado de ponta a ponta com `test_bare_tv_remote_reaches_every_state`: simula um perfil de controle remoto básico (só setas, ENTER e voltar — sem toque, sem tecla M/ESC/P, sem gamepad) passando por todos os estados do jogo.

- [x] **26. Migração de `pygame` para `pygame-ce`**
  Trocar a dependência no `pyproject.toml`, recriar o ambiente (`uv sync`), rodar a suíte completa e validar o jogo no desktop. Nenhum `import` muda. Pré-requisito da cadeia de build Android. _(R9.2)_
  **`uv sync` trocou limpo** (desinstalou `pygame==2.6.1`, instalou `pygame-ce==2.5.7`, que também trouxe SDL 2.32.10 — versão mais nova que a 2.28.4 anterior). Isso quebrou 9 testes: sob `SDL_VIDEODRIVER=dummy`, `pygame.display.set_mode(..., SCALED)` no SDL novo enfileira uma sequência de eventos de janela (`WindowShown`, `WindowFocusGained/Lost`, `ActiveEvent` etc.) que não existia na versão antiga — incluindo um `WindowFocusLost` genuíno, que contaminava o `poll()` seguinte com uma ação `focus_lost` espúria. **Confirmado que é só um artefato do driver `dummy`**: rodando com driver de vídeo real, a mesma criação de janela não gera nenhum `WindowFocusLost` (só eventos neutros como `WindowShown`/`MouseMotion`). Corrigido com `pygame.event.clear()` logo após o `set_mode()`, tanto em `Game.__init__` (defensivo, produção) quanto nos testes que criam `InputManager` diretamente. Reconstruí o executável (`BlockyBird.spec`) e confirmei que ainda empacota e roda normal com `pygame-ce`.

- [x] **27. `buildozer.spec` e receita local do `pygame-ce`**
  Criar `buildozer.spec` (minapi 21, api 34, três ABIs, `orientation = all`, fullscreen) e a receita local em `p4a-recipes/pygame-ce/`. Injetar no manifesto o suporte a Android TV: `touchscreen` não obrigatório, categoria `LEANBACK_LAUNCHER` e banner 320×180 gerado por código. **Esta é a task de maior risco** (ver design seção 24.1: a receita não está mergeada no p4a upstream) — atacar cedo dentro da fase 2 e, se a receita não compilar, fixar a versão de `pygame-ce` conhecida como funcional. _(R17.1, R17.3, R17.4, R14.1, R14.2)_
  **Estado:** `buildozer.spec` fixa `p4a.branch = v2024.01.21` (última release do p4a antes de o hostpython3 passar a Python 3.14, que quebra o `setup.py` de todas as versões testadas do `pygame-ce` — `distutils.ccompiler.spawn` removido no Python 3.12+; achado real, documentado no próprio `buildozer.spec` e no design seção 24.1) e injeta `android/tv_extra_manifest.xml` (features de touchscreen/leanback opcionais) e `android/tv_intent_filter.xml` (categoria `LEANBACK_LAUNCHER`) via `android.extra_manifest_xml`/`android.manifest.intent_filters`. `scripts/generate_tv_banner.py` gera `assets/android_banner.png` (320×180, confirmado por inspeção do cabeçalho PNG) reaproveitando `pixelfont`/`textures` do próprio jogo, referenciado por `android.add_resources`.
  **Ajuste feito na revisão desta task:** a receita local (copiada do PR upstream kivy/python-for-android#2971) vinha fixada em `pygame-ce==2.4.0`, desalinhada da versão `2.5.7` já validada no desktop (task 26). Corrigido para `version = '2.5.7'` (tag confirmada existente no repositório `pygame-community/pygame-ce`), evitando ter duas versões de `pygame-ce` diferentes em voo entre desktop e Android; se essa versão não compilar no p4a (só verificável na task 28, sem Docker/Android neste ambiente — ver design seção 25), a saída documentada é fixar aqui a última versão conhecida como funcional.
  **Não verificável neste ambiente:** compilação real da receita (exige p4a + NDK/SDK Android, ver design seção 24.1/25) — fica para a task 28. `buildozer.spec` foi validado apenas como INI bem formado (`configparser`) e pela suíte `pytest` completa (63 testes, inalterada por esta task, já que nenhum código do jogo mudou).

- [ ] **28. Build local do APK e primeira instalação real**
  Gerar o APK via container Docker do Buildozer, instalar em aparelho físico e validar o loop básico (abre, joga por toque, som, recorde persiste após fechar e reabrir). Primeiro ponto em que o jogo roda de fato no Android. _(R17.1, R14.1)_

- [x] **29. Job de CI do APK na Release**
  Acrescentar ao `release.yml` um job `ubuntu-latest` independente que builda o APK em Docker, com cache de `~/.buildozer`, e anexa `BlockyBird-<tag>.apk` **sem compressão** aos assets — mantendo os dois assets de desktop já existentes. _(R17.2, R13.3)_
  **Implementação:** job `build-apk` em `.github/workflows/release.yml`, independente do job `build` (matriz Windows/Linux) para que uma falha na cadeia Android (a parte mais frágil, task 27) não impeça a publicação dos executáveis de desktop. `docker pull kivy/buildozer` + `docker run … kivy/buildozer android debug`, com `yes y |` porque a imagem recusa rodar como root e porque o primeiro build precisa aceitar as licenças do Android SDK interativamente. APK renomeado para `BlockyBird-<tag>.apk` e publicado via `softprops/action-gh-release@v2`, que copia o arquivo como está (o `.apk` já é um zip; a action não o recomprime).
  **Ajuste feito na implementação:** o `docker run` inicial só montava `${{ github.workspace }}:/home/user/hostcwd`, sem o segundo volume documentado pela própria imagem oficial (`kivy/buildozer` no Docker Hub) para persistir cache entre execuções — `-v "$HOME/.buildozer":/home/user/.buildozer`, onde SDK/NDK baixados ficam guardados fora do diretório do projeto. Sem esse mount, o cache de `actions/cache` no path `~/.buildozer` (pedido pelo design, seção 24.3) sempre voltaria vazio, forçando o download completo de SDK+NDK (30–60 min) em toda execução. Corrigido adicionando os dois volumes e cacheando ambos os paths (`~/.buildozer` e `.buildozer`) na mesma entrada de `actions/cache`.
  **Não verificável neste ambiente:** execução real do job (exige Docker + uma Release publicada no GitHub, ver design seção 25) — validado apenas como YAML bem formado (`yaml.safe_load`) e por leitura cruzada com a documentação oficial da imagem `kivy/buildozer` para confirmar os volumes/paths de cache corretos. Fica para a task 30 (ou uma release de teste) confirmar que o job efetivamente builda e anexa o APK.

- [ ] **30. Ajuste de áudio/performance no Android e verificação final da v2**
  Ajustar o buffer do mixer para Android e medir o tempo de frame em aparelho de entrada; completar o checklist manual em celular **e** em Android TV; atualizar o README com instruções de instalação do APK. _(R8.4, R9.5, R14.6, todos)_

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

## Checklist de verificação da v2 (Android)

Ver design seção 25 para o motivo da separação. Os itens de **hardware real** não podem
ser validados no ambiente de desenvolvimento e exigem teste manual do dono do projeto —
não marcar sem ter testado de fato no aparelho.

Verificável automaticamente / no desktop:

- [ ] Todas as telas renderizam com a fonte bitmap própria, sem `SysFont`, mantendo alinhamento (R7.6)
- [ ] Redimensionar a janela mantém a proporção com barras, sem distorcer nem deslocar o gameplay (R9.1, R14.3)
- [ ] Toque em coordenada normalizada converte corretamente para o espaço lógico; toque na barra é ignorado (R15.1)
- [ ] `storage.save_dir()` devolve o caminho Android quando `ANDROID_ARGUMENT` está definido e o caminho do projeto quando não está (R4.5)
- [ ] Recorde é gravado no momento em que o score ultrapassa o recorde, não só no GAME_OVER (R4.3, R16.4)
- [ ] Ação `back` pausa em JOGANDO e encerra nos outros estados (R15.2, R15.3)
- [ ] Perder foco da janela (alt-tab) leva JOGANDO → PAUSADO e não retoma sozinho (R16.1, R16.2)
- [ ] `K_RETURN` dispara flap (equivalente ao botão central de controle remoto) (R14.4)
- [ ] Suíte `pytest` completa continua passando após a migração para `pygame-ce` (R9.2)

Requer aparelho Android real (celular):

- [ ] APK instala por download direto, com "fontes desconhecidas", sem descompactar nada (R17.1, R17.2)
- [ ] Toque em qualquer ponto faz o pássaro voar; iniciar e reiniciar funcionam por toque (R15.1)
- [ ] Ícone de mudo responde ao toque e silencia de fato (R15.4)
- [ ] BACK pausa durante o jogo e encerra o app nas telas de PRONTO/PAUSADO/GAME_OVER (R15.2, R15.3)
- [ ] Trocar de app / receber ligação pausa automaticamente; ao voltar continua pausado (R16.1, R16.2)
- [ ] Recorde sobrevive a fechar e reabrir o app, e a encerramento forçado pelo sistema (R4.5, R16.4)
- [ ] Imagem preenche a tela na proporção correta, sem distorção nem corte de UI (R14.3)
- [ ] Áudio sem estouros/crepitação (R8.4, buffer do mixer)
- [ ] 60 FPS em aparelho de entrada (R9.5)

Requer Android TV real:

- [ ] App aparece na home da TV com o banner (R17.3)
- [ ] Jogo é totalmente operável pelo controle remoto, sem toque: iniciar, voar, pausar, reiniciar (R14.4)
- [ ] Mudo alcançável por D-pad na tela de PAUSADO (R15.4)
- [ ] Imagem em paisagem com pillarbox, UI inteira visível (sem corte por overscan) (R14.3)
