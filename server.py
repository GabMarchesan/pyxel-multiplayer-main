import socket
import json
import time
import uuid
import random

HOST = '0.0.0.0'
PORT = 12345

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))
sock.settimeout(1)

addr_to_id = {}
players = {}
last_seen = {}
game_state = "menu"
fim_time = None
start_time = None
py_time = int(time.time() * 30)

dificuldade = 'facil'
dificuldade_prob = {
  'facil': 0.1,
  'media': 0.2,
  'dificil': 0.4
}
dificuldade_vel = {
  'facil': 30,
  'media': 60,
  'dificil': 75
}

asteroids = []

def colisao(p, a):
    nave_w = 8
    nave_h = 8
    asteroide_r = 2
    return (
      a['x'] + asteroide_r > p['x'] and
      a['x'] - asteroide_r < p['x'] + nave_w and
      a['y'] + asteroide_r > p['y'] and
      a['y'] - asteroide_r < p['y'] + nave_h
    )

def gerar_asteroide():
    ax = random.randint(0, 200 - 4)
    ay = -10
    tipo = random.randint(0, 3)
    return {'x': ax, 'y': ay, 'tipo': tipo}

last_loop = time.time()

try:
  while True:
    print(players)
    py_time = int(time.time() * 30)
    now = time.time()
    delta = now - last_loop
    last_loop = now

    try:
      data, addr = sock.recvfrom(1024)
      msg = json.loads(data.decode())

      if addr not in addr_to_id:
        addr_to_id[addr] = str(uuid.uuid4())[:8]

      pid = addr_to_id[addr]
      if pid not in players:
        players[pid] = {'x': msg['x'], 'y': msg['y'], 'ready': msg.get('ready', False), 'exploded': False}
      else:
        if not players[pid].get('exploded'):
          players[pid]['x'] = msg['x']
          players[pid]['y'] = msg['y']
        players[pid]['ready'] = msg.get('ready', False)

      host_id = sorted(players.keys())[0] if players else None

      if game_state == "menu":
        all_ready = all(p.get('ready') for p in players.values())
        if all_ready and msg.get('start') and pid == host_id:
          if 'dificuldade' in msg:
            dificuldade = msg['dificuldade']
          game_state = "jogo"
          start_time = time.time()

      last_seen[pid] = time.time()
      active_ids = [pid for pid in players if players[pid].get('exploded') or time.time() - last_seen[pid] < 5]
      players = {pid: players[pid] for pid in active_ids}

      if game_state == "jogo" and random.random() < dificuldade_prob[dificuldade] * delta * 60:
        asteroids.append(gerar_asteroide())

      for a in asteroids:
        a['y'] += dificuldade_vel[dificuldade] * delta

      asteroids = [a for a in asteroids if a['y'] < 140]

      for pid in list(players.keys()):
        p = players[pid]
        if p.get('exploded'):
          continue
        for a in asteroids:
          if colisao(p, a):
            p['exploded'] = True
            p['exploded_frame'] = py_time
            break

      alive = [p for p in players.values() if not p.get('exploded')]
      if game_state == "jogo":
        if not alive:
          game_state = "fim"
          fim_time = time.time()
        elif start_time is not None and time.time() - start_time >= 30:
          game_state = "vitoria"
          fim_time = time.time()

      if game_state in ("fim", "vitoria") and fim_time is not None and time.time() - fim_time > 5:
        game_state = "menu"
        asteroids.clear()
        for p in players.values():
          p['exploded'] = False
          p['ready'] = False
        fim_time = None
        start_time = None

      for client_addr, client_id in addr_to_id.items():
        if client_id not in players:
          continue
        out = json.dumps({
          'players': players,
          'your_id': client_id,
          'asteroids': asteroids,
          'state': game_state
        }).encode()
        sock.sendto(out, client_addr)

    except socket.timeout:
      continue

except KeyboardInterrupt:
  print('\nEncerrando servidor...')
finally:
  sock.close()
