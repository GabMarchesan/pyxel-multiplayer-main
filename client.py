# Importação de bibliotecas
import pyxel
import socket
import threading
import json
import time

# Dimensões da janela do jogo
WIDTH, HEIGHT = 200, 140

# Inicializa o Pyxel e carrega a imagem de introdução
pyxel.init(WIDTH, HEIGHT)
pyxel.load("tela_inicial.pyxres")

# Velocidade de movimento do jogador
PLAYER_SPEED = 2

# Configurações do socket para comunicação UDP
addr = ('0.0.0.0', 12345)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Variáveis de estado do jogo e do jogador
x = WIDTH // 2                  # Posição inicial do jogador no eixo X
y = HEIGHT - 16                 # Posição inicial no eixo Y
players = {}                    # Dicionário com os dados de todos os jogadores
player_id = None                # ID do jogador atual
asteroids = []                  # Lista de asteroides ativos no jogo
ready = False                   # Indica se o jogador está pronto
state = "intro"                 # Estado atual do jogo ("intro", "menu", "jogo", etc.)
resource_loaded = False         # Indica se os recursos (sprites, sons) já foram carregados
game_start_time = None          # Tempo de início da partida
countdown_time = 30             # Tempo restante da partida
explosion_sounds_played = set() # Controla sons de explosão para não repetir

# Configuração de dificuldade
dificuldade = 'media'
dificuldades = ['facil', 'media', 'dificil']
eh_host = False                 # Indica se o jogador é o host

# Controle da tela de fim de jogo
last_fim_time = None
show_game_over = False

# Thread para receber dados dos outros jogadores/servidor
def recv_data():
    global players, player_id, asteroids, state
    global game_start_time, countdown_time
    global last_fim_time, show_game_over

    while True:
        try:
            # Recebe e processa dados enviados pelo servidor
            data, _ = sock.recvfrom(4096)
            msg = json.loads(data.decode())
            players = msg['players']
            player_id = msg['your_id']
            asteroids = msg.get('asteroids', [])
            new_state = msg.get('state', 'menu')

            # Lógica para transição de estados e controle de tempo
            if state != "jogo" and new_state == "menu":
                game_start_time = None
            elif state == "jogo" and new_state in ["fim", "vitoria"]:
                game_start_time = None
            elif new_state == "jogo" and game_start_time is None:
                game_start_time = time.time()

            # Exibe "fim" com atraso para mostrar mensagem "Todos morreram!"
            if new_state == "fim":
                if state != "fim":
                    last_fim_time = time.time()
                    show_game_over = False
                elif last_fim_time and time.time() - last_fim_time >= 1:
                    show_game_over = True
            else:
                last_fim_time = None
                show_game_over = False

            state = new_state

            # Atualiza contador regressivo
            if game_start_time:
                elapsed_time = time.time() - game_start_time
                countdown_time = max(0, 30 - int(elapsed_time))
        except:
            pass

# Inicia a thread de recepção de dados
threading.Thread(target=recv_data, daemon=True).start()

# Envia dados do jogador para o servidor
def send_data():
    # Se explodiu e ainda está no estado "jogo", não envia mais nada
    if players.get(player_id, {}).get('exploded') and state == "jogo":
        return

    msg = {'x': x, 'y': y, 'ready': ready}
    if pyxel.btnp(pyxel.KEY_RETURN):
        msg['start'] = True
    if eh_host:
        msg['dificuldade'] = dificuldade
    sock.sendto(json.dumps(msg).encode(), addr)

# Função de atualização do jogo (executada a cada frame)
def update():
    global x, y, ready, dificuldade, eh_host, state, resource_loaded

    # Tela de introdução
    if state == "intro":
        if pyxel.btnp(pyxel.KEY_RETURN):
            pyxel.load("my_resource.pyxres")
            pyxel.playm(0, loop=True)  # Toca a música do módulo 0 em loop
            state = "menu"
            resource_loaded = True
        return

    me = players.get(player_id)

    # Verifica se o jogador atual é o host
    if player_id == get_host_id():
        eh_host = True

    # Se o host está no menu, pode mudar a dificuldade
    if state == "menu" and eh_host:
        if pyxel.btnp(pyxel.KEY_1):
            dificuldade = 'facil'
        elif pyxel.btnp(pyxel.KEY_2):
            dificuldade = 'media'
        elif pyxel.btnp(pyxel.KEY_3):
            dificuldade = 'dificil'

    # Lógica de movimentação durante o jogo
    if state == "jogo" and me:
        if me.get('exploded'):
            send_data()
            return
        if pyxel.btn(pyxel.KEY_LEFT):
            x -= PLAYER_SPEED
        if pyxel.btn(pyxel.KEY_RIGHT):
            x += PLAYER_SPEED
        x = max(0, min(WIDTH - 8, x))

    # Alterna estado de "pronto" fora do jogo
    if state != "jogo":
        if pyxel.btnp(pyxel.KEY_SPACE):
            ready = not ready
        send_data()
        return

    send_data()

