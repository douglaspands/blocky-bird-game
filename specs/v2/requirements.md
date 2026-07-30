# Requisitos — Blocky Bird (Flappy Bird com temática Minecraft)

## Introdução

Blocky Bird é um clone de Flappy Bird em Python/Pygame com temática Minecraft. O jogador controla uma abelha voxel que voa entre colunas de blocos, com progressão de biomas (Overworld → Cave → Nether), efeitos sonoros e partículas de blocos. Todos os gráficos e sons são gerados por código — sem assets externos ou material protegido da Mojang.

**Escopo da v2:** além de tudo que a v1 entregou (jogo completo para desktop, ver `specs/v1/`), a v2 torna o jogo jogável em Android — celular/tablet e Android TV — no maior número possível de aparelhos, distribuído como APK instalável diretamente. Inclui também dois itens de qualidade que não mudam o gameplay, adicionados como aumento de escopo após a entrega Android: (1) todo o código Python do projeto passa a ser verificado pela ferramenta `ruff` (lint + formatação), com conformidade obrigatória e checada em CI; (2) calibração do tamanho da fonte bitmap própria (R7.6), que estava grande demais em várias telas a ponto de textos se sobreporem entre si ou com outros elementos de UI. O desktop continua suportado; nenhum requisito da v1 é removido.

Notação: critérios de aceitação em formato EARS (`QUANDO <evento>, O sistema DEVE <resposta>`).

---

## R1 — Controle do pássaro

**User story:** Como jogador, quero controlar o voo da abelha com um único comando, para que o jogo seja simples de aprender.

### Critérios de aceitação

1. QUANDO o jogador pressiona ESPAÇO, seta ↑, clica com o mouse ou pressiona o botão A do controle de Xbox, O sistema DEVE aplicar impulso vertical para cima ao pássaro.
2. ENQUANTO o jogo está em estado JOGANDO, O sistema DEVE aplicar gravidade constante ao pássaro a cada frame.
3. QUANDO o pássaro sobe, O sistema DEVE rotacionar o sprite para cima (máx. +30°); QUANDO cai, rotacionar gradualmente para baixo (máx. −60°).
4. QUANDO o pássaro atinge o topo da tela, O sistema DEVE limitar sua posição ao topo sem encerrar o jogo.

## R2 — Obstáculos

**User story:** Como jogador, quero desviar de colunas de blocos, para que exista desafio.

### Critérios de aceitação

1. ENQUANTO o jogo está em estado JOGANDO, O sistema DEVE gerar pares de colunas (superior/inferior) em intervalos fixos de distância horizontal.
2. QUANDO um par de colunas é gerado, O sistema DEVE posicionar a abertura vertical em altura aleatória, com tamanho de abertura definido pelo bioma atual.
3. ENQUANTO o jogo está em estado JOGANDO, O sistema DEVE mover as colunas da direita para a esquerda na velocidade definida pelo bioma atual.
4. QUANDO uma coluna sai completamente da tela pela esquerda, O sistema DEVE removê-la da memória.
5. QUANDO uma coluna é renderizada, O sistema DEVE desenhá-la como pilha de blocos texturizados do bioma atual (Overworld: terra/grama; Cave: pedra/pedregulho; Nether: netherrack/obsidiana).

## R3 — Colisão e fim de jogo

**User story:** Como jogador, quero que o jogo termine ao colidir, para que haja consequência por erro.

### Critérios de aceitação

1. QUANDO o pássaro colide com uma coluna ou com o chão, O sistema DEVE transicionar para o estado GAME_OVER.
2. QUANDO ocorre colisão, O sistema DEVE emitir partículas de bloco quebrando no ponto de impacto e tocar o som de dano.
3. ENQUANTO em estado GAME_OVER, O sistema DEVE exibir tela de fim ("Game Over" estilizado, pontuação atual e recorde) e congelar o movimento dos obstáculos.
4. QUANDO o jogador pressiona ESPAÇO, clica ou pressiona o botão A do controle na tela de GAME_OVER, O sistema DEVE reiniciar a partida no estado PRONTO.
5. A detecção de colisão DEVE usar hitbox retangular do pássaro reduzida (~85% do sprite) para tolerância justa.

