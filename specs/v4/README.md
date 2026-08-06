# Blocky Bee — Specs v4

**Status:** em andamento.

## Descrição

A v4 acrescenta uma terceira forma de jogar Blocky Bee, sem instalar nada: um único arquivo
`.html` que roda no **Chrome**, desktop ou Android, compilado do mesmo código-fonte em `src/`
já usado pelos builds nativos — via **WebAssembly**, com `pygbag`. Não é uma reescrita: é o
mesmo laço de jogo, a mesma física, os mesmos biomas, a mesma cascata de renderização
acelerada por GPU da v3, agora também compilados para rodar dentro de uma aba de navegador.
Os builds nativos (`.exe` via PyInstaller, `.apk` via Buildozer) continuam existindo e sendo
publicados sem nenhuma mudança.

**Execução assíncrona.** `pygbag` exige que o laço principal ceda o controle ao navegador a
cada quadro (`async def`, `await asyncio.sleep(0)`) — sem isso a aba trava. Essa conversão é
feita uma única vez em `Game.run()`, sem ramo de plataforma: o mesmo laço assíncrono roda
também no desktop e no Android nativos, onde o `await` extra custa uma cessão de controle sem
I/O real.

**Entrada sem mudança de código.** Teclado, mouse e toque continuam passando pelo mesmo
`InputManager` da v1–v3 — a ponte SDL2 do Emscripten mapeia eventos do navegador para os
mesmos tipos de evento já consumidos. O controle Xbox também entra no escopo, reconhecido
pela Gamepad API do Chrome através do mesmo caminho de hotplug já usado nativamente (R10.2),
nunca exigido para chegar à tela inicial.

**Armazenamento sem sistema de arquivos.** Recorde e nível de qualidade passam a usar
`localStorage` do navegador quando rodando como web, com a mesma disciplina de nunca gravar
durante uma partida em andamento (R27.5) e a mesma degradação graciosa de dado ausente ou
corrompido já garantida em desktop/Android.

**Um único arquivo, de verdade.** O build padrão do `pygbag` produz vários arquivos, e por
padrão busca o runtime WebAssembly (CPython + SDL2 + pygame-ce, dezenas de MB) de um CDN de
terceiros a cada carregamento. Um script de pós-processamento (`scripts/build_web.py`) embute
tudo em base64 dentro de um único `.html`, com uma checagem que falha o build se sobrar
qualquer dependência de rede — a garantia não fica só na intenção, fica num teste.

**Distribuição em dois lugares, um só arquivo.** O `.html` único é publicado num link estável
via GitHub Pages — estendendo a implantação que já existe para o site de documentação, não um
workflow paralelo e concorrente — e também anexado como quarto asset de cada Release, ao lado
do `.exe` e do `.apk`.

Mesmo escopo de dispositivo da v3: desktop e Android, via Chrome. iOS continua fora, mesmo
pelo navegador — no iOS todo app de navegador roda sobre o motor WebKit da Apple, não sobre o
Chromium real.

## Conteúdo desta pasta

- [`requirements.md`](requirements.md) — requisitos R1–R41 em formato EARS. R1–R13 são o jogo base (v1); R14–R17 são a entrega Android e R18–R21 os aumentos de escopo da v2; R22–R36 são da v3 (identidade, tela e orientação, GPU, desempenho, timestep, qualidade adaptativa, rastreabilidade, boas práticas de Git/GitHub); **R37–R41 são da v4** (WebAssembly via pygbag, entrada no navegador, armazenamento sem sistema de arquivos, empacotamento em arquivo único, distribuição via GitHub Pages e Release).
- [`design.md`](design.md) — arquitetura técnica. Partes I–V (seções 1–44) cobrem v1–v3; **Parte VI (seções 45–53) é a v4**.
- [`tasks.md`](tasks.md) — plano incremental. Tasks 1–83 são o histórico de v1–v3, todas concluídas; **tasks 84–96 são a v4**.
- [`traceability.md`](traceability.md) — matriz critério → design → task → teste, verificada por `tests/test_traceability.py`. Critérios `R37`–`R41` aparecem com a coluna Testes em branco (task ainda não implementada) ou com o marcador `manual` (só um Chrome real confirma), até as tasks correspondentes serem concluídas.

## O que muda em relação à v3

| Limite na v3 | Resposta na v4 |
|---|---|
| Jogar exige instalar um executável (Windows/Linux) ou um APK (Android) | Um único `.html`, aberto direto no Chrome, sem instalação |
| Laço principal síncrono, incompatível com o modelo de execução do navegador | `Game.run()` assíncrono, cedendo o controle a cada quadro — mesmo código em nativo e web |
| `storage.py` resolve um diretório gravável no sistema de arquivos real | Ramo `is_web()` usa `localStorage` do navegador, mesma API pública e mesma disciplina de gravação |
| Nenhuma forma de compartilhar o jogo por link | Link estável via GitHub Pages, ao lado do site de documentação |

## Riscos e limites conhecidos

- **Maior risco, não resolvido por leitura de código:** se `pygame._sdl2.video.Renderer`
  (o renderer acelerado por GPU que a v3 usa por padrão) de fato constrói com sucesso sob
  Emscripten. A cascata de fallback de três níveis já existente limita o dano — o pior caso é
  cair para o caminho de superfície, não deixar de abrir —, mas só um build real em Chrome
  (task 85) confirma qual nível vence de fato.
- **O runtime do `pygbag` não é pequeno.** Um `.html` verdadeiramente único, sem nenhuma
  dependência de rede depois de carregado, custa perder o cache HTTP separado que o build
  multi-arquivo padrão teria — o runtime inteiro (dezenas de MB) é rebaixado a cada visita à
  URL do GitHub Pages, não só na primeira. Decisão registrada em `design.md` seção 51, com
  medição real na task 90.
- **GitHub Pages já publicava o site de documentação** (`docs.yml`) antes da v4 existir — um
  segundo workflow de deploy concorrente sobrescreveria essa publicação silenciosamente. A v4
  estende o workflow existente em vez de criar um novo (design seção 52).
- **Verificação:** boa parte do que a v4 promete (backend de render vencedor, qualidade de
  áudio, paridade de toque, Gamepad API, ausência de requisição de rede) só um Chrome real
  confirma — sem caminho automatizável no ambiente de desenvolvimento headless que os testes
  já usam (`SDL_VIDEODRIVER=dummy`). `tasks.md` separa isso numa seção própria, "Requer
  verificação manual no Chrome", no mesmo espírito da seção equivalente da v3 para Android.

## Sobre esta versão

Esta pasta é um retrato **completo e autocontido** dos specs da v4 — cobre o jogo inteiro,
não só as mudanças desta versão. A v1, a v2 e a v3 permanecem intactas em
[`specs/v1/`](../v1/), [`specs/v2/`](../v2/) e [`specs/v3/`](../v3/) como histórico. Veja
[`specs/README.md`](../README.md) para o padrão de versionamento.