# Desenha a explosão animada dos jogadores
def draw_explosion(x, y, exp_frame, py_time, offset_y=0):
    t = py_time - exp_frame
    if t < 30:
        if (x, y, exp_frame) not in explosion_sounds_played:
            pyxel.play(0, 0)
            explosion_sounds_played.add((x, y, exp_frame))

        # Desenha círculos com cores diferentes conforme o tempo
        if t < 10:
            color = 10
            radius = 3 + t // 3
        elif t < 20:
            color = 9
            radius = 6 + (t - 10) // 2
        else:
            color = 8
            radius = 9 + (t - 20) // 2
        pyxel.circ(x + 4, y + 4 + offset_y, radius, color)

# Retorna o ID do host (primeiro da lista ordenada)
def get_host_id():
    return sorted(players.keys())[0] if players else None

# Função de renderização (desenho na tela)
def draw():
    global ready
    pyxel.cls(0)  # Limpa a tela
    py_time = int(time.time() * 30)

    # Tela de introdução com imagem
    if state == "intro":
        pyxel.blt(0, 0, 0, 0, 0, 200, 140)
        return

    # Tela de menu com lista de jogadores e dificuldade
    if state == "menu":
        pyxel.blt(0, 0, 0, 0, 96, 200, 140)
        total = len(players)
        prontos = sum(1 for p in players.values() if p.get("ready"))

        pyxel.text(58, 47, f"Players prontos: {prontos}/{total}", 5)
        if ready:
            pyxel.text(42, 57, "Voce esta pronto (espaco)", 3)
        else:
            pyxel.text(42, 57, "Voce nao esta pronto (espaco)", 8)

        if player_id == get_host_id():
            pyxel.text(62, 75, f"Dificuldade: {dificuldade.upper()}", 5)
            pyxel.text(44, 85, "1-Facil  2-Media  3-Dificil", 5)
            pyxel.text(43, 95, "Pressione ENTER para iniciar", 5)
        return

    # Tela de fim de jogo
    if state == "fim" and show_game_over:
        pyxel.cls(0)
        pyxel.text(70, 60, "TODOS MORRERAM!", pyxel.frame_count % 16)
        pyxel.text(50, 75, f"Faltavam {countdown_time}s para vencer", 8)
        return

    # Tela de vitória
    if state == "vitoria":
        pyxel.cls(0)
        pyxel.text(70, 60, "VOCE(S) VENCERAM!", pyxel.frame_count % 16)
        pyxel.text(66, 75, f"Dificuldade: {dificuldade.upper()}", 10)
        return

    # Desenha asteroides na tela
    for a in asteroids:
        tipo = a.get('tipo', 0)
        u = tipo * 8
        pyxel.blt(a['x'], a['y'], 0, u, 0, 8, 8, colkey=0)

    # Desenha os jogadores (exceto o próprio)
    for pid in players:
        if pid == player_id:
            continue
        p = players[pid]
        if p.get('exploded'):
            exp_frame = p.get('exploded_frame')
            if exp_frame:
                draw_explosion(p['x'], p['y'], exp_frame, py_time)
            continue
        pyxel.blt(p['x'], p['y'], 0, 10, 8, 9, 16, colkey=0)

    # Desenha o próprio jogador
    my = players.get(player_id)
    if my:
        if my.get('exploded'):
            exp_frame = my.get('exploded_frame')
            if exp_frame:
                draw_explosion(x, y + 4, exp_frame, py_time, offset_y=0)
        else:
            pyxel.blt(x, y, 0, 0, 8, 9, 16, colkey=0)

    # Mostra o tempo restante na tela
    if state == "jogo" and game_start_time:
        pyxel.text(WIDTH - 50, 10, f"Tempo: {countdown_time}", 8)

# Inicia o loop principal do jogo
pyxel.run(update, draw)
