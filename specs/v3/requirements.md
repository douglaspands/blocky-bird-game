# Requisitos — Blocky Bee (Flappy Bird com temática Minecraft)

## Introdução

Blocky Bee é um clone de Flappy Bird em Python/Pygame com temática Minecraft. O jogador controla uma abelha voxel que voa entre colunas de blocos, com progressão de biomas (Overworld → Cave → Nether), efeitos sonoros e partículas de blocos. Todos os gráficos e sons são gerados por código — sem assets externos ou material protegido da Mojang.

**Escopo da v3:** além de tudo que a v1 e a v2 entregaram (jogo completo para desktop e para Android, ver `specs/v1/` e `specs/v2/`), a v3 ataca seis frentes. (1) **Identidade:** o jogo passa a se chamar **Blocky Bee** — o personagem sempre foi uma abelha, e o nome antigo ("Bird") era herança do gênero, não do jogo. (2) **Aproveitamento de tela:** a barra preta que sobrava em todo aparelho — nos quatro lados no Android, nas laterais num monitor maximizado — é eliminada em todos os sistemas operacionais, sem cortar a cena e **sem alterar a dificuldade**: a área jogável continua sendo exatamente a mesma coluna de 480×720 de mundo, e o espaço que sobra vira faixa decorativa com temática Minecraft (céu estendido, terra mais funda, corte transversal do subsolo e mobs que não interagem com o jogo). A tela inteira também passa a valer como superfície de entrada: tocar sobre a faixa decorativa faz o pássaro voar como se o toque tivesse caído na área jogável, para que nenhuma parte da tela do celular seja zona morta. (3) **Desempenho:** o jogo passa a ser renderizado com aceleração por GPU por padrão, com todo o conteúdo estático pré-renderizado, pressão de coletor de lixo reduzida e taxa de quadros independente do aparelho — o Android da v2 sofria com queda de FPS e com física em câmera lenta quando não sustentava 60 FPS. (4) **Documentação:** toda classe e função pública passa a ter docstring obrigatória, verificada em CI, e o projeto ganha um site de documentação que publica a API junto com os documentos de spec. (5) **Rigor de SDD:** matriz de rastreabilidade ligando cada critério de aceitação ao design, à tarefa e ao teste que o prova, verificada por teste automatizado, mais cobertura mínima no CI, e um README que explica a motivação do projeto e o método. (6) **Boas práticas de Git e GitHub:** as convenções de branch, commit e tag já em uso informalmente passam a estar documentadas, com `LICENSE`, hooks de pre-commit espelhando o gate de CI, Dependabot e demais itens de higiene esperados de um projeto Python público. O desktop continua suportado; nenhum requisito da v1 ou da v2 é removido.

**Escopo da v2 (mantido):** além de tudo que a v1 entregou (jogo completo para desktop, ver `specs/v1/`), a v2 torna o jogo jogável em Android — celular/tablet, sempre em orientação retrato — no maior número possível de aparelhos, distribuído como APK instalável diretamente. Inclui também itens de qualidade e apresentação que não mudam o gameplay, adicionados como aumento de escopo após a entrega Android: (1) todo o código Python do projeto passa a ser verificado pela ferramenta `ruff` (lint + formatação), com conformidade obrigatória e checada em CI; (2) calibração do tamanho da fonte bitmap própria (R7.6), que estava grande demais em várias telas a ponto de textos se sobreporem entre si ou com outros elementos de UI; (3) um ícone do aplicativo com a personagem do jogo (a abelha voxel, R7.2), gerado por código, para a janela/executável do desktop e para o launcher do Android — incluindo o formato de **ícone adaptativo** exigido desde o Android 8.0 (API 26), para que a abelha não fique cortada nem distorcida pelas diferentes máscaras de ícone dos fabricantes (círculo, "squircle", quadrado arredondado). O desktop continua suportado; nenhum requisito da v1 é removido.

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
6. A detecção de colisão DEVE exigir uma sobreposição mínima nos dois eixos (não só encostar) antes de contar como colisão, para tolerar um resvalar raso no canto de uma coluna ou do chão.

