# Plano de Implementação — Blocky Bee

Tarefas incrementais; cada uma referencia os requisitos que atende. Executar em ordem — cada tarefa deixa o jogo executável.

**Estado desta versão:** as tasks 1–19 são o histórico já concluído na v1 (mantidas aqui para o documento ser autocontido). As tasks 20–30 são o trabalho da v2 (Android). As tasks 31–41 são aumentos de escopo posteriores da v2 (qualidade, correções pós-lançamento, o ícone do aplicativo e o ajuste final de resolução/orientação), também já concluídas. **As tasks 42–73 são o trabalho da v3** — identidade, aproveitamento de tela com faixas decorativas, render acelerado por GPU, desempenho, timestep fixo, qualidade adaptativa e a camada de documentação/rastreabilidade.

As tasks 20–25 são todas implementáveis e testáveis **no desktop**, deliberadamente antes de mexer na cadeia de build Android — assim o risco de empacotamento (task 27, ver design seção 24.1) fica isolado no fim, e cada task anterior é verificável de imediato.

A ordem das tasks da v3 também é deliberada: **renomear → medir → definir o canvas → trocar o backend de render → construir o atlas → alocação/GC → loop → adaptar → documentar**. O rename vem primeiro para que nada novo nasça com o nome velho; a instrumentação vem antes das otimizações para que cada ganho seja medido em vez de suposto; o canvas vem antes do backend porque define o tamanho lógico que o renderizador recebe; e o backend vem antes do atlas porque é ele quem transforma superfície em textura. As tasks 42–71 são todas verificáveis **no desktop**, deixando o build Android isolado no fim (tasks 72–73), pela mesma razão da v2.

**Numeração:** a v2 terminou na task 41, com lacunas em 35/38/39/40 (iterações revertidas, removidas no commit `6009b5e`). A v3 começa em 42 e não reaproveita as lacunas, para que o número da task continue sendo uma referência estável no histórico e nos documentos.

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
  `BlockyBee.spec` (onefile, sem console) permite gerar `dist/BlockyBee.exe` / `dist/BlockyBee` com `uv run pyinstaller BlockyBee.spec`, sem exigir Python nem `uv` na máquina de destino. `pyinstaller` adicionado como dependência de dev. _(R13.1)_

- [x] **19. CI/CD de release (GitHub Actions)**
  `.github/workflows/release.yml`: ao publicar uma Release com tag no GitHub, builda o executável para Windows e Linux (matriz de jobs) e anexa aos assets da release como `BlockyBee-windows-x64-<tag>.zip` e `BlockyBee-linux-x64-<tag>.tar.bz2` via `softprops/action-gh-release`; nome do asset inclui plataforma e arquitetura. _(R13.2)_

---

## Tarefas da v2 — Android (pendentes)

Fase 1 — mudanças no jogo, testáveis no desktop (tasks 20–25). Fase 2 — cadeia de build e distribuição Android (tasks 26–30).

- [x] **20. Fonte bitmap própria, sem dependência do sistema**
  Implementar `pixelfont.py`: glifos 5×7 desenhados por código para `A-Z`, `0-9`, `:`, `/`, `!`, `-` e espaço, com `render(text, scale, color)` e cache. Trocar o `SysFont("couriernew")` de `ui.py` por essa fonte, preservando a sombra dura e a hierarquia de tamanhos das telas atuais. Validar visualmente que PRONTO, HUD, PAUSADO e GAME_OVER continuam legíveis e centralizados. _(R7.6, R7.5, R14.5)_
  **Ajuste feito na implementação:** a fonte bitmap é proporcionalmente mais larga que a `SysFont` antiga — mapear `base_size` direto para escala fixa estourava a largura da tela em 3 textos reais (`BLOCKY BEE` 585px, `ESPACO / CLIQUE PARA VOAR` 745px, `ESPACO / CLIQUE PARA REINICIAR` 716px, todos > 480px). Adicionado `ui._fit_scale()`: reduz a escala automaticamente até o texto caber em `SCREEN_W - 40`, verificado para todas as strings reais do jogo.

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

- [x] **25. Mapeamentos adicionais de teclado e correção de alcançabilidade em PAUSADO**
  Mapear `K_RETURN`/`K_KP_ENTER` para `flap` e adicionar o mudo por setas ←/→ no overlay de PAUSADO, com a dica escrita na tela. Revisar que todo estado é alcançável sem toque e sem gamepad. _(R15.4, R15.5)_
  **Bug real encontrado na revisão de alcançabilidade (o próprio ponto que esta task pedia para checar):** `_flap_action()` não tratava `PAUSADO`, e o BACK em `PAUSADO` encerra o jogo (não despausa) — então quem pausasse via BACK (sem tecla ESC/P nem botão Start de gamepad) ficava **sem nenhuma forma de despausar**, só de sair. O mesmo valia para quem só usa toque no celular. Corrigido fazendo `_flap_action()` também despausar (sem flapar o pássaro) quando `PAUSADO`. Validado de ponta a ponta com `test_bare_tv_remote_reaches_every_state`: simula um perfil de entrada básico (só setas, ENTER e voltar — sem toque, sem tecla M/ESC/P, sem gamepad) passando por todos os estados do jogo.

- [x] **26. Migração de `pygame` para `pygame-ce`**
  Trocar a dependência no `pyproject.toml`, recriar o ambiente (`uv sync`), rodar a suíte completa e validar o jogo no desktop. Nenhum `import` muda. Pré-requisito da cadeia de build Android. _(R9.2)_
  **`uv sync` trocou limpo** (desinstalou `pygame==2.6.1`, instalou `pygame-ce==2.5.7`, que também trouxe SDL 2.32.10 — versão mais nova que a 2.28.4 anterior). Isso quebrou 9 testes: sob `SDL_VIDEODRIVER=dummy`, `pygame.display.set_mode(..., SCALED)` no SDL novo enfileira uma sequência de eventos de janela (`WindowShown`, `WindowFocusGained/Lost`, `ActiveEvent` etc.) que não existia na versão antiga — incluindo um `WindowFocusLost` genuíno, que contaminava o `poll()` seguinte com uma ação `focus_lost` espúria. **Confirmado que é só um artefato do driver `dummy`**: rodando com driver de vídeo real, a mesma criação de janela não gera nenhum `WindowFocusLost` (só eventos neutros como `WindowShown`/`MouseMotion`). Corrigido com `pygame.event.clear()` logo após o `set_mode()`, tanto em `Game.__init__` (defensivo, produção) quanto nos testes que criam `InputManager` diretamente. Reconstruí o executável (`BlockyBee.spec`) e confirmei que ainda empacota e roda normal com `pygame-ce`.