## R4 — Pontuação

**User story:** Como jogador, quero acumular pontos e ver meu recorde, para medir meu progresso.

### Critérios de aceitação

1. QUANDO o pássaro ultrapassa completamente uma coluna, O sistema DEVE incrementar a pontuação em 1 ponto e tocar o som de ponto (estilo XP orb).
2. ENQUANTO o jogo está em estado JOGANDO, O sistema DEVE exibir a pontuação atual no topo da tela em fonte pixelada.
3. QUANDO a pontuação da partida em curso supera o recorde, O sistema DEVE atualizar o recorde e persisti-lo em arquivo local (`highscore.json`) — sem esperar o fim da partida, para que o recorde sobreviva ao encerramento abrupto do app pelo sistema operacional (comum em Android).
4. QUANDO o jogo inicia, O sistema DEVE carregar o recorde do arquivo local; SE o arquivo não existir ou estiver corrompido, O sistema DEVE assumir recorde 0.
5. O arquivo de recorde DEVE ser gravado em diretório com permissão de escrita garantida na plataforma (em Android, o armazenamento privado do app; no desktop, a raiz do projeto), nunca dependendo do diretório de trabalho corrente.

## R5 — Progressão de biomas

**User story:** Como jogador, quero que o cenário e a dificuldade evoluam conforme pontuo, para manter o jogo interessante.

### Critérios de aceitação

1. QUANDO a pontuação atinge 0, 10 e 25 pontos, O sistema DEVE ativar respectivamente os biomas Overworld, Cave e Nether.
2. QUANDO um bioma é ativado, O sistema DEVE aplicar seus parâmetros: cor de fundo/decoração, texturas das colunas, velocidade de rolagem e tamanho da abertura.
3. A dificuldade DEVE crescer por bioma: Overworld (velocidade 2.5, abertura 160 px), Cave (3.0, 145 px), Nether (3.5, 130 px) — valores de referência ajustáveis no design.
4. QUANDO ocorre transição de bioma, O sistema DEVE fazer transição visual gradual do fundo (fade ≤ 1 s) e exibir o nome do bioma brevemente na tela.

## R6 — Estados do jogo

**User story:** Como jogador, quero telas claras de início e fim, para entender o que fazer.

### Critérios de aceitação

1. QUANDO o jogo abre, O sistema DEVE exibir o estado PRONTO com título, pássaro flutuando (animação idle) e instrução de comando.
2. QUANDO o jogador dá o primeiro comando de voo no estado PRONTO, O sistema DEVE transicionar para JOGANDO.
3. QUANDO o jogador pressiona ESC, P ou o botão Start do controle durante JOGANDO, O sistema DEVE pausar/despausar o jogo com overlay "Pausado".
4. Os estados válidos DEVEM ser exatamente: PRONTO, JOGANDO, PAUSADO, GAME_OVER, com transições PRONTO→JOGANDO, JOGANDO↔PAUSADO, JOGANDO→GAME_OVER, GAME_OVER→PRONTO.

## R7 — Apresentação visual (temática Minecraft)

**User story:** Como jogador, quero visual voxel estilo Minecraft, para que a temática seja reconhecível.

### Critérios de aceitação

1. Todos os sprites DEVEM ser gerados por código em estilo pixel-art/voxel (blocos 16×16 escalados), sem uso de assets da Mojang.
2. O pássaro DEVE ser uma abelha voxel (corpo amarelo/listras pretas, asas animadas em 2 frames).
3. O chão DEVE ser uma faixa rolante de blocos do bioma atual, com rolagem sincronizada à velocidade das colunas.
4. ENQUANTO em qualquer estado, O sistema DEVE renderizar decoração de fundo do bioma (Overworld: nuvens e colinas; Cave: estalactites e minérios; Nether: lava e fortaleza) com parallax.
5. Os textos DEVEM usar fonte estilo pixelada com sombra dura, imitando a UI do Minecraft.
6. A renderização de texto NÃO DEVE depender de fontes instaladas no sistema operacional — o resultado DEVE ser idêntico em desktop e Android (que não possui as fontes usadas na v1).