## R4 — Pontuação

**User story:** Como jogador, quero acumular pontos e ver meu recorde, para medir meu progresso.

### Critérios de aceitação

1. QUANDO o pássaro ultrapassa completamente uma coluna, O sistema DEVE incrementar a pontuação em 1 ponto e tocar o som de ponto (estilo XP orb).
2. ENQUANTO o jogo está em estado JOGANDO, O sistema DEVE exibir a pontuação atual no topo da tela em fonte pixelada.
3. QUANDO a pontuação da partida em curso supera o recorde, O sistema DEVE atualizar o recorde e persisti-lo em arquivo local (`highscore.json`) — sem esperar o fim da partida, para que o recorde sobreviva ao encerramento abrupto do app pelo sistema operacional (comum em Android).
4. QUANDO o jogo inicia, O sistema DEVE carregar o recorde do arquivo local; SE o arquivo não existir ou estiver corrompido, O sistema DEVE assumir recorde 0.
5. O arquivo de recorde DEVE ser gravado em diretório com permissão de escrita garantida na plataforma (em Android, o armazenamento privado do app; no desktop rodando a partir do código-fonte, a raiz do projeto; no executável empacotado — Windows/Linux via PyInstaller, R13 —, a pasta onde o executável está, nunca o diretório temporário de extração), nunca dependendo do diretório de trabalho corrente.

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

1. O jogo DEVE rodar a 60 FPS fixos, com resolução **lógica** fixa de 480×720; a tela real pode ter qualquer proporção, preenchida por `pygame.SCALED` sem distorcer nem cortar a imagem — o excedente de um dos eixos vira barra (letterbox), nunca sobrando nas laterais graças à orientação travada em retrato (ver R14.3, R14.4).
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

## R14 — Compatibilidade com Android (celular e tablet, sempre em retrato)

**User story:** Como jogador, quero jogar no meu celular, para não depender de um PC.

### Critérios de aceitação

1. O jogo DEVE rodar em Android 5.0 (API 21) ou superior, em celulares e tablets, sempre em orientação retrato.
2. O APK DEVE conter as ABIs `armeabi-v7a`, `arm64-v8a` e `x86_64`, para cobrir aparelhos antigos, atuais e ambientes x86 (emuladores, Chromebooks).
3. QUANDO o jogo inicia em qualquer aparelho, O sistema DEVE preencher a tela real sem distorcer a imagem, sem cortar UI e **sem cortar nenhuma parte da imagem renderizada**; barra (letterbox) no topo/base é aceitável. A resolução lógica DEVE continuar fixa em 480×720 em qualquer aparelho (a mesma calibração de dificuldade da task 12, nunca mudando com a tela). Com a orientação sempre travada em retrato (critério 4), a tela real nunca fica mais larga, relativamente, que a base 2:3 — a barra que sobra é sempre letterbox, nunca pillarbox (ver design.md seção 20.1).
4. O manifesto do APK DEVE travar a orientação em retrato (`orientation = portrait` no `buildozer.spec`) — o jogo NUNCA DEVE rodar em paisagem no Android, mesmo que o aparelho seja fisicamente girado.
5. O jogo NÃO DEVE depender de fontes, arquivos ou recursos do sistema operacional que não existam no Android (ver R7.6).
6. SE o aparelho não tiver saída de áudio disponível, O sistema DEVE continuar funcionando sem som (já coberto por R8.4, reafirmado para Android).

## R15 — Entrada por toque e teclas do Android

**User story:** Como jogador de celular, quero comandar o jogo tocando na tela, e quero que os botões do aparelho façam o esperado.

### Critérios de aceitação

