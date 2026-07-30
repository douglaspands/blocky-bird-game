# Plano de Implementação — Blocky Bird

Tarefas incrementais; cada uma referencia os requisitos que atende. Executar em ordem — cada tarefa deixa o jogo executável.

**Estado desta versão:** as tasks 1–19 são o histórico já concluído na v1 (mantidas aqui para o documento ser autocontido). As tasks 20–30 são o trabalho da v2 (Android), já concluídas. As tasks 31–35 são aumentos de escopo posteriores da v2 (qualidade e correções pós-lançamento), também já concluídas. As tasks 36–37 são o trabalho da v3 (ícone do aplicativo).

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
  `.github/workflows/release.yml`: ao publicar uma Release com tag no GitHub, builda o executável para Windows e Linux (matriz de jobs) e anexa aos assets da release como `BlockyBird-windows-x64-<tag>.zip` e `BlockyBird-linux-x64-<tag>.tar.bz2` via `softprops/action-gh-release`; nome do asset inclui plataforma e arquitetura. _(R13.2)_

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

- [x] **28. Build local do APK e primeira instalação real**
  Gerar o APK via container Docker do Buildozer, instalar em aparelho físico e validar o loop básico (abre, joga por toque, som, recorde persiste após fechar e reabrir). Primeiro ponto em que o jogo roda de fato no Android. _(R17.1, R14.1)_
  **Estado:** Docker ficou disponível neste ambiente (ao contrário do que o design.md/task 27 assumiam) e o build real via `docker run kivy/buildozer android debug` foi executado até `BUILD SUCCESSFUL`, gerando `bin/blockybird-0.2.0-armeabi-v7a_arm64-v8a_x86_64-debug.apk` (62 MB, as 3 ABIs). Vários bugs reais só apareciam nesta etapa (nunca antes exercida) e foram corrigidos:
  - Cache `.buildozer` de uma tentativa anterior tinha `hostpython3` compilado como CPython 3.14 em vez do 3.11.5 esperado do pin `p4a.branch = v2024.01.21` — cache limpo para forçar reclone correto.
  - `docker run -v "$(pwd):..."` a partir do Git Bash montava um volume anônimo vazio em vez do diretório do projeto (path mangling do MSYS) — corrigido com `MSYS_NO_PATHCONV=1`.
  - O cache real do Android SDK/NDK do buildozer vive em `$HOME/.buildozer` **dentro do container** (efêmero a cada `docker run --rm`), mas o marcador "já instalado" fica em `.buildozer/state.db` do projeto (persistido via bind mount) — a inconsistência fazia `platforms;android-34` nunca ser reinstalado em containers novos ("Available Android APIs are ()"). Corrigido montando um diretório persistente do host (`~/.buildozer-android-global-cache`) também em `/home/user/.buildozer`.
  - `p4a-recipes/jpeg/__init__.py` (nova receita local): o `CMakeLists.txt` do libjpeg-turbo 2.0.1 exige `cmake_minimum_required` < 3.5, incompatível com o CMake 4.2.3 do container — corrigido com `-DCMAKE_POLICY_VERSION_MINIMUM=3.5` direto na chamada (variável de ambiente via `docker -e` não chega ao subprocesso, pois `Arch.get_env()` do p4a monta o ambiente do zero); `rm -f` trocado por `rm -rf` para sobreviver a retries.
  - `p4a-recipes/pygame-ce/__init__.py`: faltava `'cython'` em `depends` (a cópia do PR upstream não declarava, ao contrário de outras receitas do p4a que compilam `.pyx`) — `setup.py build_ext` falhava com "You need cython".
  - `p4a-recipes/pygame-ce/__init__.py`: `sdl_image_includes` apontava para a raiz de `jni/SDL2_image`, mas a versão do sdl2_image (2.8.0) move o header público para `jni/SDL2_image/include/SDL_image.h` (diferente do `SDL2_ttf`, que mantém `SDL_ttf.h` na raiz) — `src_c/imageext.c` falhava com "'SDL_image.h' file not found".
  - `buildozer.spec` + novo `android/tv_banner_attribute.txt`: `android.extra_manifest_application_arguments` espera um **caminho de arquivo** (mesma convenção de `android.extra_manifest_xml`), não o texto inline — buildozer faz `open(valor, 'rt').read()`; o valor antigo (a string do atributo) só falhava na etapa de empacotamento/gradle, nunca antes alcançada.
  **Não verificável neste ambiente:** instalação e playtest em aparelho físico (sem Android real disponível) — pendente de validação manual pelo dono do projeto antes de publicar.