## R8 — Áudio

**User story:** Como jogador, quero sons de feedback, para que as ações tenham resposta audível.

### Critérios de aceitação

1. QUANDO o pássaro voa, pontua, colide ou muda de bioma, O sistema DEVE tocar o som correspondente (flap, XP orb, dano/bloco quebrando, portal).
2. Todos os sons DEVEM ser sintetizados por código (ondas quadradas/ruído, estilo 8-bit) — sem arquivos de áudio externos.
3. QUANDO o jogador pressiona M, O sistema DEVE alternar mudo/som.
4. SE o dispositivo de áudio não estiver disponível, O sistema DEVE continuar funcionando sem som (degradação graciosa).

## R9 — Requisitos não funcionais

1. O jogo DEVE rodar a 60 FPS fixos, com resolução **lógica** de 480×720 escalada para a resolução real da tela mantendo a proporção (letterbox/pillarbox) — na v1 o letterbox estava fora de escopo; na v2 é obrigatório (ver R14.3).
2. O jogo DEVE depender apenas de Python ≥ 3.10 e `pygame-ce` ≥ 2.5 (mais stdlib) em tempo de execução. `pygame-ce` substitui o `pygame` usado na v1 por ser o pacote com suporte a Android na cadeia de build escolhida (R17) e ser compatível a nível de API.
3. O projeto DEVE ser gerenciado com a ferramenta `uv` (instalada localmente): dependências declaradas em `pyproject.toml`, ambiente criado via `uv sync` e jogo iniciado com `uv run main.py` a partir da raiz do projeto.
4. A física DEVE ser determinística por frame (timestep fixo via clock do Pygame).
5. O jogo DEVE manter 60 FPS em aparelho Android de entrada (referência: 4 núcleos, Android 8, sem GPU dedicada), medido pelo tempo de frame de `update` + `draw`.

## R10 — Controle de Xbox

**User story:** Como jogador, quero jogar com controle de Xbox, para ter alternativa ao teclado/mouse.

### Critérios de aceitação

1. QUANDO o jogo inicia, O sistema DEVE detectar controles conectados via `pygame.joystick` e inicializá-los.
2. QUANDO um controle é conectado ou desconectado durante o jogo (hotplug), O sistema DEVE tratar o evento sem travar e atualizar a lista de controles ativos.
3. Os mapeamentos DEVEM ser: botão A → voar/reiniciar, Start → pausar/despausar, botão Y → mudo, equivalentes às teclas de teclado.
4. Teclado, mouse e controle DEVEM funcionar simultaneamente, sem necessidade de seleção de dispositivo.
5. SE nenhum controle estiver conectado, O sistema DEVE funcionar normalmente com teclado/mouse.

## R11 — Créditos

**User story:** Como criador do jogo, quero que meu nome e do meu parceiro apareçam no jogo, para receber crédito pela autoria.

### Critérios de aceitação

1. QUANDO o jogo exibe o estado PRONTO, O sistema DEVE exibir os nomes dos criadores ("Douglas e Pedro") abaixo do título.
2. O título da janela (barra de título/taskbar) DEVE incluir os nomes dos criadores.

## R12 — Recorde na tela inicial

**User story:** Como jogador, quero ver meu recorde atual assim que abro o jogo, para me sentir motivado a superá-lo.

### Critérios de aceitação

1. QUANDO o jogo exibe o estado PRONTO, O sistema DEVE exibir o recorde atual em destaque no rodapé da tela, acima do chão.
2. SE não houver recorde registrado, O sistema DEVE exibir "RECORDE: 0".

## R13 — Distribuição e empacotamento

**User story:** Como jogador sem Python instalado, quero baixar um executável e simplesmente dar duplo clique para jogar, sem precisar instalar nada.