- [x] **27. `buildozer.spec` e receita local do `pygame-ce`**
  Criar `buildozer.spec` (minapi 21, api 34, três ABIs, orientação retrato, fullscreen) e a receita local em `p4a-recipes/pygame-ce/`. **Esta é a task de maior risco** (ver design seção 24.1: a receita não está mergeada no p4a upstream) — atacar cedo dentro da fase 2 e, se a receita não compilar, fixar a versão de `pygame-ce` conhecida como funcional. _(R17.1, R14.1, R14.2)_
  **Estado:** `buildozer.spec` fixa `p4a.branch = v2024.01.21` (última release do p4a antes de o hostpython3 passar a Python 3.14, que quebra o `setup.py` de todas as versões testadas do `pygame-ce` — `distutils.ccompiler.spawn` removido no Python 3.12+; achado real, documentado no próprio `buildozer.spec` e no design seção 24.1).
  **Ajuste feito na revisão desta task:** a receita local (copiada do PR upstream kivy/python-for-android#2971) vinha fixada em `pygame-ce==2.4.0`, desalinhada da versão `2.5.7` já validada no desktop (task 26). Corrigido para `version = '2.5.7'` (tag confirmada existente no repositório `pygame-community/pygame-ce`), evitando ter duas versões de `pygame-ce` diferentes em voo entre desktop e Android; se essa versão não compilar no p4a (só verificável na task 28, sem Docker/Android neste ambiente — ver design seção 25), a saída documentada é fixar aqui a última versão conhecida como funcional.
  **Não verificável neste ambiente:** compilação real da receita (exige p4a + NDK/SDK Android, ver design seção 24.1/25) — fica para a task 28. `buildozer.spec` foi validado apenas como INI bem formado (`configparser`) e pela suíte `pytest` completa (63 testes, inalterada por esta task, já que nenhum código do jogo mudou).

- [x] **28. Build local do APK e primeira instalação real**
  Gerar o APK via container Docker do Buildozer, instalar em aparelho físico e validar o loop básico (abre, joga por toque, som, recorde persiste após fechar e reabrir). Primeiro ponto em que o jogo roda de fato no Android. _(R17.1, R14.1)_
  **Estado:** Docker ficou disponível neste ambiente (ao contrário do que o design.md/task 27 assumiam) e o build real via `docker run kivy/buildozer android debug` foi executado até `BUILD SUCCESSFUL`, gerando `bin/blockybee-0.2.0-armeabi-v7a_arm64-v8a_x86_64-debug.apk` (62 MB, as 3 ABIs). Vários bugs reais só apareciam nesta etapa (nunca antes exercida) e foram corrigidos:
  - Cache `.buildozer` de uma tentativa anterior tinha `hostpython3` compilado como CPython 3.14 em vez do 3.11.5 esperado do pin `p4a.branch = v2024.01.21` — cache limpo para forçar reclone correto.
  - `docker run -v "$(pwd):..."` a partir do Git Bash montava um volume anônimo vazio em vez do diretório do projeto (path mangling do MSYS) — corrigido com `MSYS_NO_PATHCONV=1`.
  - O cache real do Android SDK/NDK do buildozer vive em `$HOME/.buildozer` **dentro do container** (efêmero a cada `docker run --rm`), mas o marcador "já instalado" fica em `.buildozer/state.db` do projeto (persistido via bind mount) — a inconsistência fazia `platforms;android-34` nunca ser reinstalado em containers novos ("Available Android APIs are ()"). Corrigido montando um diretório persistente do host (`~/.buildozer-android-global-cache`) também em `/home/user/.buildozer`.
  - `p4a-recipes/jpeg/__init__.py` (nova receita local): o `CMakeLists.txt` do libjpeg-turbo 2.0.1 exige `cmake_minimum_required` < 3.5, incompatível com o CMake 4.2.3 do container — corrigido com `-DCMAKE_POLICY_VERSION_MINIMUM=3.5` direto na chamada (variável de ambiente via `docker -e` não chega ao subprocesso, pois `Arch.get_env()` do p4a monta o ambiente do zero); `rm -f` trocado por `rm -rf` para sobreviver a retries.
  - `p4a-recipes/pygame-ce/__init__.py`: faltava `'cython'` em `depends` (a cópia do PR upstream não declarava, ao contrário de outras receitas do p4a que compilam `.pyx`) — `setup.py build_ext` falhava com "You need cython".
  - `p4a-recipes/pygame-ce/__init__.py`: `sdl_image_includes` apontava para a raiz de `jni/SDL2_image`, mas a versão do sdl2_image (2.8.0) move o header público para `jni/SDL2_image/include/SDL_image.h` (diferente do `SDL2_ttf`, que mantém `SDL_ttf.h` na raiz) — `src_c/imageext.c` falhava com "'SDL_image.h' file not found".
  **Não verificável neste ambiente:** instalação e playtest em aparelho físico (sem Android real disponível) — pendente de validação manual pelo dono do projeto antes de publicar.

- [x] **29. Job de CI do APK na Release**
  Acrescentar ao `release.yml` um job `ubuntu-latest` independente que builda o APK em Docker, com cache de `~/.buildozer`, e anexa `BlockyBee-<tag>.apk` **sem compressão** aos assets — mantendo os dois assets de desktop já existentes. _(R17.2, R13.3)_
  **Implementação:** job `build-apk` em `.github/workflows/release.yml`, independente do job `build` (matriz Windows/Linux) para que uma falha na cadeia Android (a parte mais frágil, task 27) não impeça a publicação dos executáveis de desktop. `docker pull kivy/buildozer` + `docker run … kivy/buildozer android debug`, com `yes y |` porque a imagem recusa rodar como root e porque o primeiro build precisa aceitar as licenças do Android SDK interativamente. APK renomeado para `BlockyBee-<tag>.apk` e publicado via `softprops/action-gh-release@v2`, que copia o arquivo como está (o `.apk` já é um zip; a action não o recomprime).
  **Ajuste feito na implementação:** o `docker run` inicial só montava `${{ github.workspace }}:/home/user/hostcwd`, sem o segundo volume documentado pela própria imagem oficial (`kivy/buildozer` no Docker Hub) para persistir cache entre execuções — `-v "$HOME/.buildozer":/home/user/.buildozer`, onde SDK/NDK baixados ficam guardados fora do diretório do projeto. Sem esse mount, o cache de `actions/cache` no path `~/.buildozer` (pedido pelo design, seção 24.3) sempre voltaria vazio, forçando o download completo de SDK+NDK (30–60 min) em toda execução. Corrigido adicionando os dois volumes e cacheando ambos os paths (`~/.buildozer` e `.buildozer`) na mesma entrada de `actions/cache`.
  **Não verificável neste ambiente:** execução real do job (exige Docker + uma Release publicada no GitHub, ver design seção 25) — validado apenas como YAML bem formado (`yaml.safe_load`) e por leitura cruzada com a documentação oficial da imagem `kivy/buildozer` para confirmar os volumes/paths de cache corretos. Fica para a task 30 (ou uma release de teste) confirmar que o job efetivamente builda e anexa o APK.

- [x] **30. Ajuste de áudio/performance no Android e verificação final da v2**
  Ajustar o buffer do mixer para Android e medir o tempo de frame em aparelho de entrada; completar o checklist manual em celular; atualizar o README com instruções de instalação do APK. _(R8.4, R9.5, R14.6, todos)_
  **Implementado e verificável neste ambiente:** `sounds.py` agora chama `pygame.mixer.init(..., buffer=1024)` quando `storage.is_android()` é verdadeiro (mantendo o default do pygame no desktop, sem regressão), conforme o valor inicial documentado no design (seção 11) — `2048` fica como próximo passo caso o playtest real em aparelho ainda acuse estouro/crepitação com `1024`. Coberto por `tests/test_sounds.py` (2 testes, mockando `is_android` e `pygame.mixer.init` para inspecionar os kwargs passados). README atualizado com seção "Instalar no Android" (fontes desconhecidas, controles por toque/BACK, requisito de API 21) e o comando `docker run` para reproduzir o build do APK localmente. Suíte completa: 65 testes passando.
  **Não verificável neste ambiente (sem Android real nem emulador, ver design seção 25):** medir o tempo de frame em aparelho de entrada (R9.5), confirmar que `buffer=1024` de fato elimina estouros/crepitação no hardware real (R8.4) — se não eliminar, subir para `ANDROID_MIXER_BUFFER = 2048` em `sounds.py` — e os itens de checklist abaixo marcados como "requer aparelho Android real". Ficam pendentes de validação manual pelo dono do projeto antes de considerar a v2 encerrada.

## Correção pós-lançamento — Tela cheia no Android sem pillarbox, sempre em retrato

Pedido do dono do projeto: no Android, a tela deve ser preenchida sem barra visível nas laterais, e o jogo deve rodar sempre em retrato (nunca em paisagem, mesmo que o aparelho gire).

- [x] **41. Travar orientação retrato e preencher a tela via letterbox (`pygame.SCALED`)**
  `buildozer.spec`: `orientation = portrait`, `fullscreen = 1`. `src/game.py::Game.__init__` usa `pygame.SCALED | pygame.RESIZABLE` (mesmo mecanismo da task 21) sem nenhum branch por plataforma — resolução lógica fixa 480×720 em qualquer aparelho, escalada para a janela/tela real mantendo a proporção; o excedente de um dos eixos vira barra de letterbox, nunca corta a imagem. `src/scale.py::fit_scale(canvas_w, canvas_h, window_w, window_h)` calcula a escala (mínimo dos dois fatores de eixo) e os offsets do letterbox, usado por `input.py` para converter toque (`FINGERDOWN`) em coordenada lógica — `MOUSEBUTTONDOWN` já chega pré-convertido pelo próprio `pygame.SCALED`. Toque na barra de letterbox é ignorado (não dispara `flap`/`mute`). Ver design.md seção 20. _(R9.1, R14.3, R14.4, R15.1, R15.4)_
  **Por que travar a orientação elimina o pillarbox:** com `pygame.SCALED` (escala = menor dos dois fatores de eixo), pillarbox (barra lateral) só ocorre quando a janela é proporcionalmente mais larga que o jogo (2:3). Travado em retrato, a janela do Android nunca fica mais larga que alta — a esmagadora maioria dos celulares é mais alongada que 2:3 — então a barra que sobra é sempre letterbox (topo/base), nunca pillarbox.
  **Testes:** `tests/test_scale.py` (`fit_scale` — janela mais larga → letterbox vertical, mais alta → letterbox horizontal, e a invariante de que o canvas escalado nunca excede a janela). `tests/test_game.py::test_screen_uses_fixed_logical_resolution_via_scaled` (confirma `game.screen.get_size() == (480, 720)`, independente de plataforma). `tests/test_input.py::test_finger_tap_outside_logical_area_is_ignored` (toque na barra de letterbox é ignorado).
  **Suíte completa (86 testes) verde; `ruff check`/`ruff format --check`/`ty check` sem violações.** Validado com `uv run main.py` (driver de vídeo real, não headless): janela abre em 480×720 sem exceção.
  **Não verificável neste ambiente:** confirmar visualmente em celular Android real que a orientação fica travada em retrato e que não sobra pillarbox nas laterais (mesma limitação da seção 25) — fica pendente de validação manual do dono do projeto.

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
- [x] `uv run pyinstaller BlockyBee.spec` gera um executável que abre com duplo clique, sem Python instalado (R13.1) — testado localmente no Windows; build Linux não testado neste ambiente (sem Linux disponível)
- [x] Publicar uma Release de teste no GitHub e confirmar que os assets `BlockyBee-windows-<tag>.zip` e `BlockyBee-linux-<tag>.tar.bz2` aparecem automaticamente (R13.2) — Release `v1.0.0` publicada em `douglaspands/blocky-bird-game`, com `BlockyBee-linux-v1.0.0.tar.bz2` e `BlockyBee-windows-v1.0.0.zip` anexados automaticamente pelo `github-actions[bot]`, confirmado via API pública do GitHub

## Checklist de verificação da v2 (Android)

Ver design seção 25 para o motivo da separação. Os itens de **hardware real** não podem
ser validados no ambiente de desenvolvimento e exigem teste manual do dono do projeto —
não marcar sem ter testado de fato no aparelho.

Verificável automaticamente / no desktop:

- [x] Todas as telas renderizam com a fonte bitmap própria, sem `SysFont`, mantendo alinhamento (R7.6) — confirmado por inspeção (`grep SysFont src/`: só ocorre em comentários explicativos, nenhum uso real) e visualmente durante a task 20
- [x] Redimensionar a janela do desktop reamostra o letterbox automaticamente (`pygame.SCALED`), preservando a proporção do jogo (não da tela) e sem distorcer nem deslocar o gameplay (R9.1, R14.3) — validado com janela real redimensionada ao vivo para tamanhos bem diferentes da base 480×720
- [x] Toque/clique em coordenada normalizada converte corretamente para o espaço lógico, respeitando o letterbox; toque na barra é ignorado (R15.1) — `tests/test_input.py::test_finger_tap_in_game_area_flaps`, `test_finger_tap_outside_logical_area_is_ignored`
- [x] `storage.save_dir()` devolve o caminho Android quando `ANDROID_ARGUMENT` está definido e o caminho do projeto quando não está (R4.5) — `tests/test_storage.py`
- [x] Recorde é gravado no momento em que o score ultrapassa o recorde, não só no GAME_OVER (R4.3, R16.4) — `tests/test_game.py::test_highscore_saved_incrementally_mid_round`
- [x] Ação `back` pausa em JOGANDO e encerra nos outros estados (R15.2, R15.3) — `tests/test_game.py::test_back_in_*`
- [x] Perder foco da janela (alt-tab) leva JOGANDO → PAUSADO e não retoma sozinho (R16.1, R16.2) — `tests/test_game.py::test_focus_lost_*`
- [x] `K_RETURN` dispara flap (equivalente ao botão central de controle remoto) (R14.4) — `tests/test_input.py::test_return_and_kp_enter_flap`
- [x] Suíte `pytest` completa continua passando após a migração para `pygame-ce` (R9.2) — 65 testes, `SDL_VIDEODRIVER=dummy uv run pytest`
- [x] A área jogável é sempre 480×720 fixo, em qualquer aparelho (calibração de dificuldade da task 12 nunca muda); `pygame.SCALED` aplica letterbox automático sem cortar a imagem, e a orientação fica travada em retrato no Android (R14.3, R14.4) — `tests/test_scale.py`, `tests/test_game.py::test_screen_uses_fixed_logical_resolution_via_scaled`

Requer aparelho Android real (celular):

- [x] APK instala por download direto, com "fontes desconhecidas", sem descompactar nada (R17.1, R17.2)
- [x] Toque em qualquer ponto faz o pássaro voar; iniciar e reiniciar funcionam por toque (R15.1)
- [x] Ícone de mudo responde ao toque e silencia de fato (R15.4)
- [x] BACK pausa durante o jogo e encerra o app nas telas de PRONTO/PAUSADO/GAME_OVER (R15.2, R15.3)
- [x] Trocar de app / receber ligação pausa automaticamente; ao voltar continua pausado (R16.1, R16.2)
- [x] Recorde sobrevive a fechar e reabrir o app, e a encerramento forçado pelo sistema (R4.5, R16.4)
- [x] A orientação fica travada em retrato mesmo girando o aparelho, e a imagem preenche a tela sem pillarbox nas laterais (letterbox no topo/base é aceitável, desde que a imagem inteira continue visível) (R14.3, R14.4)
- [x] Áudio sem estouros/crepitação (R8.4, buffer do mixer)
- [x] 60 FPS em aparelho de entrada (R9.5)
- [x] Ícone do launcher mostra a abelha inteira, sem cortar antenas/asas, em qualquer forma de máscara do fabricante (R21.4, R21.5) — task 37

## Tarefas adicionais da v2 (pós-Android) — Qualidade

Aumento de escopo pedido depois que as tasks 20–30 (Android) já estavam concluídas: conformidade com `ruff` em todo o código Python, calibração do tamanho de fonte para eliminar sobreposição de texto nas telas, correção de bug de persistência do recorde no executável empacotado, e conformidade com `ty` (checagem de tipos).

- [x] **31. Conformidade com Ruff**
  Adicionar `ruff` como dependência de dev (`uv add --dev ruff`), configurar `[tool.ruff]` em `pyproject.toml` (`line-length = 110`, `target-version = "py310"`, regras `E, F, W, I, UP, B, SIM, RUF`, ver design seção 26). Rodar `uv run ruff check --fix .` e `uv run ruff format .` sobre `main.py`, `src/`, `tests/`, `scripts/`, `p4a-recipes/`; revisar manualmente qualquer correção automática que mude comportamento (não só estilo) antes de aceitar. Corrigir à mão o que `--fix` não resolver. Criar `.github/workflows/ci.yml` (`on: push, pull_request`) rodando `ruff check`, `ruff format --check` e `pytest` (`SDL_VIDEODRIVER=dummy`) no mesmo job. Confirmar `uv run pytest` completo continua verde após as correções de lint. _(R18)_
  **Ajuste feito na implementação:** `uv run ruff format .` reformata por padrão também blocos de código Python dentro de cercas ```` ```python ```` em arquivos `.md` (comportamento desta versão do ruff, 0.16.0) — isso reformatou `specs/v1/design.md`, violando a regra do próprio projeto de nunca editar pastas de versões anteriores já concluídas (`specs/README.md`). Corrigido com `extend-exclude = ["specs"]` em `[tool.ruff]`, restringindo a varredura de fato ao código do jogo (o escopo já pretendido pelo design, que nunca mencionava `specs/`).
  **Violações reais encontradas (15 no total, 7 corrigidas por `--fix`, 8 à mão):** auto-fix foi só estilo (ordenação de imports em `p4a-recipes/jpeg/__init__.py`, `.format()` → f-string, `noqa` órfão, `typing.Callable` → `collections.abc.Callable` em `decor.py`). À mão: `RUF012` (atributos de classe mutáveis `built_libraries`/`depends` nas receitas p4a — anotados com `ClassVar`, já que são o padrão de configuração do próprio framework p4a, não um bug real); `SIM115` (dois `open()` sem context manager em `p4a-recipes/pygame-ce/__init__.py` — convertidos para `with`); `B905` (dois `zip()` sem `strict=` em `src/biome.py` e `scripts/generate_app_icon.py` — ambos combinam tuplas RGB de tamanho fixo e igual, `strict=True` é correto e não muda comportamento); `E501` (duas docstrings de uma linha em `src/biome.py`/`src/pipes.py` acima de 110 colunas — quebradas em docstring de duas linhas, sem alterar o texto).
  **Suíte completa (65 testes) permanece verde após todas as correções.**

- [x] **32. Calibração de tamanho de fonte sem sobreposição**
  Implementar `ui._stack()` (empilhamento vertical por altura real de linha, ver design seção 27) e migrar `draw_ready_screen`, `draw_paused_overlay` e `draw_game_over_screen` para usá-lo em vez dos deltas fixos em pixels atuais. Revisar visualmente (`uv run main.py`) o `base_size`/escala de cada papel de texto (título, créditos, instrução, HUD, overlay de pausa, textos de game over, recorde) até nenhuma sobreposição ser visível em nenhuma das quatro telas, registrando os valores finais escolhidos. Criar `tests/test_ui_layout.py` com um teste por tela que renderiza os textos reais (incluindo `RECORDE: 999999` para o caso de recorde com muitos dígitos) e assere que nenhum par de retângulos se sobrepõe e que todos ficam dentro de `[20, SCREEN_W - 20]` horizontalmente e fora da área do chão verticalmente; incluir o retângulo do ícone de mudo (`ui.MUTE_ICON_RECT`) na checagem das telas onde ele aparece. _(R19)_
  **`ui._stack(surface, center_x, top_y, lines, margin=8)` implementado:** recebe `(text, base_size, color)` na ordem de exibição, calcula a escala real de cada linha via `_fit_scale`/`_scale_for` já existentes, delega o desenho a `draw_text` (mesma função usada fora do stack, o que manteve um único ponto de instrumentação para os testes) e avança a posição vertical por `GLYPH_H * escala + SHADOW_OFFSET + margin` — nunca por uma constante escolhida a olho.
  **`base_size` finais escolhidos (calibração visual via screenshots offscreen com as telas reais, incluindo `RECORDE: 999999`):** título (`BLOCKY BEE`/`PAUSADO`/`GAME OVER`) `base_size=12` (escala 6, contra 18/escala 9 antes); texto secundário de destaque (`PONTOS`/`RECORDE` no game over) `base_size=8` (escala 4, igual ao recorde da tela PRONTO); instrução/dica (`ESPACO / CLIQUE PARA VOAR`, `ESPACO / CLIQUE PARA REINICIAR`, `SETAS: MUDO`) `base_size=5`-`6` (escala 2-3); créditos `base_size=5` (escala 2); HUD de score `base_size=12` (escala 6, reduzido de 20/escala 10 — o valor antigo já quase tocava o topo da tela). Nenhuma sobreposição visível nas quatro telas nem no pior caso (`RECORDE: 999999`); confirmado também com um smoke test real (`uv run main.py`) sem exceptions.
  **`tests/test_ui_layout.py`:** `_rects_for_screen` monkeypatcha `ui.draw_text` (interceptado também dentro de `_stack`, já que é a mesma função do módulo) para capturar, por linha, um `pygame.Rect` de texto+sombra sem duplicar a lógica de renderização. Um teste por tela (PRONTO, HUD, PAUSADO, GAME_OVER) chama isso com os textos reais — incluindo `999999` — e verifica ausência de sobreposição (incluindo contra `ui.MUTE_ICON_RECT`, presente em todas as telas pois `game.py` o desenha incondicionalmente) e que cada retângulo de texto fica em `[20, SCREEN_W - 20]` horizontalmente e acima de `GROUND_Y` verticalmente. `MUTE_ICON_RECT` entra só na checagem de colisão, não na de limites horizontais — ele fica a propósito perto da borda direita (dentro da margem de 14px do ícone, não da margem de 20px do texto). Suíte completa: 69 testes (65 + 4 novos), `SDL_VIDEODRIVER=dummy uv run pytest`.

- [x] **33. Corrigir persistência do recorde no executável Windows/Linux empacotado**
  Bug reportado pelo dono do projeto: no executável Windows gerado por `BlockyBee.spec`, o recorde deixou de persistir e `highscore.json` não era mais criado ao lado do `.exe`. Causa raiz: `storage.save_dir()` resolvia o diretório desktop a partir de `Path(__file__).resolve().parent.parent`, mas o PyInstaller empacota em modo **onefile** (`EXE(pyz, a.scripts, a.binaries, a.datas, ...)` numa única chamada), e nesse modo `__file__` do módulo aponta para o diretório temporário de extração (`sys._MEIPASS`), apagado ao fechar o processo — nunca para a pasta real do executável. O mesmo problema afeta o build Linux (mesmo `.spec`), ainda não reportado. Corrigido em `storage.py` com `is_frozen()` (checa `sys.frozen`, atributo que o PyInstaller injeta em runtime) e, quando verdadeiro, `save_dir()` retorna `Path(sys.executable).resolve().parent` em vez do caminho baseado em `__file__`; Android (`is_android()`) e desktop rodando de fonte (`uv run main.py`) continuam com o comportamento anterior. Ver design seção 23. _(R4.5)_
  **Decisão de design confirmada com o dono do projeto:** gravar ao lado do executável (não em um diretório padrão de dados do SO como `%APPDATA%`), já que a distribuição é um zip/tar portátil (R13.2) e não uma instalação em local somente-leitura como `Program Files`.
  **Validado:** `tests/test_storage.py::test_save_dir_frozen_desktop_uses_executable_dir` (simula `sys.frozen`/`sys.executable` via `monkeypatch`); suíte completa (70 testes) verde. Build real via `uv run pyinstaller BlockyBee.spec` e verificação manual em `dist/BlockyBee.exe`: com `sys.frozen`/`sys.executable` simulados apontando para o executável gerado, `storage.save_dir()` resolve para `dist/`, `score.save_highscore()` cria `dist/highscore.json` ao lado do `.exe` e `score.load_highscore()` recupera o valor salvo corretamente.

- [x] **34. Conformidade com ty (checagem de tipos)**
  Adicionar `ty` como dependência de dev (`uv add --dev ty`), configurar `[tool.ty.environment]`/`[tool.ty.src]` em `pyproject.toml` (`python-version = "3.10"`, `exclude = ["p4a-recipes", "specs", ".buildozer", "build", "dist"]`, ver design seção 28). Rodar `uv run ty check .` sobre `main.py`, `src/`, `tests/`, `scripts/`; corrigir violações reais no código, suprimir com `# ty: ignore[regra]` + comentário curto só quando a causa é uma limitação do checador (módulo só resolvível em runtime de outra plataforma, atributo dinâmico em teste). Adicionar step `ty check .` em `.github/workflows/ci.yml`, entre `ruff format --check` e `pytest`. Confirmar `uv run pytest` e `ruff check`/`ruff format --check` continuam verdes. _(R20)_
  **`p4a-recipes/` excluído do escopo:** diferente do `ruff` (task 31, que inclui as receitas por serem código próprio do projeto), `ty` precisa *resolver* imports de verdade — e as receitas importam `sh`/`pythonforandroid.*`, pacotes que só existem dentro da imagem Docker do buildozer (R17), nunca no `.venv` local. Incluí-las geraria só `unresolved-import` permanente e não-acionável.
  **Violações reais encontradas (3, todas corrigidas no código, nenhuma suprimida):** `src/biome.py` (`_lerp_color`) e `src/particles.py` (`ParticleSystem.burst`) construíam uma cor RGB a partir de expressão de tamanho variável (genexpr / slice de `pygame.Color`) e atribuíam a `tuple[int, int, int]` — `ty` infere `tuple[int, ...]` para as duas formas; corrigido desempacotando em variáveis nomeadas e retornando/atribuindo um literal de 3-tupla. `src/input.py` (`InputManager`) anotava `dict[int, pygame.joystick.Joystick]`, mas o próprio stub do pygame-ce documenta `Joystick` como função-fábrica (não classe) nesta versão da lib; corrigido usando `pygame.joystick.JoystickType` (o tipo real da instância) e removida a chamada redundante `joystick.init()` (deprecated desde 2.0.0, a construção já inicializa).
  **Supressões pontuais (2, com comentário explicando o motivo):** `src/storage.py` — `from android.storage import app_storage_path` dentro do `try/except ImportError` (seção 23), módulo só existe em runtime p4a; `# ty: ignore[unresolved-import]`. `tests/test_storage.py` — atribuição dinâmica de atributos a um fake `types.ModuleType` para simular o módulo `android.storage` injetado pelo p4a nos testes; `# ty: ignore[unresolved-attribute]`.
  **Validado:** `uv run ty check .` reporta zero diagnósticos; suíte completa (70 testes) e `ruff check`/`ruff format --check` permanecem verdes.

## Tarefas adicionais da v2 (pós-Android) — Ícone do aplicativo

Pedido do dono do projeto: o ícone do app deve ser a personagem do jogo (a abelha), e no Android o ícone precisa aparecer "com as proporções ajustadas" — sem cortar a personagem quando o launcher aplica sua máscara (círculo/squircle/quadrado arredondado). Ver design.md seção 29.

- [x] **36. Geração do ícone por código e integração no desktop**
  Criar `scripts/generate_app_icon.py` (script standalone, reaproveitando `textures.make_bee`): gera `assets/app_icon_512.png` (janela + fonte do `.ico`), `assets/app_icon.ico` (multi-resolução 16–256px, construído via `struct` da stdlib embutindo PNGs, sem depender de Pillow) e `assets/android_icon_legacy.png`. Criar `src/assets.py::asset_path()` (resolve `sys._MEIPASS` quando `storage.is_frozen()`, raiz do projeto caso contrário) e chamar `pygame.display.set_icon()` em `Game.__init__` (`src/game.py`), envolvido em `try/except` para degradação graciosa. Atualizar `BlockyBee.spec`: `datas=[('assets/app_icon_512.png', 'assets')]` no `Analysis` e `icon='assets/app_icon.ico'` no `EXE`. Testes para as funções puras do script (ajuste de escala, construção do `.ico`) e para `asset_path()` nos dois ramos. Validar rodando `uv run main.py` (ícone na barra de título) e gerando o executável (`uv run pyinstaller BlockyBee.spec`, ícone no `.exe`/Explorer). _(R21.1, R21.2, R21.3, R21.7)_
  **Implementado conforme o design (seção 29.1–29.3), sem desvios.** `make_composed_icon()` desenha uma cena com céu do Overworld + faixa de grama/terra + abelha centralizada, reamostrada em escala nearest-neighbor (pixel-art fiel, R7.1); só o `.ico` usa `smoothscale` nos tamanhos pequenos (16–48px), documentado no design como o único ponto onde a suavização é aceitável. `build_ico()` monta o container `ICONDIR`/`ICONDIRENTRY` manualmente com `struct`, embutindo um PNG por resolução (16/32/48/64/128/256) — validado por round-trip (`pygame.image.load` de cada entrada extraída de volta) tanto no teste automatizado quanto por `file assets/app_icon.ico` (reconhecido como "MS Windows icon resource" com 6 ícones).
  **`src/assets.py::asset_path()`**: replica o padrão já usado por `storage.py` (seção 23), mas na direção oposta — `sys._MEIPASS` é onde o PyInstaller onefile *extrai* dados para leitura (correto aqui), ao contrário de `storage.save_dir()`, que evita `_MEIPASS` de propósito por ser efêmero (não serve para *gravar* o recorde, task 33). `Game.__init__` chama `pygame.display.set_icon()` envolvido em `contextlib.suppress(OSError, pygame.error)` (troca de um `try/except: pass` por sugestão do `ruff`/SIM105) antes do `set_mode`, sem custo perceptível no Android (onde não há efeito visível, mas também não há necessidade de um `if is_android()` para pular — `asset_path()` já resolve para a raiz do projeto lá, e o arquivo existe no APK via `source.include_exts = py,png`).
  **Validado:** suíte completa (87 testes = 81 anteriores + 6 novos, `tests/test_assets.py` e `tests/test_generate_app_icon.py`) verde; `ruff check`/`ruff format --check`/`ty check` sem violações. Smoke test real (não headless) de `uv run main.py` por alguns segundos sem exceções. Build real via `uv run pyinstaller BlockyBee.spec`: log confirma `"Copying icon to EXE"`; `dist/BlockyBee.exe` executado por alguns segundos sem exceções.
  **Não verificado visualmente neste ambiente:** confirmar a olho que o ícone da abelha aparece de fato na barra de título/taskbar e no Explorer (o smoke test só confirma ausência de erro, não a aparência) — recomenda-se uma checagem visual rápida pelo dono do projeto antes de publicar.

- [x] **37. Ícone adaptativo do Android no `buildozer.spec`**
  Estender `scripts/generate_app_icon.py` para também gerar `assets/android_icon_foreground.png` (432×432, só a abelha, escalada para caber nos 66/108 dp da zona segura de máscara) e `assets/android_icon_background.png` (432×432, gradiente de céu do Overworld, opaco, sem a abelha). Adicionar ao `buildozer.spec`: `icon.filename` (aponta para o ícone legado da task 36, cobre API < 26), `icon.adaptive_foreground.filename` e `icon.adaptive_background.filename` (cobrem API ≥ 26, R21.4–R21.6). Validar `buildozer.spec` como INI bem formado e as dimensões/canal alfa dos PNGs gerados; se Docker estiver acessível neste ambiente (ver design seção 25), rodar o build real do APK e confirmar `BUILD SUCCESSFUL` com as novas chaves. _(R21.4, R21.5, R21.6, R21.7)_
  **As três camadas já foram geradas na task 36** (mesmo `scripts/generate_app_icon.py`, seção 29.1 do design) — esta task só adiciona as três chaves correspondentes no `[app]` do `buildozer.spec`, seguindo o estilo de caminho relativo já usado no arquivo (sem `%(source.dir)s`, já que `source.dir = .` torna as duas formas equivalentes aqui). Validado como INI bem formado via `configparser` (mesma checagem das tasks 27/31).
  **Docker estava acessível neste ambiente** (imagem `kivy/buildozer:latest` já em cache local, `Buildozer 1.6.1.dev0`) **e o build real foi executado ponta a ponta**, reaproveitando o cache de SDK/NDK persistido de uma sessão anterior (`~/.buildozer-android-global-cache`, ~2.6 GB) e o `.buildozer/` do projeto — `BUILD SUCCESSFUL in 1m 36s`, gerando `bin/blockybee-0.2.0-armeabi-v7a_arm64-v8a_x86_64-debug.apk` (62 MB). O comando `p4a` invocado pelo buildozer (visível no log) confirma a tradução das três chaves do spec para as flags reais do python-for-android: `--icon .../android_icon_legacy.png --icon-fg .../android_icon_foreground.png --icon-bg .../android_icon_background.png`.
  **Verificação real do conteúdo do APK (além do log de build), inspecionando o `.apk` extraído (é um zip):** `res/mipmap-anydpi-v26/icon.xml` existe e contém as strings `adaptive-icon`/`background`/`foreground` (XML binário compilado pelo aapt, confirmando um `<adaptive-icon>` de verdade, não um ícone comum); `res/mipmap/icon_foreground.png` (432×432, RGBA — canal alfa presente, confirmando a camada transparente) e `res/mipmap/icon_background.png` (432×432, RGB — sem alfa, confirmando a camada opaca) batem em dimensão **e em tamanho de arquivo em bytes** com os PNGs gerados por `scripts/generate_app_icon.py` (1277 e 1488 bytes respectivamente) — prova de que são exatamente os arquivos gerados, não um fallback ou um ícone padrão do template. `res/mipmap/icon.png` (2292 bytes) também bate com `android_icon_legacy.png`, confirmando o ícone legado (API < 26).
  **Ainda não verificável neste ambiente:** a composição final da máscara pelo launcher (círculo/squircle/quadrado arredondado) só é visível de fato num aparelho ou emulador Android real — o que foi verificado aqui é que os recursos corretos (as camadas certas, nos tamanhos certos, com/sem alfa conforme esperado) chegam ao APK; a etapa que falta é inteiramente do lado do sistema operacional Android no aparelho, fora do alcance deste ambiente (mesma limitação da seção 25). Recomenda-se instalar o APK gerado (ou o de uma Release futura) num celular e confirmar visualmente que a abelha aparece inteira, sem antenas/asas cortadas, em qualquer forma de ícone que o launcher use.

## Tarefas da v3 — Identidade, tela, GPU e rigor SDD (pendentes)

### Bloco A — Identidade

- [x] **42. Rename para Blocky Bee**
  Trocar o nome do produto em todos os pontos fora de `specs/v1` e `specs/v2` (que não são reescritos, R22.4): `src/config.py` (`TITLE`), `src/ui.py` (texto da tela inicial), `buildozer.spec` (`title` e `package.name = blockybee`), `BlockyBird.spec` → `BlockyBee.spec` (inclusive o `name=` interno), `.github/workflows/release.yml` (nomes de artefato e comando do PyInstaller), `README.md`, `CLAUDE.md`, e as strings de exemplo em `src/storage.py` / `tests/test_storage.py`. `package.domain` continua `com.douglaspands`. Validar que a suíte continua verde, que o `buildozer.spec` segue sendo INI bem formado (mesma checagem via `configparser` das tasks 27/31/37) e que `uv run main.py` abre com o título novo. _(R22.1, R22.2, R22.4)_
  **Implementado conforme o design (seção 31), sem desvios.** 8 arquivos tocados fora de `specs/`: `src/config.py` (`TITLE`), `src/ui.py` (`"BLOCKY BEE"` na tela inicial), `buildozer.spec` (`title` e `package.name`), `BlockyBee.spec` (renomeado com `git mv`, preservando o histórico do arquivo, mais o `name='BlockyBee'` interno), `.github/workflows/release.yml` (7 ocorrências: comando do PyInstaller, empacotamento Windows/Linux e os 3 nomes de asset), `README.md`, `CLAUDE.md`, e as strings de exemplo em `src/storage.py` e `tests/test_storage.py` (incluindo os caminhos fictícios `/data/data/org.blockybee/...`).
  **Não precisou mudar:** o passo "Rename APK sem comprimir" do `release.yml` localiza o artefato por `find bin -name '*.apk'`, sem nome fixo, então segue funcionando com o `package.name` novo. `package.domain` continua `com.douglaspands` — o identificador completo passa de `com.douglaspands.blockybird` para `com.douglaspands.blockybee`.
  **`specs/v1/` e `specs/v2/` ficaram intactas** (R22.4): continuam dizendo "Blocky Bird", que era o nome correto quando foram escritas. Só `specs/v3/` foi atualizada, junto com a linha da v3 na tabela de `specs/README.md`.
  **Validado:** suíte completa (86 testes) verde; `ruff check`, `ruff format --check` e `ty check` sem violações; `buildozer.spec` validado como INI bem formado via `configparser`, reportando `title = Blocky Bee` e `package.name = blockybee`.
  **Não verificado neste ambiente:** o título novo na barra da janela e o nome do `.exe` gerado pelo PyInstaller dependem de execução gráfica e de build de release — ficam cobertos pela task 70 (README/checklists) e pelo checklist manual.

### Bloco B — Instrumentação (medir antes de otimizar)

- [x] **43. `src/perf.py` e sobreposição de diagnóstico**
  Implementar `FrameProfiler` com médias móveis de tempo de `update`, tempo de `draw` e taxa de quadros, e uma sobreposição que os desenha com o `pixelfont` já existente, junto do backend de render em uso (task 49). Ativada apenas por `BLOCKY_PERF=1`; quando desligada, o profiler não é instanciado e a medição não entra no caminho quente. Testes para o cálculo das médias e para a ativação por variável de ambiente (ligada/desligada). _(R30.1, R30.2, R26.5)_
  **Implementado conforme o design (seção 39), sem desvios.** `_MovingAverage` usa buffer circular pré-alocado com soma corrente — adicionar uma amostra é uma escrita, duas somas e um incremento de índice, sem alocar nada. A implementação ingênua (lista que cresce + `sum()` na leitura) alocaria por frame, que é justamente o que a v3 combate; seria contraditório instrumentar desempenho com um instrumento que piora o desempenho. `FrameProfiler` usa `__slots__` pelo mesmo motivo.
  **API de cronometragem:** `begin()` marca o início e cada `end_*` mede desde a última marcação **e remarca** o cronômetro, então um frame inteiro custa três chamadas (`begin` → `end_update` → `end_draw`) em vez de quatro, sem intervalo perdido entre as etapas.
  **Custo quando desligada (R30.2):** `Game.__init__` só instancia o profiler se `perf.enabled()`, e `Game.run` iça `self.profiler` para uma variável local antes do laço, ramificando **uma vez por frame** entre um caminho instrumentado e um caminho limpo — no caminho limpo não há nem chamada de medição nem acesso a atributo.
  **Ajuste necessário fora do previsto:** `pixelfont.GLYPHS` não tinha o glifo `.`, e as linhas da sobreposição exibem milissegundos com uma casa decimal (`1.2MS`). Sem o glifo, o caractere cairia no `_BLANK` e sairia como espaço (`1 2MS`) — silenciosamente errado. Foi adicionado um ponto 5×7 (pixel único na última linha), e `test_lines_usa_apenas_glifos_existentes` passou a varrer cada caractere de cada linha contra `GLYPHS`, para que uma linha futura com caractere sem glifo quebre o build em vez de sair truncada na tela.
  **Escala 2 na sobreposição:** com escala 1 os glifos ficam com 5×7 px lógicos, o que num celular de 1080 px de largura vira ~11 px de altura física — legível no limite. A escala 2 dobra isso sem competir por espaço com o jogo.
  **Testes (13 novos, `tests/test_perf.py`):** média móvel vazia/parcial/com janela cheia (a amostra mais antiga é de fato expulsa); FPS derivado da duração real do frame e zero sem amostras; `enabled()` tratando ausência, `""` e `"0"` como desligado e qualquer outro valor como ligado; cobertura de glifos; a sobreposição desenha no canto superior esquerdo preservando a margem e **sem tocar o centro da tela**; e `Game` sem profiler por padrão / com profiler quando ligado.
  **Validado:** suíte completa (99 testes) verde; `ruff check`, `ruff format --check` e `ty check` sem violações.

- [x] **44. `scripts/benchmark.py` e baseline da v2**
  Script headless (`SDL_VIDEODRIVER=dummy`) que roda N frames de cada cenário — PRONTO, JOGANDO nos três biomas com colunas em tela, e GAME_OVER com partículas — e reporta ms/frame p50 e p95, contagem de draw calls e alocação de memória. Executar **antes de qualquer otimização** e gravar os números no bloco `BASELINE` da seção 30 do `design.md`. Teste para as funções puras de estatística (percentis) do script. _(R30.3, R30.4, R30.5)_
  **Implementado conforme o design (seção 39), com dois desvios que a própria medição obrigou** — ambos descobertos rodando o script, não previstos no papel:
  **Desvio 1 — a métrica de memória do plano media a coisa errada.** O design pedia `sys.getallocatedblocks()` e `gc.get_stats()`. Medidos, os dois deram **zero** em todos os cenários, e por um motivo estrutural, não por bug: `getallocatedblocks()` reporta o **saldo líquido** de blocos, então um frame que aloca e libera 40 objetos aparece como zero — ele detecta vazamento, não pressão; e o contador de coletas do `gc` só avança quando há excedente **líquido** de objetos-contentores, que um laço equilibrado nunca produz. A métrica foi trocada por **KB transitórios por frame**, medidos com `tracemalloc.reset_peak()` no início do frame e o pico lido no fim — a marca d'água do que foi alocado e descartado dentro daquele frame. Roda numa passada separada, porque o `tracemalloc` deixa o processo várias vezes mais lento e contaminaria a medição de tempo.
  **Desvio 2 — artefato de medição que inflava os cenários posteriores.** Na primeira execução os tempos cresciam monotonicamente ao longo da tabela (3,3 → 3,4 → 12,4 → 13,0 → 14,9 ms), o que não corresponde a nenhuma diferença real entre biomas. A causa é a mesma limitação que o `conftest.py` já documenta desde a v2 (design seção 20.2): `pygame.SCALED` exige um renderizador SDL e o driver `dummy` só permite um por processo, então cada `Game()` novo deixava um renderizador para trás. `_fresh_display()` (`display.quit()` + `display.init()` entre cenários) eliminou a deriva — os cinco cenários passaram a ficar na faixa de 3,3–4,1 ms, como esperado.
  **Contagem de draw calls:** `_CountingSurface` é uma **subclasse real** de `pygame.Surface`, não um proxy, porque `pygame.draw.*` exige uma superfície de verdade como primeiro argumento; um objeto que apenas delegasse quebraria essas chamadas. As funções de `pygame.draw` usadas pelo jogo são envolvidas separadamente, já que não passam pelo `blit`.
  **`_NoCollisionGame`** é uma subclasse que sobrescreve `_collision_texture`, em vez de um monkeypatch do método — sem isso o `ty` acusa `invalid-assignment`, e a subclasse mantém a assinatura sob checagem de tipos em vez de silenciar o diagnóstico.
  **Baseline registrado** na seção 30 do `design.md`, com o ambiente de medição, a leitura dos números (por que ~3,4 ms num desktop x86 ainda significa problema num ARM de celular) e o limite conhecido da métrica: `tracemalloc` só enxerga o alocador do Python, então a `Surface` de ~1,4 MB que `_dim_overlay` cria por frame não aparece na coluna de KB — ela se manifesta no p50/p95 do GAME_OVER, que é de fato o cenário mais lento da tabela.
  **Testes (7 novos, `tests/test_benchmark.py`):** percentil com lista vazia, amostra única, mediana, interpolação entre vizinhos, preservação da lista de entrada, e formatação da linha markdown. O caso do p95 mereceu correção durante a escrita: `[1.0]*99 + [100.0]` **não** faz o p95 subir (com 100 amostras ele cai no índice 94–95, ainda em 1.0) — o teste passou a usar 10% de amostras ruins, que é o que de fato caracteriza o engasgo periódico que o p95 existe para expor. A execução completa do benchmark não é testada de propósito: roda centenas de frames de cinco cenários e levaria mais que a suíte inteira.
  **Validado:** suíte completa (106 testes) verde; `ruff check`, `ruff format --check` e `ty check` sem violações; benchmark executado ponta a ponta em 300 frames por cenário.

### Bloco C — Canvas, tela cheia e faixas decorativas

- [x] **45. `src/viewport.py` — canvas lógico e área jogável**
  Implementar o cálculo da seção 32.3: `PLAY_W`/`PLAY_H` como constantes de mundo, canvas lógico com a proporção real da tela/janela, `play` centralizado na horizontal, e as bandas (`sky`, `ground`, `left`, `right`) derivadas. `set_mode` passa a `FULLSCREEN` no Android e `960×720 | RESIZABLE` no desktop. `config.SCREEN_W`/`SCREEN_H` deixam de ser constantes de módulo e passam a ser resolvidos pelo `Viewport` ativo, no mesmo padrão de `config.ground_y()`. Variável dev-only `BLOCKY_CANVAS=LxA` para forçar um canvas no desktop. Testes de tabela cobrindo as cinco proporções da seção 32.3 (celular 20:9 e 16:9, desktop 960×720, monitor 16:9, exatamente 2:3), mais os invariantes: a área jogável é sempre 480×720, o canvas nunca é menor que ela, e a soma das bandas fecha exatamente com o canvas (sem pixel perdido em largura ímpar). _(R23.1, R23.2, R23.3, R23.4, R23.7)_

  **Implementado conforme a seção 32.3, com dois ajustes de forma.**

  **Ajuste 1 — `pygame.SCALED` mantido como escalador provisório.** A seção 32.7 mostra o `set_mode` sem `SCALED`, porque na v3 quem leva o canvas lógico para a tela real é `Renderer.logical_size` (seção 33.2). Só que o renderizador chega na task 49: tirar o `SCALED` agora deixaria o Android desenhando um canvas de 480×1067 no canto de uma tela de 1080×2400, sem escala nenhuma — uma regressão viva entre as tasks 45 e 49. Com `SCALED | FULLSCREEN`, R23.1 e R23.3 já valem no aparelho hoje, e a escala é uniforme porque o canvas tem exatamente a proporção da tela. Bônus: `input.py` continua recebendo coordenada lógica do SDL, sem precisar antecipar a task 51. `viewport.display_flags()` documenta que o `SCALED` sai quando o renderizador entrar.

  **Ajuste 2 — funções, não variáveis de módulo.** O design escreve `config.SCREEN_W`/`SCREEN_H` "resolvidos pelo Viewport ativo"; a implementação usa `config.screen_w()`/`screen_h()`. Uma variável de módulo reatribuída não resolveria o problema real: seis módulos faziam `from src.config import SCREEN_W`, o que congela o valor no import — antes de o display existir. A forma de função é a única que garante leitura do viewport corrente, e é literalmente o padrão de `config.ground_y()` que o design cita. Pelo mesmo motivo `ui.MAX_TEXT_W` e `ui.MUTE_ICON_RECT` viraram `ui.max_text_w()` e `ui.mute_icon_rect()`. No `Ground.draw` os limites dos dois laços de blit são içados para locais, para não resolver o viewport por iteração.

  **Observado:** com o canvas de 960×720 no desktop, o `benchmark.py` sobe de 3,3–4,1 ms de p50 (baseline da v2, medido a 480×720) para 6,2–11,4 ms, e de ~96 para 110–126 draw calls por frame — chão e parallax passam a cobrir o dobro de largura, tudo ainda em CPU. É a conta esperada, e é exatamente a que o caminho de GPU (bloco D) e o atlas (bloco E) existem para pagar; os números finais entram na task 73.

  **Testes (41 novos, `tests/test_viewport.py`):** a tabela das cinco proporções da seção 32.3, mais os invariantes por proporção (área jogável sempre 480×720, canvas nunca menor que ela, proporção do canvas igual à da tela, bandas fechando exatamente com o canvas nos dois eixos), o pixel ímpar indo para a banda direita, a sobra vertical enchendo o chão antes do céu, o `BLOCKY_CANVAS` com valores válidos e malformados, e a idempotência de `compute` sobre a própria saída — que é o que sustenta forçar o canvas pelo tamanho de tela. Em `tests/test_game.py`, o teste de resolução fixa da v2 deu lugar a dois: o display criado com o canvas calculado e o caminho Android (tela cheia, canvas 480×1067 a partir de 1080×2400, área jogável intacta). `conftest.py` ganhou `_reset_viewport`, porque o `Game` define o viewport globalmente e ele vazaria de um teste para o outro.

  **Validado:** suíte completa (148 testes) verde; `ruff check`, `ruff format --check` e `ty check` sem violações. Conferência visual por frame renderizado em 960×720 e em `BLOCKY_CANVAS=480x1067`: a cena preenche o canvas inteiro nos dois casos, sem barra preta em lado nenhum. Como esperado nesta task, a área jogável ainda não está isolada dentro do canvas — abelha, chão e colunas seguem ancorados no canvas, e é a task 46 (faixas verticais) e a 47 (faixas laterais) que os movem para `play`.

  **Não verificável neste ambiente:** tela cheia na resolução nativa em aparelho real (R23.3) — coberto pela task 72.

- [x] **46. Faixas vertical (céu estendido e chão mais fundo)**
  Deslocar o jogo para coordenadas de canvas conforme a seção 32.4: posição inicial da abelha, teto (`bird.py`), `ground_y()`, faixa de sorteio de `gap_y` e descarte de colunas passam a usar `play`. Nenhuma constante de física ou de bioma muda. O HUD de pontuação e o ícone de mudo migram para a faixa de céu quando ela existe. Testes: com um canvas alongado, a abelha não sobe acima de `play.top`, o `gap_y` sorteado fica sempre dentro da área jogável, e o HUD é posicionado na faixa de céu; com canvas 2:3, tudo cai exatamente onde caía na v2 (teste de não-regressão). _(R23.4, R24.1, R24.2, R24.5, R25.1, R25.7)_

  **Implementado conforme a tabela da seção 32.4.** `config.play()` entrou como acessador da área jogável e `ground_y()` passou a ser `play.bottom - GROUND_H` — daí a faixa de chão sai de graça, porque `Ground.draw` já enchia até a base do canvas. Nenhuma constante de física ou de bioma foi tocada.

  **Ajuste 1 — o sorteio de `gap_y` precisou de piso próprio.** A tabela diz "mesma fórmula, com o novo `ground_y()`", mas `GAP_MARGIN` sozinho é um número absoluto de canvas: com faixa de céu de 251px, `uniform(80, ...)` sortearia o centro da abertura dentro da decoração, acima do teto da abelha e portanto impossível de atravessar. O piso passou a ser `play.top + GAP_MARGIN`.

  **Ajuste 2 — telas de estado e banner de bioma também migraram para `play`.** A task nomeia só o HUD e o ícone de mudo, mas PRONTO, PAUSADO, GAME_OVER e o banner estavam ancorados em `screen_h()`. Num canvas de 480×2800 o `screen_h() // 4` da tela inicial cai dentro da faixa de céu, acima da área jogável — o texto sairia do jogo. Todos passaram a `play.centerx` / `play.top`, e num canvas 2:3 os números são idênticos aos da v2. Pelo mesmo motivo `ui.max_text_w()` passou a medir contra a área jogável: contra o canvas, um texto longo teria licença para escorrer por cima das faixas laterais.

  **Ajuste 3 — `decor.py` deixou de derivar a linha do chão da altura da surface.** Colinas, poças de lava e pilares se ancoravam em `surface.get_height() - GROUND_H`, o que na v3 é a base da faixa decorativa: eles afundariam 96px na terra. Agora usam `config.ground_y()`.

  **Decisão — o ícone de mudo fica no canto do canvas, não no da área jogável.** É o ponto mais alcançável no celular, e R25.6 permite explicitamente um controle de interface sobre faixa decorativa. Verticalmente ele mora na faixa de céu quando ela o comporta (R25.7); num celular 16:9, cuja faixa tem só 37px, desce inteiro para a área jogável em vez de ficar metade em cada uma. A pontuação segue a mesma regra, centrada na faixa quando cabe.

  **Mantido de propósito:** as colunas continuam sendo desenhadas a partir do topo do canvas, atravessando a faixa de céu como se viessem de fora da tela (seção 32.5). A colisão não muda, porque a abelha nunca passa de `play.top`.

  **Testes (16 novos, `tests/test_bands.py` e `tests/test_game.py`):** com o canvas do celular 20:9, o teto do voo é `play.top` e não o topo do canvas; a trajetória de queda medida a partir de `play.top` é idêntica nas duas proporções (velocidades batem bit a bit, alturas a menos de epsilon de float — somar o mesmo delta a 200 ou a 451 arredonda diferente, e isso é representação, não física); toda abertura sorteada em 200 frames fica dentro da área jogável, bordas incluídas; a coluna é descartada em `play.left`; o chão enche a faixa decorativa até a base do canvas, verificado por pixel; a pontuação e o ícone de mudo vão para a faixa de céu, caem de volta na área de jogo quando a faixa é curta demais, e num canvas 2:3 ficam exatamente onde ficavam na v2; a abelha nasce no meio da área jogável no caminho Android. O teste de decoração da v2 que afirmava sobre a altura da surface foi reescrito para afirmar sobre a linha do chão da área jogável.

  **Validado:** suíte completa (164 testes) verde; `ruff check`, `ruff format --check` e `ty check` sem violações. Conferência visual em `BLOCKY_CANVAS=480x1067`, em PRONTO e em JOGANDO: céu vazio acima da área jogável, abelha e textos dentro dela, colunas atravessando a faixa de céu, colinas assentadas na linha do chão e terra funda até a base da tela.

- [x] **47. Faixas laterais — corte transversal do terreno**
  Gerar por bioma uma faixa lateral opaca com camadas de bloco empilhadas e veios de minério, reaproveitando as texturas da seção 10 e os desenhadores de `decor.py`, com a linha do chão alinhada a `ground_y()`. Desenhá-las **depois** das colunas, para ocultar o que ainda não entrou na área jogável. `PipeManager._spawn` passa a criar em `play.right`. Céu, parallax e chão passam a cobrir a largura toda do canvas. Testes: a coluna nasce em `play.right`; nenhum pixel de coluna é visível fora de `play` (verificado pela ordem de desenho registrada no `FakeRenderer`); a faixa é opaca; o tempo entre o nascimento da coluna e a chegada à abelha é igual num canvas 960×720 e num 480×720. _(R24.3, R24.4, R25.2, R25.5)_

  **Implementado em `src/bands.py`**, desenhado depois das colunas, da abelha e das partículas, na posição que a seção 32.6 reserva. Céu, parallax e chão já cobriam a largura toda do canvas desde a v2 (`_tile` e `Ground.draw` usam a largura real da surface), então R25.5 não precisou de código novo — ganhou teste.

  **Ajuste 1 — a parede precisou de duas âncoras, não uma.** A seção 32.5 pede as duas coisas ao mesmo tempo: camadas empilhadas (grama → terra → pedra) e a linha do chão alinhada a `ground_y()`. Ancorar tudo em `ground_y` não entrega a primeira: abaixo da linha do chão cabem no máximo 4 fileiras de bloco (`GROUND_H` + `MAX_GROUND_EXTRA` = 192px), então a camada profunda nunca aparecia — a parede virava "grama → terra" e ponto. A implementação usa duas âncoras: a crosta (borda + solo) no topo do canvas, marcando a superfície lá em cima, com a camada profunda no miolo, que é onde os veios de minério aparecem; e uma segunda fileira de borda exatamente em `ground_y()`, com solo logo abaixo, que é o que faz a terra parecer contínua de uma borda à outra. As duas âncoras não compartilham grade — `ground_y` depende da faixa de céu e quase nunca é múltiplo de 48 —, então a faixa é preenchida com a camada profunda primeiro e as fileiras são desenhadas por cima.

  **Ajuste 2 — o teste de oclusão não usa `FakeRenderer`.** Ele só nasce na task 50, junto do renderizador. Aqui a verificação é por pixel, e o teste tem contraprova: na segunda metade ele desliga a faixa e exige que aí sim a coluna apareça. Sem isso, o teste passaria mesmo que a coluna jamais tivesse sido desenhada naquela região, e não provaria nada sobre a oclusão.

  **Decisões menores.** `DEEP_BLOCK` (Overworld → pedra, Cave → pedregulho, Nether → obsidiana) mora em `bands.py` e é chaveado pelo id do bioma, no mesmo padrão de `decor._LAYERS`, para decoração não virar campo de `Biome`. `decor._draw_ore_veins` passou a ser público (`draw_ore_veins`), já que agora tem dois consumidores. As duas paredes são construídas com sementes diferentes: iguais, entregariam uma simetria de espelho que denunciaria a repetição. As superfícies são cacheadas por bioma e invalidadas quando o canvas ou `ground_y` mudam — a mesma disciplina de `BiomeManager._ensure_gradients`.

  **Testes (9 novos, `tests/test_bands.py`):** a coluna nasce em `play.right`; o número de frames entre o nascimento e a chegada à abelha é idêntico num canvas 1280×720 e num 480×720; a faixa é opaca em toda a altura, nos três biomas, verificado contra um fundo magenta que denunciaria qualquer buraco; numa tela 2:3 nada é desenhado; a fileira de borda da faixa bate pixel a pixel com a textura de borda na altura de `ground_y()`; a coluna que ainda não entrou na área jogável não sobrevive ao desenho da faixa, com a contraprova descrita acima; e céu, parallax e chão chegam às duas bordas do canvas.

  **Validado:** suíte completa (173 testes) verde; `ruff check`, `ruff format --check` e `ty check` sem violações. Conferência visual no canvas 960×720 nos três biomas, mais uma verificação ponto a ponto do material na emenda: em Overworld, Cave e Nether o bloco da faixa e o do chão da área jogável são o mesmo em toda a altura da junção (variam só no ruído interno da textura, que é por construção).

- [x] **48. Retrato travado e recomputação em redimensionamento**
  Definir `SDL_HINT_ORIENTATIONS=Portrait` antes do `pygame.init()`, reforçando no lado do SDL o `orientation = portrait` que o `buildozer.spec` já declara. No desktop, tratar `WINDOWRESIZED` recalculando o `Viewport` e reconstruindo o atlas. Verificar no APK construído (task 72) que o `AndroidManifest.xml` traz `android:screenOrientation="portrait"`, com a mesma disciplina de inspeção do `.apk` usada na task 37. Testes: um evento de redimensionamento sintético produz um `Viewport` novo e coerente, e a área jogável permanece 480×720 depois dele. _(R23.5, R23.6)_

  **Ajuste 1 — o nome do hint no plano não é o nome que o SDL lê.** `SDL_HINT_ORIENTATIONS` é o nome da macro em C; a string que ela contém, e que `SDL_GetHint` procura no ambiente, é `SDL_IOS_ORIENTATIONS` (`#define SDL_HINT_ORIENTATIONS "SDL_IOS_ORIENTATIONS"`, conferido no cabeçalho do SDL2). O prefixo `IOS` é histórico — a própria documentação do SDL descreve o hint como "which orientations are allowed on iOS/Android". Exportar o nome da macro não teria efeito nenhum, e o silêncio seria total. Não é verificável localmente: a build do SDL2 para Windows nem contém essa string, porque quem a lê são os backends de Android e iOS.

  **Ajuste 2 — "reconstruindo o atlas" ainda não se aplica.** O atlas nasce no bloco E. Hoje os caches que dependem do canvas — faixas laterais e gradientes de bioma — são chaveados pelo tamanho, então se invalidam sozinhos quando o canvas muda; não houve o que invalidar à mão.

  **Descoberto na implementação — trocar o canvas do `SCALED` exige recriar o display, e recriar tem armadilha.** Medido: o **terceiro** `set_mode(SCALED)` de um processo **aborta o interpretador** no pygame-ce 2.5.7, sem exceção para capturar, tanto no driver `windows` quanto no `dummy`. Com `display.quit()` + `display.init()` antes de cada recriação, seis ciclos seguidos funcionam — é a mesma limitação de um renderizador SDL por processo que o `conftest.py` documenta desde a v2 (design seção 20.2). Quando a camada de render entrar (task 49), isto vira `renderer.logical_size = viewport.canvas` e o rodeio inteiro desaparece.

  **Descoberto na implementação — recriar o display encolhe a janela.** `set_mode(canvas)` cria a janela do tamanho do canvas, então arrastar para 1920×1080 faria a janela pular para os 1280×720 do canvas: o redimensionamento pareceria quebrado. `viewport.restore_window_size()` devolve o tamanho arrastado via `pygame.Window.from_display_module()` — a mesma ponte que o design já prevê para a task 49. Com `SCALED`, tamanho de janela e tamanho de canvas são independentes, e é justamente isso que se está usando.

  **Debounce.** Cada pixel de um arrasto emite um `WINDOWRESIZED`; aplicar todos recriaria o display dezenas de vezes por segundo. O novo canvas só é aplicado depois de `RESIZE_SETTLE_FRAMES` (12, ~200ms a 60 FPS) sem evento novo, e um evento durante a espera reinicia a contagem — só o tamanho final chega ao `set_mode`.

  **Limite conhecido:** numa janela mais baixa que os 720px da área jogável, o SDL não permite que ela fique menor que o canvas lógico, e a altura para em 720. É coerente com o canvas nunca encolher abaixo da área jogável (R23.4), então foi mantido.

  **Testes (8 novos, `tests/test_resize.py`):** o hint de retrato é definido e não sobrescreve um valor já presente no ambiente (investigar paisagem não deve exigir editar código); um `WINDOWRESIZED` sintético vira ação de redimensionamento; aplicar 1920×1080 produz canvas 1280×720 com a área jogável intacta e o `config` enxergando o novo canvas; aplicar 1080×2400 recalcula as faixas, não só o tamanho; uma janela maior na mesma proporção não recria o display; e o debounce só aplica depois que o arrasto assenta, com o reinício da contagem a cada evento novo.

  **Validado:** suíte completa (181 testes) verde; `ruff check`, `ruff format --check` e `ty check` sem violações. Exercitado também no driver real do Windows, fora do `dummy`: quatro redimensionamentos consecutivos (1920×1080, 1000×1400, 1400×700, 960×720) recalculam canvas e faixas, mantêm a área jogável em 480×720 e preservam o tamanho da janela, sem travar.

  **Não verificável neste ambiente:** a trava de orientação em aparelho real e o `android:screenOrientation="portrait"` no `AndroidManifest.xml` do APK — task 72.

### Bloco D — Render acelerado por GPU

- [x] **49. `src/render.py` — interface de render e cascata de compatibilidade**
  Implementar a interface da seção 33.1 (`make_image`, `clear`, `draw`, `fill`, `present`, `to_logical`, `size`, `backend`) com duas implementações: `GpuRenderer` sobre `pygame._sdl2.video` (`Window.from_display_module()`, `Renderer`, `logical_size`, `Texture.from_surface`, `draw_color`/`fill_rect`, `Texture.alpha`, `coordinates_from_window`) e `SurfaceRenderer` sobre o caminho da v2. Cascata de três níveis (`accelerated=1, vsync=True` → `accelerated=-1` → superfície), com log do motivo de cada queda. Testes: a cascata cai de nível quando a criação falha (via monkeypatch) e nunca levanta exceção para quem chama; `backend` reflete o nível efetivo; as duas implementações produzem o mesmo resultado observável para a mesma sequência de chamadas. _(R26.1, R26.2, R26.3, R26.4, R26.5, R26.6, R26.7)_

  **Implementado em `src/render.py`**, com `Image`/`Renderer` como classes base finas, `GpuImage`/`GpuRenderer`, `SurfaceImage`/`SurfaceRenderer` e a fábrica `create(canvas, window, fullscreen=, title=)` que desce a cascata. Nenhum módulo de jogo foi ligado a ela ainda — a migração é a task 50, e `game.py` segue no caminho da v2 até lá.

  **Descoberto na implementação — `Window.from_display_module()` não serve para criar o renderizador.** É a premissa da seção 33.2 do design, e ela é falsa: depois de `pygame.display.set_mode(...)` a janela já tem uma `Surface` associada, e `SDL_CreateRenderer` recusa com `pygame.error: Surface already associated with window`. Medido nas três combinações (`accelerated=1`, `-1`, padrão) e nos dois drivers (`windows` e `dummy`) — não é peculiaridade de ambiente headless. O caminho de GPU passa então a criar a própria janela com `pygame._sdl2.video.Window(title, size=..., fullscreen=..., resizable=...)`, e nesse caminho o módulo `display` deixa de ser o dono da janela: título, ícone e tamanho passam a sair de `Window.title` / `Window.set_icon` / `Window.size`, e `present()` substitui `display.flip()`. A fila de eventos não muda, porque eventos do SDL são globais e não pertencem à janela. Verificado ponto a ponto: `Window` + `Renderer` funciona nos dois drivers, seis ciclos de criação/`destroy()` seguidos passam (sem a armadilha do terceiro `set_mode(SCALED)` da task 48), e `set_mode` continua funcionando no mesmo processo depois de janelas do `_sdl2` existirem — que é o que permite os testes de equivalência abaixo.

  **Ajuste — o `SurfaceRenderer` não usa `pygame.SCALED`.** A seção 33.4 o descreve como "`pygame.SCALED` e `Surface.blit`, o caminho da v2", mas com `SCALED` o SDL entrega o mouse já em coordenada lógica e o toque não, e `to_logical` significaria coisas diferentes conforme o backend ativo — exatamente a assimetria que a task 51 existe para desfazer (R34.1). Aqui o desenho vai para um canvas fora da tela e `present()` o escala para a janela com `pygame.transform.scale` (vizinho mais próximo, mesmo critério do hint do caminho de GPU), então `to_logical` converte pixel real de janela → canvas nos dois backends, pela mesma conta. O custo do escalonamento extra fica só no nível 3, que é o que só roda quando nenhum renderizador SDL pôde ser criado.

  **Decisões menores.** `Image.raw` guarda a `Texture` ou a `Surface` e é opaco para os módulos de jogo — só o renderizador que criou a imagem o desempacota. `draw(image, dest, area=None)` aceita `Rect` (estica) ou uma posição `(x, y)` (tamanho nativo), e o caminho de superfície escala à mão quando `dest` traz outro tamanho, porque o `blit` da GPU estica pelo `dstrect` e o da `Surface` não — sem isso os dois backends não desenhariam a mesma coisa. `SurfaceRenderer` cacheia por tamanho a superfície escalada do `present()` e a de mistura do `fill()` com alfa: eram as duas alocações grandes por frame que a seção 30 aponta. `make_image` do caminho de superfície já chama `convert_alpha()` com degradação quando não há display — a task 52 completa isso para o caminho de GPU. Foi acrescentada uma oitava operação fora da interface da seção 33.1, `snapshot()`, exclusiva de diagnóstico e teste (`Renderer.to_surface` na GPU, cópia do canvas na superfície): é ela que torna verificável a exigência de "mesmo resultado observável". O hint `SDL_HINT_RENDER_SCALE_QUALITY=0` (R26.7) foi para cá, porque precisa estar no ambiente antes de o renderizador nascer; `SDL_HINT_RENDER_BATCHING` continua com a task 76. O log usa o `logging` da biblioteca padrão, primeiro uso no projeto.

  **Testes (16 novos, `tests/test_render.py`):** a cascata para no nível 1 quando ele funciona, cai para o nível 2 quando `accelerated=1` falha, cai para superfície quando os dois falham, cai para superfície quando `pygame._sdl2` não existe na build, e não deixa escapar nem a falha ao abrir a janela; `vsync=True` é de fato pedido; o motivo de cada queda vai para o log; o hint de escala é definido e não sobrescreve o ambiente; e quatro testes de equivalência que rodam a mesma sequência de chamadas nos dois backends e comparam o resultado — frame completo (limpar, desenhar em tamanho nativo, esticado, recortado e recortado+esticado, e um `fill` opaco) com igualdade **exata** de pixel numa amostragem de toda a área do canvas, `Image.alpha`, `fill` translúcido e `to_logical`. Sob `SDL_VIDEODRIVER=dummy` o nível 1 não existe, então a suíte exercita a primeira queda de nível de verdade, sem simulação.

  **Validado:** suíte completa (197 testes) verde; `ruff check`, `ruff format --check` e `ty check` sem violações. Exercitado também no driver real do Windows, fora do `dummy`: `create()` devolve `gpu-accelerated`, e desenho, `fill` com alfa (fundo `(30,60,90)` sob preto a 50% → `(15,30,45)`, exato), `to_logical` e `present()` funcionam no renderizador acelerado de verdade.

  **Fica para a task 50:** trocar `renderer.logical_size` no redimensionamento (o que dispensa o `display.quit()/init()` da task 48), o ícone da janela pelo `Window.set_icon` e a instrumentação exibindo `backend` (R26.5, task 71).

- [x] **50. Migrar os módulos de desenho para o renderizador**
  `bird`, `pipes`, `ground`, `decor`, `particles`, `biome` e `ui` deixam de receber `pygame.Surface` e passam a receber `Renderer`. Introduzir um `FakeRenderer` de teste que registra as chamadas, e converter `tests/test_ui_layout.py`, `tests/test_decor.py` e a parte afetada de `tests/test_game.py` para afirmar sobre chamadas em vez de inspecionar pixels. _(R26.4)_

  **Feito.** Nenhum módulo de desenho recebe mais uma `Surface`: `bird`, `pipes`, `ground`, `decor`, `particles`, `biome`, `bands`, `ui` e também `perf.draw_overlay` recebem `render.Renderer`. `game.py` perdeu o `self.screen` e passou a `self.renderer`; `draw()` termina em `renderer.present()` no lugar de `display.flip()`.

  **`Renderer.image(key, factory)` — a operação que a task 50 acrescentou.** A interface da seção 33.1 tinha `make_image`, que converte uma `Surface` que já existe. Faltava o passo anterior: quase todo conteúdo do jogo é *gerado por código* (gradiente de céu, paredes das faixas, glifos de texto, ícone de mudo, formas não retangulares do decor), e cada módulo mantinha um cache próprio de `Surface` da v2. Ligar isso ao renderizador módulo a módulo replicaria oito caches, cada um sabendo quando invalidar. `image(key, factory)` centraliza: a fábrica roda uma vez por chave, o resultado vira imagem do backend ativo, e o módulo de desenho não guarda nada nem sabe qual backend está de pé. Os caches próprios de `SideBands`, `BiomeManager` e `DecorManager` sumiram por consequência. `forget_images()` é o par: no redimensionamento as imagens chaveadas pelo tamanho do canvas nunca mais seriam pedidas e ficariam ocupando memória de vídeo.

  **Fechados os três pendentes da task 49.** O redimensionamento virou `renderer.resize(canvas)` — `logical_size` na GPU, canvas fora da tela recriado na superfície —, e com ele o `display.quit()/init()` da task 48 desapareceu junto com o `SCALED`; `viewport.restore_window_size()` e `viewport.display_flags()` foram removidos por terem ficado sem chamador. O ícone entrou por `render.create(..., icon=)`, porque cada caminho o define de um jeito (`Window.set_icon` ou `display.set_icon`) e quem chama não deve precisar saber qual. E o profiler recebe `renderer.backend` na construção, então a sobreposição de diagnóstico mostra o nível efetivo da cascata (R26.5).

  **Duas operações a mais no `Renderer`, pelo mesmo motivo:** desde a task 49 é o renderizador que possui a janela, então `window_size` passou a ser dele. No caminho de superfície ele lê `display.get_window_size()` e não `Surface.get_size()` — a superfície de display só acompanha o arrasto no `set_mode` seguinte, a janela já reflete o tamanho novo.

  **`input.py` entrou aqui por necessidade, não por antecipação.** Sem `self.screen` e sem `SCALED`, `InputManager` precisava do renderizador para converter coordenada, e `_touch_to_logical` (que desfazia à mão o letterbox do `SCALED` só para o toque) perdeu o sentido: mouse e toque agora passam pelo mesmo `renderer.to_logical`. É a metade de R34.1 que a task 51 fecha; o resto do escopo dela — os testes de toque na faixa lateral e na faixa de céu em PRONTO e em GAME_OVER — continua aberto.

  **Descoberto na migração — `to_surface` da GPU não é o canvas lógico.** `Renderer.to_surface` devolve uma superfície do tamanho lógico mas copia os pixels *físicos* do alvo, sem desfazer a escala de `logical_size`. `snapshot()` só é fiel quando canvas e janela têm o mesmo tamanho. Não afeta o jogo (é operação de diagnóstico), mas afeta quem for conferir um canvas de celular no PC: force a janela com `BLOCKY_CANVAS` ou use o `SurfaceRenderer`. Documentado na docstring.

  **Testes (`tests/fakes.py`, novo).** `FakeRenderer` registra a sequência de chamadas em vez de pintar, e cada `FakeImage` carrega a chave com que foi pedida — é por ela que o teste reconhece o que foi desenhado (`("text", "PAUSADO", 6, cor)`, `("mute_icon", True)`, `"dirt"`). A ordem preservada é o que permite afirmar sobre oclusão. `test_ui_layout.py`, `test_decor.py`, `test_bands.py`, `test_biome.py`, `test_perf.py` e a parte afetada de `test_game.py` deixaram de inspecionar pixels: "o texto de PAUSADO não invade a linha de baixo" substituiu "o pixel (240, 310) é branco". Dois ganhos além da velocidade — as afirmações passaram a ser sobre o que o código *pede*, e casos que a leitura de pixel não alcançava ficaram verificáveis: que a faixa lateral é desenhada depois da coluna que ela precisa cobrir (R24.4), que o escurecimento é um `fill` e não uma superfície alocada por frame, que o ícone de mudo é uma chamada de desenho por estado, e que o fade de bioma usa `Image.alpha`. **208 testes** (eram 197), `ruff check`, `ruff format --check` e `ty check` sem violações.

- [x] **51. Entrada: conversão de coordenadas pelo backend**
  `input.py` passa a converter mouse e toque pelo mesmo caminho (`renderer.to_logical`), eliminando o tratamento assimétrico da v2 (que dependia de `pygame.SCALED` pré-converter o mouse). O recorte de área deixa de ser contra a área jogável: toque ou clique em qualquer ponto do canvas, faixa decorativa inclusive, dispara a ação de voar (seção 32.8) — o hit-test do ícone de mudo é a única exceção, e só coordenada fora do canvas é descartada. Testes: clique e toque no mesmo ponto físico produzem a mesma ação; toque na faixa lateral e na faixa de céu voam; toque no ícone de mudo alterna o mudo em vez de voar; coordenada fora do canvas é ignorada; em PRONTO e em GAME_OVER o toque na faixa inicia e reinicia a partida. _(R34.1, R34.2, R34.3, R34.4, R25.6, R15.1, R15.4)_

  **Nenhuma linha de comportamento mudou aqui — e isso é o resultado, não um atalho.** A task 50 já tinha entregue as duas metades desta: `to_logical` unificado para mouse e toque (era consequência obrigatória de largar o `SCALED`), e o recorte contra o canvas, que veio de graça porque `_handle_tap` sempre testou contra `config.screen_w()/screen_h()` — e `config` passou a resolver isso pelo viewport ativo na task 45, quando canvas e área jogável se separaram. O que a v3 chama de revogação da regra da v2 tinha, portanto, *já acontecido*, sem que nada afirmasse isso. O que faltava era a verificação, e ela é o entregável da task 51.

  **O que a verificação encontrou primeiro foi um problema nos próprios testes.** `tests/test_input.py` nunca chamava `config.set_viewport`, então rodava sobre o viewport global que o arquivo de teste anterior tivesse deixado — na ordem alfabética, o `WIDE` do fim de `test_bands.py`. Os testes passavam por coincidência (a geometria era consistente consigo mesma), mas nenhum deles estava exercitando o canvas que sua docstring afirmava. Ativar o viewport explicitamente em `_make_input` é o que torna possível dizer "toque na faixa lateral" e ter isso significar alguma coisa.

  **Testes (6 novos, 214 no total).** Um parametrizado sobre as quatro faixas — esquerda e direita num canvas 1280x720, céu e chão num canvas 480x1067 — que toca o centro de cada uma, depois de afirmar que a faixa existe naquela tela e que o ponto está fora de `config.play()` (sem essas duas âncoras o teste passaria por vacuidade numa tela sem faixa). Um para a única exceção: o ícone de mudo dentro da faixa de céu continua alternando o mudo, e não voando (R15.4, R25.6) — é o caso que importa, porque na tela 2:3 que os testes antigos usavam o ícone nem chega a estar numa faixa. E um de ponta a ponta com `Game`: o clique na faixa lateral entra como evento do SDL e sai como transição de estado, PRONTO → JOGANDO e GAME_OVER → PRONTO com placar zerado (R34.4). O teste de descarte fora do canvas foi renomeado e sua justificativa corrigida — não fala mais em "barra preta de letterbox", que a v3 não tem; ele agora força uma janela incompatível com o canvas de propósito, porque no jogo real o canvas cobre a tela e só o arredondamento da conversão escapa pela borda (R34.3).

  **Conferido que os testes prendem mesmo a regra:** trocando `_handle_tap` de volta para o recorte da v2 (`config.play().collidepoint`), os 6 falham e os 8 antigos passam — ou seja, a suíte anterior não tinha nada que impedisse a regra de regredir. Docstrings de `_tap` e `_handle_tap` reescritas com o porquê da revogação (design seção 32.8). Suíte completa verde, `ruff check`, `ruff format --check` e `ty check` sem violações.

### Bloco E — Atlas pré-renderizado

- [ ] **52. Conversão e envio das texturas base**
  `textures.generate_all` e o cache de `pixelfont.render` passam por `convert()`/`convert_alpha()` antes de virarem imagem do renderizador, com degradação para a superfície não convertida quando não há display inicializado (condição real sob driver `dummy`). Testes: as superfícies geradas são convertidas quando há display; a ausência de display não levanta exceção. _(R27.2, R27.4)_

- [ ] **53. Chão pré-renderizado**
  Uma faixa de `canvas_w + BLOCK` por par `(block_main, block_edge)`, cacheada, com o rolamento virando deslocamento do retângulo de origem. De 22 blits para 1 draw call. Teste: um frame de chão emite exatamente uma chamada de desenho, e o resultado visual bate com o da implementação anterior para o mesmo deslocamento. _(R27.2)_

- [ ] **54. Colunas pré-renderizadas e descarte por posição**
  Duas strips de altura do canvas por par de blocos (borda embaixo e borda em cima), recortadas por `area`. De ~24 para 2 draw calls por coluna. Somar descarte das colunas inteiramente fora da área visível — a v2 sempre desenhava um par fora da tela. Testes: duas chamadas por coluna visível; zero chamadas para uma coluna fora da área visível. _(R27.2, R27.7)_

- [ ] **55. Parallax pré-renderizado**
  Cada camada de `decor.py` vira uma strip de `period × N` tiles construída uma vez por bioma, desenhada com wrap-around. Elimina os `random.Random` por frame, os `draw.rect` e os `Rect` intermediários. Teste: o desenho da strip é idêntico ao produzido pelo caminho antigo para os mesmos índices (comparação pixel a pixel da superfície gerada), e nenhum `random.Random` é instanciado durante o desenho. _(R27.2, R27.3)_

- [ ] **56. Abelha, escurecimento e ícone de mudo pré-renderizados**
  As 62 combinações de (ângulo, frame de asa) da abelha viram texturas pré-computadas; `Bird.draw` vira consulta e um draw call. O escurecimento de PAUSADO/GAME_OVER vira `fill` com blend, eliminando a Surface de ~1,4 MB alocada por frame. O ícone de mudo vira duas texturas. Testes: nenhum `transform.rotate` durante o desenho; nenhuma Surface criada durante o desenho do overlay; o ângulo fora da grade é quantizado para a textura mais próxima. _(R27.2, R27.3)_

- [ ] **57. Mobs decorativos (`src/mobs.py`)**
  Nove sprites voxel 16×16 novos em `textures.py`, no estilo procedural de `make_bee`, com 2 frames de idle cada — Overworld: creeper, bruxa, aldeão; Cave: enderman, aranha, esqueleto; Nether: ghast, blaze, piglin. Posicionados apenas nas faixas decorativas, com deriva de parallax própria mais lenta que a camada distante. `mobs.py` recebe apenas `Viewport`, bioma e deslocamento — sem acesso ao estado de jogo. Testes: todo mob desenhado cai fora de `viewport.play`; a colisão ignora os mobs; a pontuação não muda com mobs em tela; cada bioma tem ao menos três variedades e cada sprite tem dois frames distintos. _(R25.3, R25.4)_

### Bloco F — Alocação e coletor de lixo

- [ ] **58. Eliminar alocações por frame**
  `Bird.rect`, `PipePair.top_rect`/`bottom_rect` e `Ground.rect` deixam de ser `property` que alocam e viram retângulos persistentes atualizados no lugar, computados uma vez por passo. `PipeManager.update` e `ParticleSystem.update` param de recriar a lista por frame. `__slots__` em `Bird`, `PipePair` e `Particle`. `ui.draw_text` calcula posição por aritmética em vez de dois `get_rect()`, e `_fit_scale` ganha cache. Teste: um passo de `update` + `draw` em JOGANDO não aumenta a contagem de blocos alocados além de um limite pequeno declarado. _(R27.3)_

- [ ] **59. Ajuste do coletor de lixo (`perf.tune_gc()`)**
  `gc.collect()` + `gc.freeze()` + `gc.set_threshold` elevado ao fim de `Game.__init__`, sem `gc.disable()` (que trocaria pausa por vazamento). Teste: após `tune_gc()`, a contagem de objetos permanentes é maior que zero e os limiares estão acima do padrão. _(R27.3)_

- [ ] **60. Persistência do recorde fora do frame**
  `_update_score` passa a marcar o recorde como sujo em vez de gravar em disco; a gravação acontece em GAME_OVER e em `APP_WILLENTERBACKGROUND`. Preserva a garantia de R4.3/R16.4 que motivou o desenho original. Testes: bater o recorde em JOGANDO não escreve em disco; chegar a GAME_OVER escreve; ir para segundo plano com recorde sujo escreve; ir para segundo plano sem recorde novo não escreve. _(R27.5, R4.3, R16.4)_

### Bloco G — SDL e empacotamento

- [ ] **61. Hints do SDL, filtro de eventos e inicialização do mixer**
  `SDL_HINT_RENDER_SCALE_QUALITY=0` e `SDL_HINT_RENDER_BATCHING=1` antes de criar o renderizador. `pygame.event.set_blocked` para tudo que `input.py` não consome, em especial `FINGERMOTION` e `MOUSEMOTION`. `pygame.mixer.pre_init(...)` antes de `pygame.init()`, eliminando a dupla inicialização do mixer da v2. Testes: os tipos consumidos por `input.py` continuam permitidos e `FINGERMOTION` fica bloqueado; o mixer é inicializado uma única vez. _(R26.6, R26.7, R27.6)_

- [ ] **62. `buildozer.spec` da v3**
  `android.archs` sem `x86_64`, `android.presplash_color`, `version = 0.3.0`, e o `package.name` já trocado na task 42. Validar como INI bem formado. Registrar no design que o ganho é de tamanho e tempo de build, não de FPS. _(R17.1, R22.2)_

### Bloco H — Loop e adaptação

- [ ] **63. Timestep fixo com acumulador**
  `Game.run` passa a acumular o tempo real de `clock.tick()` e a rodar `update()` em passos fixos de 1/60 s, com clamp do delta e teto de passos por frame. `update()` e as constantes ficam intactas. Testes: um frame de 16 ms produz 1 passo; um de 33 ms produz 2; um de 5000 ms produz no máximo o teto e zera o acumulador; a 60 FPS o estado após N frames é idêntico ao da implementação por frame da v2. _(R28.1, R28.2, R28.3, R28.4)_

- [ ] **64. Qualidade adaptativa (`src/quality.py`)**
  Três níveis (ALTO/MÉDIO/BAIXO) conforme a seção 38, com medição em janela deslizante apenas em JOGANDO, histerese na troca e persistência via `storage.save_dir()`. Nada que afete regra muda entre níveis. Testes: FPS sustentado baixo desce de nível; um vale isolado não desce; a subida exige margem e janela maior; velocidade de coluna, gap, hitbox e pontuação são idênticos nos três níveis; arquivo corrompido resulta em nível ALTO. _(R29.1, R29.2, R29.3, R29.4, R29.5, R29.6)_

### Bloco I — Documentação e rigor SDD

- [ ] **65. Docstrings em todo o projeto e gate no ruff**
  Ativar as regras `D` (pydocstyle, convenção `google`) no `pyproject.toml` e preencher as docstrings faltantes em `src/`, `scripts/`, `main.py` e `conftest.py`, em português, respeitando `line-length = 110`. O CI já roda `ruff check`, então o gate entra sem infraestrutura nova. _(R31.1, R31.2, R31.3)_

- [ ] **66. Site de documentação (MkDocs Material + mkdocstrings)**
  `mkdocs.yml` publicando a página de apresentação, a API extraída das docstrings de `src/` via `mkdocstrings[python]`, e os specs de v1/v2/v3 lado a lado. Workflow `.github/workflows/docs.yml` para GitHub Pages. Dependências apenas no grupo `dev`. Validar com `uv run mkdocs build --strict`. _(R31.4, R31.5)_

- [ ] **67. Matriz de rastreabilidade (`specs/v3/traceability.md`)**
  Uma linha por critério de aceitação, ligando requisito → seção de design → task → teste(s). _(R32.1)_

- [ ] **68. Teste que verifica a matriz (`tests/test_traceability.py`)**
  Parse de `requirements.md` extraindo todo critério `RN.M`; falha se algum não estiver na matriz e falha se a matriz citar um teste inexistente. É o que impede o documento de envelhecer em silêncio. _(R32.2, R32.3)_

- [ ] **69. Cobertura mínima no CI**
  `pytest-cov` no grupo `dev`, `--cov=src --cov-fail-under=N` no `pyproject.toml`, com `N` fixado na primeira medição arredondada para baixo e meta declarada de 90%. Adicionar o relatório ao job de CI. _(R32.4)_

- [ ] **70. Atualizar `README.md` e checklists**
  Nome novo, faixas decorativas, aceleração por GPU, e instruções de documentação, benchmark e sobreposição de diagnóstico. Checklist de verificação manual da v3 no formato já usado na v2. _(R22.1, R23.1, R30.1)_

- [ ] **71. Motivação e método SDD no `README.md`**
  Três blocos, reaproveitados como página inicial do site: **por que este projeto existe** (estudar SDD na prática e fazer um jogo para o filho, que gosta de jogos e de Minecraft — o que também explica a temática e o `CREDITS` que está no jogo desde a v1); **o que é SDD**, ancorado nos artefatos deste repositório; e um **prompt de exemplo** pronto para uso, combinando voz de Product Owner (objetivo, público, user stories, critérios EARS, fora de escopo) e de Tech Lead com prática em Python (stack, `uv`, estrutura, `ruff`/`ty`/`pytest` como gate, restrições, e o protocolo de gerar os três documentos antes de codar e implementar uma task por vez), com uma linha explicando o porquê de cada parte e genérico o bastante para servir a outro projeto. _(R33.1, R33.2, R33.3, R33.4, R33.5)_

### Bloco J — Fechamento

- [ ] **72. Build do APK e validação em aparelho real**
  Gerar o APK pelo caminho já documentado, instalar, e conferir: nenhuma barra preta em lado nenhum; o app não gira ao virar o aparelho; `AndroidManifest.xml` com `android:screenOrientation="portrait"`; a sobreposição com `BLOCKY_PERF=1` mostrando FPS sustentado e backend acelerado; a dificuldade igual à do desktop; faixas e mobs visíveis sem interferir no jogo. _(R23.1, R23.3, R23.5, R25.2, R25.3, R26.1, R27.1)_

- [ ] **73. Registrar os números medidos**
  Preencher o bloco `BASELINE` da seção 30 do `design.md` com antes/depois e anotar em cada task o que foi validado aqui e o que dependeu de aparelho real, no estilo já usado na v2. _(R30.5)_

## Checklist de verificação da v3

Verificável automaticamente / no desktop:

- [ ] Nome "Blocky Bee" em título, tela inicial, `.spec` do PyInstaller, `buildozer.spec` e artefatos de release (R22.1) — teste de `TITLE` e inspeção dos arquivos de build
- [ ] `package.name = blockybee` e INI bem formado (R22.2) — validação via `configparser`
- [ ] `specs/v1/` e `specs/v2/` intactas, com o nome antigo preservado (R22.4) — inspeção
- [x] Canvas lógico com a proporção da tela, área jogável sempre 480×720 (R23.4, R24.1) — `tests/test_viewport.py`
- [x] Bandas fecham exatamente com o canvas, sem pixel perdido (R23.4) — `tests/test_viewport.py`
- [x] Nenhuma constante de física ou de bioma alterada (R24.2) — inspeção + testes de física da v1/v2 ainda verdes, mais `tests/test_bands.py::test_fall_is_identical_in_both_canvases`
- [x] Coluna nasce em `play.right` e não aparece fora da área jogável (R24.3, R24.4) — `tests/test_bands.py`
- [x] Teto do voo na borda da área jogável, não do canvas (R24.5) — `tests/test_bands.py`
- [x] Redimensionar a janela recalcula canvas e faixas, mantendo a área jogável (R23.6) — `tests/test_resize.py`
- [ ] Mobs sempre fora da área jogável, sem efeito em colisão ou pontuação (R25.4, R34.5) — `tests/test_mobs.py`
- [ ] Toque/clique em faixa decorativa dispara a ação de voar, com o ícone de mudo como única exceção (R25.6, R34.1, R34.4) — `tests/test_input.py`
- [ ] Mouse e toque no mesmo ponto produzem a mesma ação; coordenada fora do canvas é ignorada (R34.2, R34.3) — `tests/test_input.py`
- [ ] Cascata de render cai de nível sem levantar exceção (R26.2, R26.3) — `tests/test_render.py`
- [ ] Zero `transform.rotate`, `random.Random` ou Surface nova durante o desenho (R27.2, R27.3) — `tests/test_render.py`
- [ ] Sem escrita em disco durante JOGANDO (R27.5) — `tests/test_game.py`
- [ ] `FINGERMOTION`/`MOUSEMOTION` bloqueados (R27.6) — `tests/test_input.py`
- [ ] Timestep fixo: 1 passo a 60 FPS, 2 a 30, teto respeitado em stall (R28.1–R28.3) — `tests/test_game.py`
- [ ] Estado após N frames idêntico ao da v2 a 60 FPS (R28.4) — `tests/test_game.py`
- [ ] Regras idênticas nos três níveis de qualidade (R29.3) — `tests/test_quality.py`
- [ ] Histerese impede oscilação de nível (R29.4) — `tests/test_quality.py`
- [ ] `ruff check` sem violações de docstring (R31.1–R31.3) — CI
- [ ] `mkdocs build --strict` sem avisos (R31.4) — CI
- [ ] Todo critério de aceitação presente na matriz (R32.2) — `tests/test_traceability.py`
- [ ] Cobertura acima do mínimo declarado (R32.4) — CI
- [ ] Ganho medido contra o baseline (R30.5) — `scripts/benchmark.py`

Requer aparelho Android real:

- [ ] Nenhuma barra preta em nenhuma borda (R23.1)
- [ ] Display em tela cheia na resolução nativa (R23.3)
- [ ] O app não gira ao virar o aparelho (R23.5)
- [ ] Faixas decorativas e mobs visíveis e coerentes com o bioma (R25.1, R25.2, R25.3)
- [ ] Toque em qualquer ponto da tela, faixas decorativas inclusive, faz a abelha voar (R34.1)
- [ ] Backend acelerado em uso, mostrado na sobreposição (R26.1, R26.5)
- [ ] 60 FPS sustentado em JOGANDO no aparelho de referência (R27.1)
- [ ] Dificuldade percebida igual à do desktop (R24)