- [x] **29. Job de CI do APK na Release**
  Acrescentar ao `release.yml` um job `ubuntu-latest` independente que builda o APK em Docker, com cache de `~/.buildozer`, e anexa `BlockyBird-<tag>.apk` **sem compressão** aos assets — mantendo os dois assets de desktop já existentes. _(R17.2, R13.3)_
  **Implementação:** job `build-apk` em `.github/workflows/release.yml`, independente do job `build` (matriz Windows/Linux) para que uma falha na cadeia Android (a parte mais frágil, task 27) não impeça a publicação dos executáveis de desktop. `docker pull kivy/buildozer` + `docker run … kivy/buildozer android debug`, com `yes y |` porque a imagem recusa rodar como root e porque o primeiro build precisa aceitar as licenças do Android SDK interativamente. APK renomeado para `BlockyBird-<tag>.apk` e publicado via `softprops/action-gh-release@v2`, que copia o arquivo como está (o `.apk` já é um zip; a action não o recomprime).
  **Ajuste feito na implementação:** o `docker run` inicial só montava `${{ github.workspace }}:/home/user/hostcwd`, sem o segundo volume documentado pela própria imagem oficial (`kivy/buildozer` no Docker Hub) para persistir cache entre execuções — `-v "$HOME/.buildozer":/home/user/.buildozer`, onde SDK/NDK baixados ficam guardados fora do diretório do projeto. Sem esse mount, o cache de `actions/cache` no path `~/.buildozer` (pedido pelo design, seção 24.3) sempre voltaria vazio, forçando o download completo de SDK+NDK (30–60 min) em toda execução. Corrigido adicionando os dois volumes e cacheando ambos os paths (`~/.buildozer` e `.buildozer`) na mesma entrada de `actions/cache`.
  **Não verificável neste ambiente:** execução real do job (exige Docker + uma Release publicada no GitHub, ver design seção 25) — validado apenas como YAML bem formado (`yaml.safe_load`) e por leitura cruzada com a documentação oficial da imagem `kivy/buildozer` para confirmar os volumes/paths de cache corretos. Fica para a task 30 (ou uma release de teste) confirmar que o job efetivamente builda e anexa o APK.

- [x] **30. Ajuste de áudio/performance no Android e verificação final da v2**
  Ajustar o buffer do mixer para Android e medir o tempo de frame em aparelho de entrada; completar o checklist manual em celular **e** em Android TV; atualizar o README com instruções de instalação do APK. _(R8.4, R9.5, R14.6, todos)_
  **Implementado e verificável neste ambiente:** `sounds.py` agora chama `pygame.mixer.init(..., buffer=1024)` quando `storage.is_android()` é verdadeiro (mantendo o default do pygame no desktop, sem regressão), conforme o valor inicial documentado no design (seção 11) — `2048` fica como próximo passo caso o playtest real em aparelho ainda acuse estouro/crepitação com `1024`. Coberto por `tests/test_sounds.py` (2 testes, mockando `is_android` e `pygame.mixer.init` para inspecionar os kwargs passados). README atualizado com seção "Instalar no Android" (fontes desconhecidas, controles por toque/BACK/D-pad em TV, requisito de API 21) e o comando `docker run` para reproduzir o build do APK localmente. Suíte completa: 65 testes passando.
  **Não verificável neste ambiente (sem Android real nem emulador, ver design seção 25):** medir o tempo de frame em aparelho de entrada (R9.5), confirmar que `buffer=1024` de fato elimina estouros/crepitação no hardware real (R8.4) — se não eliminar, subir para `ANDROID_MIXER_BUFFER = 2048` em `sounds.py` — e os itens de checklist abaixo marcados como "requer aparelho Android real" / "requer Android TV real". Ficam pendentes de validação manual pelo dono do projeto antes de considerar a v2 encerrada.

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
- [x] Publicar uma Release de teste no GitHub e confirmar que os assets `BlockyBird-windows-<tag>.zip` e `BlockyBird-linux-<tag>.tar.bz2` aparecem automaticamente (R13.2) — Release `v1.0.0` publicada em `douglaspands/blocky-bird-game`, com `BlockyBird-linux-v1.0.0.tar.bz2` e `BlockyBird-windows-v1.0.0.zip` anexados automaticamente pelo `github-actions[bot]`, confirmado via API pública do GitHub

