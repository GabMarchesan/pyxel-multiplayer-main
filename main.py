from pyxel import init, btn,cls, rect, load, circ, blt, COLOR_ORANGE, COLOR_CYAN, run, KEY_W

# Window
init(160, 120)
load("arvore.pyxres")

x = 10
y = 10
radius = 5

player_x = 10
player_y = 10

def update():
    global x, player_y, player_x

    x = x + 1
    if btn(68):  # right
        player_x = player_x + 1
    if btn(65):  # left
        player_x = player_x - 1
    if btn(KEY_W):  # up
        player_y = player_y - 1
    if btn(83):  # down
        player_y = player_y + 1

def draw():
    cls(0)
    rect(x, y, 20, 20, COLOR_ORANGE)
    circ(player_x, player_y, radius, COLOR_CYAN)
    blt(40, 50, 0, 0, 0, 7, 13)
    blt(60, 50, 1, 0, 0, 7, 13)

run(update, draw)