### Critérios de aceitação

1. O projeto DEVE poder ser empacotado em um executável standalone (Windows e Linux) via PyInstaller, sem exigir Python ou `uv` na máquina de destino.
2. QUANDO uma Release é publicada no GitHub com uma tag de versão, O sistema de CI DEVE gerar automaticamente os executáveis de Windows e Linux e anexá-los como assets da release, comprimidos como `.zip` (Windows) e `.tar.bz2` (Linux).
3. A mesma Release DEVE também publicar o APK de Android (ver R17), totalizando três assets por release.

## R14 — Compatibilidade com Android (celular e TV)

**User story:** Como jogador, quero jogar no meu celular e na minha Android TV, para não depender de um PC.

### Critérios de aceitação

1. O jogo DEVE rodar em Android 5.0 (API 21) ou superior, em celulares, tablets e Android TV.
2. O APK DEVE conter as ABIs `armeabi-v7a`, `arm64-v8a` e `x86_64`, para cobrir aparelhos antigos, atuais e ambientes x86 (emuladores, Chromebooks, TV boxes Intel).
3. QUANDO o jogo inicia em qualquer tela, O sistema DEVE preencher a tela escalando a resolução lógica 480×720 proporcionalmente, sem distorcer a imagem, adicionando barras (letterbox no topo/base, pillarbox nas laterais) conforme a proporção do aparelho — inclusive em Android TV 16:9 paisagem.
4. O jogo DEVE ser inteiramente jogável sem tela de toque (Android TV, operado por controle remoto/D-pad ou gamepad), e DEVE declarar a tela de toque como recurso não obrigatório.
5. O jogo NÃO DEVE depender de fontes, arquivos ou recursos do sistema operacional que não existam no Android (ver R7.6).
6. SE o aparelho não tiver saída de áudio disponível, O sistema DEVE continuar funcionando sem som (já coberto por R8.4, reafirmado para Android).

## R15 — Entrada por toque e teclas do Android

**User story:** Como jogador de celular, quero comandar o jogo tocando na tela, e quero que os botões do aparelho façam o esperado.

### Critérios de aceitação

1. QUANDO o jogador toca em qualquer ponto da área de jogo, O sistema DEVE executar a ação de voar/iniciar/reiniciar — equivalente a ESPAÇO (R1.1, R3.4, R6.2).
2. QUANDO o jogador aciona o botão BACK do Android durante JOGANDO, O sistema DEVE pausar o jogo (em vez de encerrar o app).
3. QUANDO o jogador aciona o botão BACK do Android em PRONTO, PAUSADO ou GAME_OVER, O sistema DEVE encerrar o jogo.
4. O sistema DEVE oferecer forma de alternar mudo sem teclado físico: um controle de mudo tocável na tela (celular) e, em aparelhos sem toque, uma ação alcançável por D-pad na tela de PAUSADO (Android TV), além do botão Y do gamepad já previsto em R10.3.
5. Toque, teclado, mouse e controle DEVEM continuar funcionando simultaneamente, sem seleção de dispositivo (extensão de R10.4).

## R16 — Ciclo de vida do aplicativo Android

**User story:** Como jogador de celular, quero que o jogo não me prejudique quando eu receber uma ligação ou trocar de app.

### Critérios de aceitação

1. QUANDO o app vai para segundo plano durante JOGANDO, O sistema DEVE transicionar automaticamente para PAUSADO.
2. QUANDO o app retorna ao primeiro plano, O sistema DEVE permanecer em PAUSADO, aguardando comando explícito do jogador para retomar.
3. O recorde DEVE ser persistido conforme R4.5 (armazenamento privado do app no Android).
4. QUANDO o sistema operacional encerra o app sem aviso, o recorde já alcançado DEVE ser preservado (garantido pela gravação incremental de R4.3).

## R17 — Empacotamento Android (APK)

**User story:** Como jogador, quero baixar um APK e instalar direto, sem loja de aplicativos e sem descompactar nada.