## Checklist de verificação da v2 (Android)

Ver design seção 25 para o motivo da separação. Os itens de **hardware real** não podem
ser validados no ambiente de desenvolvimento e exigem teste manual do dono do projeto —
não marcar sem ter testado de fato no aparelho.

Verificável automaticamente / no desktop:

- [x] Todas as telas renderizam com a fonte bitmap própria, sem `SysFont`, mantendo alinhamento (R7.6) — confirmado por inspeção (`grep SysFont src/`: só ocorre em comentários explicativos, nenhum uso real) e visualmente durante a task 20
- [x] Redimensionar a janela mantém a proporção com barras, sem distorcer nem deslocar o gameplay (R9.1, R14.3) — validado com janela real 900×500 na task 21 (pillarbox correto, coordenada do mouse conferida por instrumentação direta)
- [x] Toque em coordenada normalizada converte corretamente para o espaço lógico; toque na barra é ignorado (R15.1) — `tests/test_input.py::test_finger_tap_in_game_area_flaps`, `test_finger_tap_outside_logical_area_is_ignored`
- [x] `storage.save_dir()` devolve o caminho Android quando `ANDROID_ARGUMENT` está definido e o caminho do projeto quando não está (R4.5) — `tests/test_storage.py`
- [x] Recorde é gravado no momento em que o score ultrapassa o recorde, não só no GAME_OVER (R4.3, R16.4) — `tests/test_game.py::test_highscore_saved_incrementally_mid_round`
- [x] Ação `back` pausa em JOGANDO e encerra nos outros estados (R15.2, R15.3) — `tests/test_game.py::test_back_in_*`
- [x] Perder foco da janela (alt-tab) leva JOGANDO → PAUSADO e não retoma sozinho (R16.1, R16.2) — `tests/test_game.py::test_focus_lost_*`
- [x] `K_RETURN` dispara flap (equivalente ao botão central de controle remoto) (R14.4) — `tests/test_input.py::test_return_and_kp_enter_flap`
- [x] Suíte `pytest` completa continua passando após a migração para `pygame-ce` (R9.2) — 65 testes, `SDL_VIDEODRIVER=dummy uv run pytest`

Requer aparelho Android real (celular):

- [ ] APK instala por download direto, com "fontes desconhecidas", sem descompactar nada (R17.1, R17.2)
- [ ] Toque em qualquer ponto faz o pássaro voar; iniciar e reiniciar funcionam por toque (R15.1)
- [ ] Ícone de mudo responde ao toque e silencia de fato (R15.4)
- [ ] BACK pausa durante o jogo e encerra o app nas telas de PRONTO/PAUSADO/GAME_OVER (R15.2, R15.3)
- [ ] Trocar de app / receber ligação pausa automaticamente; ao voltar continua pausado (R16.1, R16.2)
- [ ] Recorde sobrevive a fechar e reabrir o app, e a encerramento forçado pelo sistema (R4.5, R16.4)
- [ ] Imagem preenche a tela inteira sem barra preta, mantendo a proporção correta e sem corte de UI (R14.3) — item reaberto pela task 35 após relato real no Galaxy S20 FE; antes da task 35 tolerava barra, agora não deveria sobrar nenhuma
- [ ] Áudio sem estouros/crepitação (R8.4, buffer do mixer)
- [ ] 60 FPS em aparelho de entrada (R9.5)
- [ ] Ícone do launcher mostra a abelha inteira, sem cortar antenas/asas, em qualquer forma de máscara do fabricante (R21.4, R21.5) — task 37

Requer Android TV real:

- [ ] App aparece na home da TV com o banner (R17.3)
- [ ] Jogo é totalmente operável pelo controle remoto, sem toque: iniciar, voar, pausar, reiniciar (R14.4)
- [ ] Mudo alcançável por D-pad na tela de PAUSADO (R15.4)
- [ ] Imagem em paisagem preenche a tela inteira sem barra preta, UI inteira visível (sem corte por overscan) (R14.3) — antes da task 35 esperava-se pillarbox (seção 20.1); agora o fundo deve estender até as bordas

## Tarefas adicionais da v2 (pós-Android) — Qualidade