1. QUANDO o jogador toca em qualquer ponto da tela — área jogável ou faixa decorativa (R34.1) —, O sistema DEVE executar a ação de voar/iniciar/reiniciar — equivalente a ESPAÇO (R1.1, R3.4, R6.2).
2. QUANDO o jogador aciona o botão BACK do Android durante JOGANDO, O sistema DEVE pausar o jogo (em vez de encerrar o app).
3. QUANDO o jogador aciona o botão BACK do Android em PRONTO, PAUSADO ou GAME_OVER, O sistema DEVE encerrar o jogo.
4. O sistema DEVE oferecer forma de alternar mudo sem teclado físico: um controle de mudo tocável na tela (celular), além do botão Y do gamepad já previsto em R10.3.
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
2. QUANDO uma Release é publicada no GitHub com tag de versão, O sistema de CI DEVE gerar o APK e anexá-lo como asset da release **sem compressão** (arquivo `.apk` puro, `BlockyBee-<tag>.apk`), pronto para download e instalação direta.
3. O manifesto DEVE travar o app em orientação retrato (ver R14.4).

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

## R20 — Conformidade com ty (checagem de tipos)

**User story:** Como mantenedor, quero que o código do jogo seja verificado por um checador de tipos estático, para detectar incompatibilidades de tipo (ex.: o bug de `tuple[int, ...]` vs. `tuple[int, int, int]` encontrado na auditoria inicial) antes que virem bug em produção.

### Critérios de aceitação

1. O projeto DEVE declarar `ty` (Astral) como dependência de desenvolvimento em `pyproject.toml` (grupo `dev`), com versão mínima fixada.
2. O projeto DEVE ter configuração explícita de `ty` (`[tool.ty.environment]`/`[tool.ty.src]` em `pyproject.toml`) definindo a versão-alvo do Python e os caminhos excluídos da checagem.
3. QUANDO `uv run ty check .` é executado a partir da raiz do projeto, O sistema DEVE reportar zero diagnósticos sobre o código do jogo (`src/`, `tests/`, `main.py`, `scripts/`).
4. Módulos que só existem em tempo de execução em uma plataforma específica (ex.: `android.storage`, disponível apenas dentro do runtime python-for-android) e código de teste que monkeypatcha atributos dinâmicos em objetos NÃO DEVEM ser tratados como violação — DEVEM ser suprimidos pontualmente com `# ty: ignore[regra]` e um comentário curto explicando o motivo, nunca com uma supressão genérica.
5. Receitas locais de build Android (`p4a-recipes/`) DEVEM ficar fora do escopo da checagem de tipos — elas importam módulos (`sh`, `pythonforandroid.*`) que só existem dentro da imagem Docker do buildozer (R17), nunca no ambiente de desenvolvimento local.
6. O pipeline de CI (GitHub Actions) DEVE rodar `ty check` em cada push/pull request, falhando o job SE houver qualquer diagnóstico de erro — para que uma regressão de tipo não seja mesclada sem ser notada.
7. Violações reais encontradas na auditoria inicial DEVEM ser corrigidas no código (não suprimidas) sempre que a causa for um tipo genuinamente incompatível, não uma limitação do ambiente de checagem.

---

## R21 — Ícone do aplicativo

**User story:** Como jogador, quero reconhecer o Blocky Bee pelo ícone na área de trabalho, na barra de tarefas e na tela inicial do Android, para identificar e abrir o jogo rapidamente entre os outros aplicativos instalados.

### Critérios de aceitação

