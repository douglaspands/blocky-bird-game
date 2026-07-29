# Requisitos — Blocky Bird (Flappy Bird com temática Minecraft)

## Introdução

Blocky Bird é um clone de Flappy Bird em Python/Pygame com temática Minecraft. O jogador controla uma abelha voxel que voa entre colunas de blocos, com progressão de biomas (Overworld → Cave → Nether), efeitos sonoros e partículas de blocos. Todos os gráficos e sons são gerados por código — sem assets externos ou material protegido da Mojang.

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
3. QUANDO a partida termina com pontuação maior que o recorde, O sistema DEVE atualizar o recorde e persisti-lo em arquivo local (`highscore.json`).
4. QUANDO o jogo inicia, O sistema DEVE carregar o recorde do arquivo local; SE o arquivo não existir ou estiver corrompido, O sistema DEVE assumir recorde 0.

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

## R8 — Áudio

**User story:** Como jogador, quero sons de feedback, para que as ações tenham resposta audível.

### Critérios de aceitação

1. QUANDO o pássaro voa, pontua, colide ou muda de bioma, O sistema DEVE tocar o som correspondente (flap, XP orb, dano/bloco quebrando, portal).
2. Todos os sons DEVEM ser sintetizados por código (ondas quadradas/ruído, estilo 8-bit) — sem arquivos de áudio externos.
3. QUANDO o jogador pressiona M, O sistema DEVE alternar mudo/som.
4. SE o dispositivo de áudio não estiver disponível, O sistema DEVE continuar funcionando sem som (degradação graciosa).

## R9 — Requisitos não funcionais

1. O jogo DEVE rodar a 60 FPS fixos em resolução 480×720 (janela redimensionável com letterbox opcional fora de escopo).
2. O jogo DEVE depender apenas de Python ≥ 3.10 e `pygame` ≥ 2.5 (mais stdlib).
3. O projeto DEVE ser gerenciado com a ferramenta `uv` (instalada localmente): dependências declaradas em `pyproject.toml`, ambiente criado via `uv sync` e jogo iniciado com `uv run main.py` a partir da raiz do projeto.
4. A física DEVE ser determinística por frame (timestep fixo via clock do Pygame).

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

---

## Fora de escopo

Multiplayer, mobile/touch, skins alternativas, música de fundo contínua, menus de configuração, salvamento em nuvem.