Aumento de escopo pedido depois que as tasks 20–30 (Android) já estavam concluídas: conformidade com `ruff` em todo o código Python, calibração do tamanho de fonte para eliminar sobreposição de texto nas telas, correção de bug de persistência do recorde no executável empacotado, conformidade com `ty` (checagem de tipos) e preenchimento de tela sem barra preta no Android mantendo a proporção.

- [x] **31. Conformidade com Ruff**
  Adicionar `ruff` como dependência de dev (`uv add --dev ruff`), configurar `[tool.ruff]` em `pyproject.toml` (`line-length = 110`, `target-version = "py310"`, regras `E, F, W, I, UP, B, SIM, RUF`, ver design seção 26). Rodar `uv run ruff check --fix .` e `uv run ruff format .` sobre `main.py`, `src/`, `tests/`, `scripts/`, `p4a-recipes/`; revisar manualmente qualquer correção automática que mude comportamento (não só estilo) antes de aceitar. Corrigir à mão o que `--fix` não resolver. Criar `.github/workflows/ci.yml` (`on: push, pull_request`) rodando `ruff check`, `ruff format --check` e `pytest` (`SDL_VIDEODRIVER=dummy`) no mesmo job. Confirmar `uv run pytest` completo continua verde após as correções de lint. _(R18)_
  **Ajuste feito na implementação:** `uv run ruff format .` reformata por padrão também blocos de código Python dentro de cercas ```` ```python ```` em arquivos `.md` (comportamento desta versão do ruff, 0.16.0) — isso reformatou `specs/v1/design.md`, violando a regra do próprio projeto de nunca editar pastas de versões anteriores já concluídas (`specs/README.md`). Corrigido com `extend-exclude = ["specs"]` em `[tool.ruff]`, restringindo a varredura de fato ao código do jogo (o escopo já pretendido pelo design, que nunca mencionava `specs/`).
  **Violações reais encontradas (15 no total, 7 corrigidas por `--fix`, 8 à mão):** auto-fix foi só estilo (ordenação de imports em `p4a-recipes/jpeg/__init__.py`, `.format()` → f-string, `noqa` órfão, `typing.Callable` → `collections.abc.Callable` em `decor.py`). À mão: `RUF012` (atributos de classe mutáveis `built_libraries`/`depends` nas receitas p4a — anotados com `ClassVar`, já que são o padrão de configuração do próprio framework p4a, não um bug real); `SIM115` (dois `open()` sem context manager em `p4a-recipes/pygame-ce/__init__.py` — convertidos para `with`); `B905` (dois `zip()` sem `strict=` em `src/biome.py` e `scripts/generate_tv_banner.py` — ambos combinam tuplas RGB de tamanho fixo e igual, `strict=True` é correto e não muda comportamento); `E501` (duas docstrings de uma linha em `src/biome.py`/`src/pipes.py` acima de 110 colunas — quebradas em docstring de duas linhas, sem alterar o texto).
  **Suíte completa (65 testes) permanece verde após todas as correções.**

- [x] **32. Calibração de tamanho de fonte sem sobreposição**
  Implementar `ui._stack()` (empilhamento vertical por altura real de linha, ver design seção 27) e migrar `draw_ready_screen`, `draw_paused_overlay` e `draw_game_over_screen` para usá-lo em vez dos deltas fixos em pixels atuais. Revisar visualmente (`uv run main.py`) o `base_size`/escala de cada papel de texto (título, créditos, instrução, HUD, overlay de pausa, textos de game over, recorde) até nenhuma sobreposição ser visível em nenhuma das quatro telas, registrando os valores finais escolhidos. Criar `tests/test_ui_layout.py` com um teste por tela que renderiza os textos reais (incluindo `RECORDE: 999999` para o caso de recorde com muitos dígitos) e assere que nenhum par de retângulos se sobrepõe e que todos ficam dentro de `[20, SCREEN_W - 20]` horizontalmente e fora da área do chão verticalmente; incluir o retângulo do ícone de mudo (`ui.MUTE_ICON_RECT`) na checagem das telas onde ele aparece. _(R19)_
  **`ui._stack(surface, center_x, top_y, lines, margin=8)` implementado:** recebe `(text, base_size, color)` na ordem de exibição, calcula a escala real de cada linha via `_fit_scale`/`_scale_for` já existentes, delega o desenho a `draw_text` (mesma função usada fora do stack, o que manteve um único ponto de instrumentação para os testes) e avança a posição vertical por `GLYPH_H * escala + SHADOW_OFFSET + margin` — nunca por uma constante escolhida a olho.
  **`base_size` finais escolhidos (calibração visual via screenshots offscreen com as telas reais, incluindo `RECORDE: 999999`):** título (`BLOCKY BIRD`/`PAUSADO`/`GAME OVER`) `base_size=12` (escala 6, contra 18/escala 9 antes); texto secundário de destaque (`PONTOS`/`RECORDE` no game over) `base_size=8` (escala 4, igual ao recorde da tela PRONTO); instrução/dica (`ESPACO / CLIQUE PARA VOAR`, `ESPACO / CLIQUE PARA REINICIAR`, `SETAS: MUDO`) `base_size=5`-`6` (escala 2-3); créditos `base_size=5` (escala 2); HUD de score `base_size=12` (escala 6, reduzido de 20/escala 10 — o valor antigo já quase tocava o topo da tela). Nenhuma sobreposição visível nas quatro telas nem no pior caso (`RECORDE: 999999`); confirmado também com um smoke test real (`uv run main.py`) sem exceptions.
  **`tests/test_ui_layout.py`:** `_rects_for_screen` monkeypatcha `ui.draw_text` (interceptado também dentro de `_stack`, já que é a mesma função do módulo) para capturar, por linha, um `pygame.Rect` de texto+sombra sem duplicar a lógica de renderização. Um teste por tela (PRONTO, HUD, PAUSADO, GAME_OVER) chama isso com os textos reais — incluindo `999999` — e verifica ausência de sobreposição (incluindo contra `ui.MUTE_ICON_RECT`, presente em todas as telas pois `game.py` o desenha incondicionalmente) e que cada retângulo de texto fica em `[20, SCREEN_W - 20]` horizontalmente e acima de `GROUND_Y` verticalmente. `MUTE_ICON_RECT` entra só na checagem de colisão, não na de limites horizontais — ele fica a propósito perto da borda direita (dentro da margem de 14px do ícone, não da margem de 20px do texto). Suíte completa: 69 testes (65 + 4 novos), `SDL_VIDEODRIVER=dummy uv run pytest`.

- [x] **33. Corrigir persistência do recorde no executável Windows/Linux empacotado**
  Bug reportado pelo dono do projeto: no executável Windows gerado por `BlockyBird.spec`, o recorde deixou de persistir e `highscore.json` não era mais criado ao lado do `.exe`. Causa raiz: `storage.save_dir()` resolvia o diretório desktop a partir de `Path(__file__).resolve().parent.parent`, mas o PyInstaller empacota em modo **onefile** (`EXE(pyz, a.scripts, a.binaries, a.datas, ...)` numa única chamada), e nesse modo `__file__` do módulo aponta para o diretório temporário de extração (`sys._MEIPASS`), apagado ao fechar o processo — nunca para a pasta real do executável. O mesmo problema afeta o build Linux (mesmo `.spec`), ainda não reportado. Corrigido em `storage.py` com `is_frozen()` (checa `sys.frozen`, atributo que o PyInstaller injeta em runtime) e, quando verdadeiro, `save_dir()` retorna `Path(sys.executable).resolve().parent` em vez do caminho baseado em `__file__`; Android (`is_android()`) e desktop rodando de fonte (`uv run main.py`) continuam com o comportamento anterior. Ver design seção 23. _(R4.5)_
  **Decisão de design confirmada com o dono do projeto:** gravar ao lado do executável (não em um diretório padrão de dados do SO como `%APPDATA%`), já que a distribuição é um zip/tar portátil (R13.2) e não uma instalação em local somente-leitura como `Program Files`.
  **Validado:** `tests/test_storage.py::test_save_dir_frozen_desktop_uses_executable_dir` (simula `sys.frozen`/`sys.executable` via `monkeypatch`); suíte completa (70 testes) verde. Build real via `uv run pyinstaller BlockyBird.spec` e verificação manual em `dist/BlockyBird.exe`: com `sys.frozen`/`sys.executable` simulados apontando para o executável gerado, `storage.save_dir()` resolve para `dist/`, `score.save_highscore()` cria `dist/highscore.json` ao lado do `.exe` e `score.load_highscore()` recupera o valor salvo corretamente.

- [x] **34. Conformidade com ty (checagem de tipos)**
  Adicionar `ty` como dependência de dev (`uv add --dev ty`), configurar `[tool.ty.environment]`/`[tool.ty.src]` em `pyproject.toml` (`python-version = "3.10"`, `exclude = ["p4a-recipes", "specs", ".buildozer", "build", "dist"]`, ver design seção 28). Rodar `uv run ty check .` sobre `main.py`, `src/`, `tests/`, `scripts/`; corrigir violações reais no código, suprimir com `# ty: ignore[regra]` + comentário curto só quando a causa é uma limitação do checador (módulo só resolvível em runtime de outra plataforma, atributo dinâmico em teste). Adicionar step `ty check .` em `.github/workflows/ci.yml`, entre `ruff format --check` e `pytest`. Confirmar `uv run pytest` e `ruff check`/`ruff format --check` continuam verdes. _(R20)_
  **`p4a-recipes/` excluído do escopo:** diferente do `ruff` (task 31, que inclui as receitas por serem código próprio do projeto), `ty` precisa *resolver* imports de verdade — e as receitas importam `sh`/`pythonforandroid.*`, pacotes que só existem dentro da imagem Docker do buildozer (R17), nunca no `.venv` local. Incluí-las geraria só `unresolved-import` permanente e não-acionável.
  **Violações reais encontradas (3, todas corrigidas no código, nenhuma suprimida):** `src/biome.py` (`_lerp_color`) e `src/particles.py` (`ParticleSystem.burst`) construíam uma cor RGB a partir de expressão de tamanho variável (genexpr / slice de `pygame.Color`) e atribuíam a `tuple[int, int, int]` — `ty` infere `tuple[int, ...]` para as duas formas; corrigido desempacotando em variáveis nomeadas e retornando/atribuindo um literal de 3-tupla. `src/input.py` (`InputManager`) anotava `dict[int, pygame.joystick.Joystick]`, mas o próprio stub do pygame-ce documenta `Joystick` como função-fábrica (não classe) nesta versão da lib; corrigido usando `pygame.joystick.JoystickType` (o tipo real da instância) e removida a chamada redundante `joystick.init()` (deprecated desde 2.0.0, a construção já inicializa).
  **Supressões pontuais (2, com comentário explicando o motivo):** `src/storage.py` — `from android.storage import app_storage_path` dentro do `try/except ImportError` (seção 23), módulo só existe em runtime p4a; `# ty: ignore[unresolved-import]`. `tests/test_storage.py` — atribuição dinâmica de atributos a um fake `types.ModuleType` para simular o módulo `android.storage` injetado pelo p4a nos testes; `# ty: ignore[unresolved-attribute]`.
  **Validado:** `uv run ty check .` reporta zero diagnósticos; suíte completa (70 testes) e `ruff check`/`ruff format --check` permanecem verdes.