1. O ícone do aplicativo DEVE ter a abelha voxel do jogo (R7.2, `textures.make_bee`) como elemento central reconhecível, gerado por código a partir das mesmas texturas/paletas do jogo — sem imagem externa nem material de terceiros (R7.1).
2. No desktop, a janela do jogo (barra de título/taskbar) DEVE exibir o ícone da abelha em vez do ícone padrão do pygame, tanto rodando via `uv run main.py` quanto no executável empacotado (R13.1).
3. O executável Windows gerado por PyInstaller (`BlockyBee.spec`, R13.1) DEVE embutir o ícone da abelha como ícone do arquivo `.exe`, visível no Explorer e na barra de tarefas antes mesmo de o jogo abrir.
4. O APK Android (R17) DEVE declarar o ícone da abelha como ícone do launcher em formato de **ícone adaptativo** (camadas de primeiro plano e de fundo separadas), para que o sistema componha a forma final (círculo, "squircle", quadrado arredondado etc.) sem cortar nem distorcer a personagem, em qualquer aparelho Android 8.0+ (API 26+).
5. Na camada de primeiro plano do ícone adaptativo, a abelha DEVE ficar inteiramente dentro da zona seguro-de-máscara (os 66 dp centrais de um canvas de 108 dp, ~61% da área), para não ser cortada por nenhuma máscara padrão do sistema — este é o comportamento concreto por trás de "aparecer com as proporções ajustadas".
6. O APK Android TAMBÉM DEVE declarar um ícone legado (não adaptativo) equivalente, para aparelhos com Android anterior à 8.0 (API < 26), que não suportam ícone adaptativo.
7. A geração de todas as variações/resoluções do ícone (desktop `.ico`, ícone legado do Android, camadas adaptativas de primeiro plano/fundo) DEVE ser reprodutível por um script versionado no repositório — sem edição manual de imagem fora do controle de versão (`scripts/generate_app_icon.py`).

---

## R22 — Identidade do aplicativo

**User story:** Como jogador, quero que o jogo se chame Blocky Bee, para que o nome corresponda ao personagem que eu de fato controlo — uma abelha, não um pássaro.

### Critérios de aceitação

1. O nome exibido do jogo DEVE ser "Blocky Bee" no título da janela do desktop, na tela inicial (R6.1), no nome do executável empacotado (R13.1), no título do aplicativo Android (R17) e nos nomes dos artefatos publicados em Release (R13.3).
2. O identificador do aplicativo Android (`package.name`) DEVE ser `blockybee`, mantendo o domínio `com.douglaspands`.
3. O sistema NÃO DEVE tentar migrar o recorde do identificador anterior (`blockybee`): o armazenamento privado de um aplicativo Android não é legível por outro, então uma instalação nova começa com recorde 0 — comportamento já coberto por R4.4.
4. As pastas de spec de versões anteriores (`specs/v1/`, `specs/v2/`) NÃO DEVEM ser renomeadas nem reescritas: elas registram o estado do projeto quando o nome ainda era "Blocky Bee", e reescrevê-las falsificaria o histórico.

---

## R23 — Aproveitamento de tela e orientação

**User story:** Como jogador, quero que o jogo ocupe a tela inteira do meu aparelho, para não jogar numa janelinha cercada de barras pretas.

### Critérios de aceitação

1. QUANDO o jogo é executado em qualquer sistema operacional suportado, O sistema NÃO DEVE exibir barra preta em nenhuma borda da tela ou da janela.
2. O sistema NÃO DEVE cortar nenhuma parte da cena para preencher a tela — o preenchimento DEVE vir de conteúdo desenhado, nunca de zoom com recorte.
3. QUANDO o jogo é executado em Android, O sistema DEVE criar o display em modo de tela cheia, usando a resolução nativa do aparelho.
4. QUANDO a proporção da tela ou da janela difere da proporção da área jogável, O sistema DEVE calcular um canvas lógico com a proporção real e posicionar a área jogável dentro dele, destinando o espaço restante às faixas decorativas de R25.
5. ENQUANTO o jogo roda em Android, O sistema DEVE permanecer em orientação retrato, sem girar quando o aparelho é virado.
6. QUANDO a janela do desktop é redimensionada, O sistema DEVE recalcular o canvas lógico e as faixas decorativas, mantendo a área jogável inalterada.
7. A janela padrão do desktop DEVE abrir numa proporção mais larga que a da área jogável, para que as faixas decorativas laterais fiquem visíveis sem o jogador precisar redimensionar nada.

---

## R24 — Preservação da dificuldade

**User story:** Como jogador, quero que o desafio seja o mesmo em qualquer aparelho, para que meu recorde signifique a mesma coisa no celular e no computador.

### Critérios de aceitação