### Critérios de aceitação

1. O projeto DEVE poder ser empacotado como APK via Buildozer/python-for-android, assinado com chave de debug — suficiente para instalação direta ao permitir "fontes desconhecidas".
2. QUANDO uma Release é publicada no GitHub com tag de versão, O sistema de CI DEVE gerar o APK e anexá-lo como asset da release **sem compressão** (arquivo `.apk` puro, `BlockyBird-<tag>.apk`), pronto para download e instalação direta.
3. O APK DEVE declarar suporte a Android TV (categoria de launcher leanback e banner de 320×180) para ser reconhecido e iniciável na interface de TV.
4. O manifesto DEVE permitir as orientações necessárias para funcionar tanto em celular (retrato) quanto em Android TV (paisagem fixa por hardware).

## R18 — Conformidade com Ruff

**User story:** Como mantenedor, quero que todo o código Python do projeto siga um padrão de lint e formatação verificado por ferramenta, para reduzir bugs bobos e manter o estilo consistente conforme o projeto cresce.

### Critérios de aceitação

1. O projeto DEVE declarar `ruff` como dependência de desenvolvimento em `pyproject.toml` (grupo `dev`), com versão mínima fixada.
2. O projeto DEVE ter configuração explícita de `ruff` (seção `[tool.ruff]` em `pyproject.toml`) definindo o conjunto de regras de lint habilitado e o comprimento de linha.
3. QUANDO `uv run ruff check .` é executado a partir da raiz do projeto, O sistema DEVE reportar zero violações sobre todo o código Python versionado (`src/`, `tests/`, `main.py`, `scripts/`, receitas locais em `p4a-recipes/`).
4. QUANDO `uv run ruff format --check .` é executado, O sistema DEVE reportar que nenhum arquivo precisa de reformatação.
5. O pipeline de CI (GitHub Actions) DEVE rodar `ruff check` e `ruff format --check` em cada push/pull request, falhando o job SE houver qualquer violação — para que uma regressão de lint não seja mesclada sem ser notada.
6. Violações encontradas na auditoria inicial DEVEM ser corrigidas no código (não silenciadas com `# noqa` genérico); supressões pontuais DEVEM ser justificadas com um comentário curto quando a regra não se aplicar ao caso.

## R19 — Tamanho de fonte sem sobreposição

**User story:** Como jogador, quero que todos os textos do jogo sejam legíveis e não se sobreponham entre si nem com outros elementos de UI, em qualquer tela do jogo.

### Critérios de aceitação

1. Em cada tela do jogo (PRONTO, HUD durante JOGANDO, PAUSADO, GAME_OVER), os retângulos ocupados por textos renderizados NÃO DEVEM se sobrepor entre si, nem com o chão, nem com o ícone de mudo (R15.4).
2. Todo texto renderizado DEVE caber inteiramente dentro dos limites da resolução lógica (480×720), com uma margem mínima de 20 px nas laterais e sem ultrapassar o topo ou a área do chão.
3. O espaçamento vertical entre linhas de texto de uma mesma tela DEVE ser calculado a partir da altura real do texto renderizado no tamanho escolhido (não um deslocamento fixo em pixels independente do tamanho da fonte), para que o layout continue correto se o tamanho for ajustado no futuro.
4. Cada papel de texto (título, subtítulo/créditos, instrução, HUD de pontuação, overlay de pausa, textos de game over, recorde) DEVE ter um tamanho definido que priorize legibilidade sem violar os critérios 1–2 — o levantamento do tamanho ideal por papel é parte da implementação desta versão.
5. A verificação de não sobreposição DEVE ser automatizada (teste que renderiza cada tela e compara os retângulos dos textos), para não depender de inspeção visual manual a cada mudança futura de texto ou fonte.

---

## Fora de escopo

Multiplayer, skins alternativas, música de fundo contínua, menus de configuração, salvamento em nuvem, publicação na Google Play Store (o APK é para instalação direta; assinatura de release com keystore próprio fica para uma versão futura), suporte a iOS.