- [x] **35. Preencher a tela no Android sem barra preta, mantendo a proporção**
  Bug reportado pelo dono do projeto: no Galaxy S20 FE sobra uma faixa preta nas laterais em vez da tela preenchida — comportamento que a v2 original considerava aceitável (R14.3 original: letterbox/pillarbox conforme a proporção do aparelho, ver design seção 20.1). Em vez de barra preta, estender o canvas real até a proporção do aparelho (`src/screen_adapt.py::adapted_canvas_size`), mantendo a área jogável fixa em 480×720 (calibração da task 12 intocada) e desenhando-a numa subsurface centralizada/ancorada no chão dentro do canvas maior; só o fundo (`biome.draw_background`, `decor.draw`) se estende pelo canvas inteiro. Atualizar `input.InputManager` para converter toque/clique considerando o canvas e o offset da área jogável. Ver design seção 20.1.1 e R14.3 refinado. _(R14.3)_
  **Não reproduzível neste ambiente:** sem Android real disponível (mesma limitação da seção 25), não foi possível confirmar a causa exata do pillarbox lateral relatado no S20 FE (a tabela medida na seção 20.1, calculada só a partir da proporção 1080×2400, previa letterbox topo/base, não pillarbox lateral — possíveis causas não confirmáveis aqui: orientação paisagem no aparelho, ou área útil reduzida pela barra de sistema). Por isso a correção é genérica: mede a proporção real via `pygame.display.Info()` em runtime e estende o eixo que sobrar, funcionando independente da causa exata e cobrindo também o caso já conhecido da Android TV (pillarbox de 62%, seção 20.1).
  **Suíte completa: 81 testes (70 + 11 novos — 5 em `test_screen_adapt.py`, 2 em `test_decor.py` novo, 2 em `test_biome.py` e 2 em `test_input.py`) permanece verde; `ruff check`/`ruff format --check`/`ty check` sem violações.** Smoke test manual no desktop (`uv run main.py`) sem exceções — comportamento idêntico ao anterior, já que no desktop o canvas continua igual à área jogável (480×720, offset zero).
  **Não verificável neste ambiente:** preenchimento real de tela sem barra no Galaxy S20 FE e em Android TV exige aparelho físico + build APK (mesma limitação das tasks 27–30) — fica pendente de validação manual do dono do projeto antes de publicar; os itens correspondentes no checklist da v2 (abaixo) continuam sem marcar até essa validação.