1. A área jogável DEVE ter sempre as mesmas dimensões de mundo (480×720), independentemente da proporção da tela ou da janela.
2. O sistema NÃO DEVE alterar tamanho de bloco, tamanho da abelha, tamanho da abertura entre colunas, espaçamento horizontal entre colunas, gravidade, impulso de voo nem velocidade de queda em função da proporção da tela.
3. QUANDO uma coluna é gerada, O sistema DEVE posicioná-la na borda direita da área jogável, para que o tempo entre o surgimento da coluna e a chegada dela ao pássaro seja idêntico em qualquer proporção de tela.
4. O sistema NÃO DEVE exibir colunas na faixa decorativa antes de elas entrarem na área jogável — o jogador NÃO DEVE enxergar um obstáculo mais cedo em uma tela mais larga.
5. O teto e o chão que limitam o voo DEVEM ficar nas bordas da área jogável, não nas bordas do canvas — a faixa decorativa NÃO DEVE aumentar o espaço vertical disponível para voar.

---

## R25 — Faixas decorativas e ambientação

**User story:** Como jogador, quero que o espaço fora da área de jogo tenha cenário do universo Minecraft, para que a tela inteira faça parte do jogo em vez de ser moldura vazia.

### Critérios de aceitação

1. QUANDO sobra espaço vertical (tela mais alongada que a área jogável), O sistema DEVE dar prioridade ao chão: a parte de cima recebe céu do bioma atual limitado a um teto pequeno (2 fileiras de bloco), e a parte de baixo recebe o restante da sobra como fileiras adicionais de bloco de chão — o chão é uma faixa tileável sem gradiente nem parallax, e por isso mais barata de desenhar numa tela muito alongada (R27, task 80).
2. QUANDO sobra espaço horizontal (tela mais larga que a área jogável), O sistema DEVE preencher cada lateral com um corte transversal do subsolo do bioma atual — camadas de bloco empilhadas com veios de minério.
3. O sistema DEVE exibir mobs decorativos do universo Minecraft nas faixas, com pelo menos três variedades por bioma, todos gerados por código a partir das mesmas paletas do jogo (R7.1), sem imagem externa nem material de terceiros.
4. Os mobs e o conteúdo das faixas NÃO DEVEM colidir com o pássaro, gerar pontuação, alterar a velocidade do jogo nem influenciar qualquer regra — são exclusivamente decorativos.
5. O céu, as camadas de parallax (R7.4) e o chão DEVEM ser desenhados na largura inteira do canvas, para que a cena seja contínua de uma borda à outra.
6. QUANDO o jogador toca ou clica sobre uma faixa decorativa, O sistema DEVE tratar a entrada como se ela tivesse ocorrido na área jogável (R34.1), salvo quando o ponto cair sobre um controle de interface ali posicionado (R15.4).
7. QUANDO existe faixa de céu acima da área jogável, O sistema DEVE posicionar a pontuação do HUD e o botão de mudo nela, liberando a área de jogo.

---

## R26 — Aceleração por GPU com compatibilidade

**User story:** Como jogador de celular, quero que o jogo use a placa gráfica do aparelho, para rodar liso mesmo num aparelho modesto.

### Critérios de aceitação

1. O sistema DEVE renderizar com aceleração por GPU por padrão, sem exigir configuração nem opção do jogador.
2. QUANDO o renderizador acelerado não puder ser criado, O sistema DEVE tentar um renderizador escolhido pelo próprio SDL (inclusive por software) antes de desistir da aceleração.
3. QUANDO nenhum renderizador puder ser criado, O sistema DEVE cair para o caminho de renderização por superfície da v2, mantendo o jogo funcional em vez de falhar ao abrir.
4. A camada de desenho DEVE expor a mesma interface para todos os caminhos, de modo que nenhum módulo de jogo precise saber qual está em uso.
5. O sistema DEVE registrar em log e expor à instrumentação (R30) qual caminho de renderização está efetivamente em uso.
6. O sistema DEVE solicitar sincronização vertical ao criar o renderizador acelerado, para não desperdiçar quadros nem produzir rasgo de imagem.
7. O sistema DEVE usar amostragem por vizinho mais próximo na escala final, preservando a nitidez da arte em pixel (R7.1).