## Tarefas da v3 — Ícone do aplicativo

Pedido do dono do projeto: o ícone do app deve ser a personagem do jogo (a abelha), e no Android o ícone precisa aparecer "com as proporções ajustadas" — sem cortar a personagem quando o launcher aplica sua máscara (círculo/squircle/quadrado arredondado). Ver design.md seção 29.

- [x] **36. Geração do ícone por código e integração no desktop**
  Criar `scripts/generate_app_icon.py` (padrão de `scripts/generate_tv_banner.py`, reaproveitando `textures.make_bee`): gera `assets/app_icon_512.png` (janela + fonte do `.ico`), `assets/app_icon.ico` (multi-resolução 16–256px, construído via `struct` da stdlib embutindo PNGs, sem depender de Pillow) e `assets/android_icon_legacy.png`. Criar `src/assets.py::asset_path()` (resolve `sys._MEIPASS` quando `storage.is_frozen()`, raiz do projeto caso contrário) e chamar `pygame.display.set_icon()` em `Game.__init__` (`src/game.py`), envolvido em `try/except` para degradação graciosa. Atualizar `BlockyBird.spec`: `datas=[('assets/app_icon_512.png', 'assets')]` no `Analysis` e `icon='assets/app_icon.ico'` no `EXE`. Testes para as funções puras do script (ajuste de escala, construção do `.ico`) e para `asset_path()` nos dois ramos. Validar rodando `uv run main.py` (ícone na barra de título) e gerando o executável (`uv run pyinstaller BlockyBird.spec`, ícone no `.exe`/Explorer). _(R21.1, R21.2, R21.3, R21.7)_
  **Implementado conforme o design (seção 29.1–29.3), sem desvios.** `make_composed_icon()` desenha o mesmo tipo de cena do banner de TV (céu do Overworld + faixa de grama/terra + abelha centralizada), reamostrada em escala nearest-neighbor (pixel-art fiel, R7.1); só o `.ico` usa `smoothscale` nos tamanhos pequenos (16–48px), documentado no design como o único ponto onde a suavização é aceitável. `build_ico()` monta o container `ICONDIR`/`ICONDIRENTRY` manualmente com `struct`, embutindo um PNG por resolução (16/32/48/64/128/256) — validado por round-trip (`pygame.image.load` de cada entrada extraída de volta) tanto no teste automatizado quanto por `file assets/app_icon.ico` (reconhecido como "MS Windows icon resource" com 6 ícones).
  **`src/assets.py::asset_path()`**: replica o padrão já usado por `storage.py` (seção 23), mas na direção oposta — `sys._MEIPASS` é onde o PyInstaller onefile *extrai* dados para leitura (correto aqui), ao contrário de `storage.save_dir()`, que evita `_MEIPASS` de propósito por ser efêmero (não serve para *gravar* o recorde, task 33). `Game.__init__` chama `pygame.display.set_icon()` envolvido em `contextlib.suppress(OSError, pygame.error)` (troca de um `try/except: pass` por sugestão do `ruff`/SIM105) antes do `set_mode`, sem custo perceptível no Android (onde não há efeito visível, mas também não há necessidade de um `if is_android()` para pular — `asset_path()` já resolve para a raiz do projeto lá, e o arquivo existe no APK via `source.include_exts = py,png`).
  **Validado:** suíte completa (87 testes = 81 anteriores + 6 novos, `tests/test_assets.py` e `tests/test_generate_app_icon.py`) verde; `ruff check`/`ruff format --check`/`ty check` sem violações. Smoke test real (não headless) de `uv run main.py` por alguns segundos sem exceções. Build real via `uv run pyinstaller BlockyBird.spec`: log confirma `"Copying icon to EXE"`; `dist/BlockyBird.exe` executado por alguns segundos sem exceções.
  **Não verificado visualmente neste ambiente:** confirmar a olho que o ícone da abelha aparece de fato na barra de título/taskbar e no Explorer (o smoke test só confirma ausência de erro, não a aparência) — recomenda-se uma checagem visual rápida pelo dono do projeto antes de publicar.

- [x] **37. Ícone adaptativo do Android no `buildozer.spec`**
  Estender `scripts/generate_app_icon.py` para também gerar `assets/android_icon_foreground.png` (432×432, só a abelha, escalada para caber nos 66/108 dp da zona segura de máscara) e `assets/android_icon_background.png` (432×432, gradiente de céu do Overworld, opaco, sem a abelha). Adicionar ao `buildozer.spec`: `icon.filename` (aponta para o ícone legado da task 36, cobre API < 26), `icon.adaptive_foreground.filename` e `icon.adaptive_background.filename` (cobrem API ≥ 26, R21.4–R21.6). Validar `buildozer.spec` como INI bem formado e as dimensões/canal alfa dos PNGs gerados; se Docker estiver acessível neste ambiente (ver design seção 25), rodar o build real do APK e confirmar `BUILD SUCCESSFUL` com as novas chaves. _(R21.4, R21.5, R21.6, R21.7)_
  **As três camadas já foram geradas na task 36** (mesmo `scripts/generate_app_icon.py`, seção 29.1 do design) — esta task só adiciona as três chaves correspondentes no `[app]` do `buildozer.spec`, seguindo o estilo de caminho relativo já usado no arquivo (sem `%(source.dir)s`, já que `source.dir = .` torna as duas formas equivalentes aqui). Validado como INI bem formado via `configparser` (mesma checagem das tasks 27/31).
  **Docker estava acessível neste ambiente** (imagem `kivy/buildozer:latest` já em cache local, `Buildozer 1.6.1.dev0`) **e o build real foi executado ponta a ponta**, reaproveitando o cache de SDK/NDK persistido de uma sessão anterior (`~/.buildozer-android-global-cache`, ~2.6 GB) e o `.buildozer/` do projeto — `BUILD SUCCESSFUL in 1m 36s`, gerando `bin/blockybird-0.2.0-armeabi-v7a_arm64-v8a_x86_64-debug.apk` (62 MB). O comando `p4a` invocado pelo buildozer (visível no log) confirma a tradução das três chaves do spec para as flags reais do python-for-android: `--icon .../android_icon_legacy.png --icon-fg .../android_icon_foreground.png --icon-bg .../android_icon_background.png`.
  **Verificação real do conteúdo do APK (além do log de build), inspecionando o `.apk` extraído (é um zip):** `res/mipmap-anydpi-v26/icon.xml` existe e contém as strings `adaptive-icon`/`background`/`foreground` (XML binário compilado pelo aapt, confirmando um `<adaptive-icon>` de verdade, não um ícone comum); `res/mipmap/icon_foreground.png` (432×432, RGBA — canal alfa presente, confirmando a camada transparente) e `res/mipmap/icon_background.png` (432×432, RGB — sem alfa, confirmando a camada opaca) batem em dimensão **e em tamanho de arquivo em bytes** com os PNGs gerados por `scripts/generate_app_icon.py` (1277 e 1488 bytes respectivamente) — prova de que são exatamente os arquivos gerados, não um fallback ou um ícone padrão do template. `res/mipmap/icon.png` (2292 bytes) também bate com `android_icon_legacy.png`, confirmando o ícone legado (API < 26).
  **Ainda não verificável neste ambiente:** a composição final da máscara pelo launcher (círculo/squircle/quadrado arredondado) só é visível de fato num aparelho ou emulador Android real — o que foi verificado aqui é que os recursos corretos (as camadas certas, nos tamanhos certos, com/sem alfa conforme esperado) chegam ao APK; a etapa que falta é inteiramente do lado do sistema operacional Android no aparelho, fora do alcance deste ambiente (mesma limitação da seção 25). Recomenda-se instalar o APK gerado (ou o de uma Release futura) num celular e confirmar visualmente que a abelha aparece inteira, sem antenas/asas cortadas, em qualquer forma de ícone que o launcher use.