---

## R27 — Desempenho

**User story:** Como jogador de celular, quero o jogo fluido do início ao fim da partida, para que a dificuldade venha do desafio e não da lentidão.

### Critérios de aceitação

1. ENQUANTO o jogo está em estado JOGANDO num aparelho Android de referência, O sistema DEVE sustentar 60 quadros por segundo.
2. O sistema DEVE pré-renderizar na inicialização todo conteúdo visual que não muda entre quadros (chão, colunas, camadas de parallax, faixas decorativas, mobs, sprites rotacionados do pássaro, textos), em vez de redesenhá-lo a cada quadro.
3. O sistema NÃO DEVE criar objetos descartáveis a cada quadro no laço principal (superfícies, retângulos, listas ou geradores de números aleatórios) quando o mesmo resultado puder ser reaproveitado.
4. O sistema DEVE converter toda superfície para o formato do display antes de usá-la em desenho.
5. O sistema NÃO DEVE executar escrita em disco durante o quadro enquanto o jogo está em estado JOGANDO; a persistência do recorde (R4.3) DEVE ocorrer no fim da partida ou quando o aplicativo vai para segundo plano (R16.1), preservando a garantia de que o recorde sobrevive ao encerramento abrupto pelo sistema operacional.
6. O sistema DEVE descartar da fila de eventos os tipos que não utiliza, em especial os eventos contínuos de movimento de toque e de mouse.
7. O sistema NÃO DEVE desenhar obstáculos inteiramente fora da área visível.

---

## R28 — Independência de taxa de quadros

**User story:** Como jogador, quero que o jogo corra na mesma velocidade em qualquer aparelho, para que um celular mais fraco deixe a imagem menos fluida, mas nunca o jogo em câmera lenta.

### Critérios de aceitação

1. O sistema DEVE avançar a simulação em passos de tempo fixos, a partir do tempo real decorrido, em vez de um passo por quadro desenhado.
2. QUANDO um quadro demora mais que o passo fixo, O sistema DEVE executar quantos passos de simulação forem necessários para recuperar o tempo decorrido, até um limite máximo de passos por quadro.
3. O sistema NÃO DEVE acelerar o jogo para compensar uma pausa longa (aplicativo em segundo plano, travamento do sistema): o tempo decorrido DEVE ser limitado antes de virar passos de simulação.
4. A física, os temporizadores de animação e a progressão de biomas DEVEM produzir exatamente o mesmo resultado a 60 quadros por segundo que a implementação da v2 produzia.

---

## R29 — Qualidade adaptativa

**User story:** Como jogador de um aparelho antigo, quero que o jogo se ajuste sozinho, para continuar jogável mesmo que o cenário fique mais simples.

### Critérios de aceitação

1. ENQUANTO o jogo está em estado JOGANDO, O sistema DEVE medir a taxa de quadros real ao longo de uma janela de tempo.
2. QUANDO a taxa de quadros medida fica abaixo do alvo, O sistema DEVE reduzir o nível de qualidade visual, desligando primeiro os elementos puramente decorativos.
3. O sistema NÃO DEVE alterar velocidade das colunas, tamanho da abertura, detecção de colisão nem pontuação ao mudar de nível de qualidade.
4. O sistema DEVE aplicar histerese na troca de nível, para não alternar repetidamente entre dois níveis.
5. O sistema DEVE persistir o nível detectado no mesmo diretório gravável do recorde (R4.5) e reaplicá-lo na abertura seguinte.
6. SE o arquivo de nível não existir ou estiver corrompido, O sistema DEVE assumir o nível máximo de qualidade e redetectar.

---

## R30 — Instrumentação de desempenho

**User story:** Como mantenedor, quero medir o desempenho no aparelho e no CI, para provar que uma otimização funcionou em vez de supor.

### Critérios de aceitação

1. O sistema DEVE oferecer uma sobreposição de diagnóstico exibindo taxa de quadros, tempo de atualização, tempo de desenho e caminho de renderização em uso.
2. A sobreposição DEVE ser ativada por variável de ambiente e ficar desligada por padrão, sem custo mensurável quando desligada.
3. O projeto DEVE incluir um script de benchmark executável sem display real, cobrindo os estados PRONTO, JOGANDO (nos três biomas) e GAME_OVER.
4. O benchmark DEVE reportar tempo por quadro e volume de alocação de memória, de forma comparável entre execuções.
5. Os valores medidos antes e depois das otimizações DEVEM ser registrados no documento de design desta versão.

---

## R31 — Documentação

**User story:** Como pessoa que chega ao repositório, quero entender o código sem lê-lo inteiro, para conseguir contribuir ou aprender com ele.

### Critérios de aceitação

1. Todo módulo, classe e função pública do projeto DEVE ter docstring.
2. As docstrings DEVEM seguir uma convenção única, verificada automaticamente.
3. O pipeline de CI DEVE falhar QUANDO houver docstring ausente ou fora da convenção.
4. O projeto DEVE ser capaz de gerar um site de documentação a partir das docstrings do código e dos documentos de spec, no mesmo lugar.
5. As dependências de documentação DEVEM ficar restritas ao grupo de desenvolvimento, sem entrar no aplicativo empacotado.

---

## R32 — Rastreabilidade e cobertura

**User story:** Como estudante de SDD, quero ver a ligação explícita entre requisito, design, tarefa e teste, para entender como a spec governa o código de fato.

### Critérios de aceitação

1. Esta versão DEVE manter uma matriz de rastreabilidade ligando cada critério de aceitação ao trecho de design, à tarefa e ao(s) teste(s) que o comprovam.
2. O projeto DEVE ter um teste automatizado que falha QUANDO um critério de aceitação não aparece na matriz.
3. O projeto DEVE ter um teste automatizado que falha QUANDO a matriz referencia um teste que não existe.
4. O pipeline de CI DEVE medir a cobertura de testes e falhar abaixo de um mínimo declarado.

---

## R33 — Documentação de motivação e método

**User story:** Como pessoa começando em Spec Driven Development, quero entender por que este projeto existe e como reproduzir o método, para aplicar a mesma abordagem no meu projeto.

### Critérios de aceitação

1. O `README.md` DEVE explicar a motivação do projeto: estudar Spec Driven Development na prática e fazer um jogo para o filho do autor, que gosta de jogos e de Minecraft.
2. O `README.md` DEVE explicar o que é Spec Driven Development, ancorando a explicação nos artefatos que o próprio repositório contém.
3. O `README.md` DEVE incluir um prompt de exemplo, pronto para uso, que planejaria e construiria um projeto como este seguindo o método.
4. O prompt de exemplo DEVE combinar a definição de produto (objetivo, público, user stories, critérios de aceitação, fora de escopo) com a definição técnica (stack, ferramental, estrutura, restrições e protocolo de trabalho).
5. O prompt de exemplo DEVE vir acompanhado de explicação sobre o porquê de cada parte, e DEVE ser genérico o bastante para servir de ponto de partida para outros projetos.

---

## R34 — Entrada em toda a área visível

**User story:** Como jogador de celular, quero tocar em qualquer ponto da tela para voar, para não precisar mirar com o polegar na coluna estreita da área jogável.

### Critérios de aceitação

1. QUANDO o jogador toca ou clica em qualquer ponto do canvas — incluindo as faixas decorativas de R25 —, O sistema DEVE executar a ação de voar/iniciar/reiniciar, exceto quando o ponto cair sobre um controle de interface (R15.4).
2. O sistema DEVE aplicar a mesma regra ao toque do Android e ao clique de mouse do desktop, sem ramificação por plataforma (extensão de R15.5).
3. SE o ponto convertido para coordenadas lógicas cair fora do canvas, O sistema DEVE ignorar a entrada.
4. QUANDO o jogo está em PRONTO, PAUSADO ou GAME_OVER, a entrada sobre faixa decorativa DEVE ter o mesmo efeito que teria sobre a área jogável (R6.2, R3.4).
5. O sistema NÃO DEVE, por receber entrada, dar à faixa decorativa qualquer outro papel de jogo — colisão, pontuação e velocidade seguem inalteradas (reafirma R25.4).

---

## R35 — Boas práticas de Git e GitHub

**User story:** Como mantenedor, quero que as convenções de git/GitHub já em uso estejam documentadas e reforçadas por automação, para que um projeto Python continue confiável de contribuir e de lançar mesmo depois de um tempo sem mexer nele.

### Critérios de aceitação

1. O projeto DEVE incluir um arquivo `LICENSE` com uma licença permissiva (MIT), e o `README.md` DEVE referenciá-la, deixando claro que ela cobre o código do projeto, não a marca Minecraft.
2. O `pyproject.toml` DEVE declarar a licença nos metadados do projeto, consistente com o arquivo `LICENSE`.
3. O projeto DEVE ter um `CONTRIBUTING.md` documentando as convenções já em uso: nomes de branch (`main`, `release/vN`, `feature/<slug>`), formato de mensagem de commit (imperativo, citando a task/requisito de `specs/vN/tasks.md`) e formato de tag (`vMAJOR.MINOR.PATCH`, com sufixo `-RCn` opcional).
4. O projeto DEVE ter um `CHANGELOG.md` no formato Keep a Changelog, com uma seção "Não lançado" para a versão em andamento.
5. O repositório DEVE ter hooks de pre-commit que espelham o gate de CI (`ruff check`, `ruff format`, `ty check`) mais checagens básicas de higiene (fim de arquivo sem newline, espaço em branco sobrando, conflito de merge não resolvido, arquivo grande demais, YAML/TOML mal formado, final de linha misto), instaláveis via `uv run pre-commit install`.
6. O CI DEVE rodar os mesmos hooks de pre-commit, para que a checagem valha mesmo sem instalação local.
7. O projeto DEVE ter `.editorconfig` e `.gitattributes` garantindo final de linha consistente (`LF`) entre o desenvolvimento no Windows e o CI no Linux, com os assets binários (`.png`, `.ico`) marcados explicitamente.
8. O repositório DEVE ter Dependabot configurado para abrir PRs de atualização das dependências Python (ecossistema `uv`) e das GitHub Actions usadas nos workflows.
9. Todo workflow em `.github/workflows/` DEVE declarar `permissions` explícitas de menor privilégio, em vez de herdar o padrão do repositório.
10. O projeto DEVE ter um template de Pull Request lembrando do fluxo já documentado em "Sobre este projeto e o método SDD" (task/requisito referenciado, `tasks.md` marcado, gate de CI verde).

---

## R36 — Última pontuação na tela inicial

**User story:** Como jogador, quero ver a pontuação da minha última partida assim que volto à tela inicial, para comparar rapidamente com o recorde.

### Critérios de aceitação

1. QUANDO o jogo exibe o estado PRONTO após pelo menos uma partida ter terminado nesta execução, O sistema DEVE exibir a pontuação dessa última partida acima do recorde, em destaque menor que o recorde.
2. SE o jogo ainda não exibiu nenhum GAME_OVER nesta execução, O sistema NÃO DEVE exibir essa linha.
3. A última pontuação exibida NÃO DEVE ser persistida em disco nem sobreviver ao reinício do aplicativo.

---

## Fora de escopo

Multiplayer, skins alternativas, música de fundo contínua, menus de configuração, salvamento em nuvem, publicação na Google Play Store (o APK é para instalação direta; assinatura de release com keystore próprio fica para uma versão futura), suporte a iOS. Ícone temático/monocromático do Android 13+ ("Material You" themed icons) e imagem de destaque ("feature graphic") de loja de aplicativos ficam fora de escopo — dependem de publicação na Play Store, já fora de escopo. Scaffolding de projeto open-source voltado a múltiplos contribuidores externos — templates de issue, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `CODEOWNERS` — também fica fora: este é um projeto pessoal/pai-e-filho, sem processo formal de triagem de issues de terceiros.
