import socket
import config
import threading
import time

send_channels = {}

recv_channels = {}
recv_lock = threading.Lock()

# Event that is set once the server socket has been bound & is listening.
server_ready = threading.Event()

def dial(retries=10, backoff=0.5):
  """Attempt to connect to each peer with retries/backoff.

  This makes containers resilient to startup order: peers will retry
  connecting if a remote listener isn't ready yet.
  """
  for i, host in enumerate(config.PEERS):
    if i == config.ID:
      continue

    attempt = 0
    while attempt < retries:
      try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2.0)
        s.connect((host, config.PORT))
        # success
        send_channels[host] = s
        print(f"[SEND] Connected to {host}:{config.PORT}")
        with ready_cond:
          ready_cond.notify_all()
        break
      except Exception as e:
        attempt += 1
        print(f"[SEND] Failed to connect to {host} (attempt {attempt}/{retries}): {e}")
        time.sleep(backoff)
    else:
      print(f"[SEND] Giving up connecting to {host} after {retries} attempts")


def handle_connection(conn, addr):
  host, port = addr
  print(f"[RECV] Incoming connection from {host}:{port}")

  with recv_lock:
    recv_channels[host] = conn

  with ready_cond:
    ready_cond.notify_all()


def listen():
  server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  server.bind(("0.0.0.0", config.PORT))
  server.listen()

  # Signal that we are now listening so dialers can proceed.
  server_ready.set()

  print(f"Listening for peers on port {config.PORT}...")

  while True:
    conn, addr = server.accept()
    t = threading.Thread(target=handle_connection, args=(conn, addr), daemon=True)
    t.start()

def start_listener(wait=True, timeout=5.0):
  t = threading.Thread(target=listen, daemon=True)
  t.start()
  if wait:
    # Wait for the server socket to be bound before returning. This avoids
    # races where dial() runs before the listener is ready.
    ok = server_ready.wait(timeout=timeout)
    if not ok:
      print(f"[WARN] Listener didn't become ready within {timeout} seconds")

ready_lock = threading.Lock()
ready_cond = threading.Condition(ready_lock)

def expected_peers():
  return len(config.PEERS) - 1

def wait_for_send_channels():
  expected = expected_peers()
  with ready_cond:
    while len(send_channels) < expected:
      ready_cond.wait()

def wait_for_recv_channels():
  expected = expected_peers()
  with ready_cond:
    while len(recv_channels) < expected:
      ready_cond.wait()

def wait_for_all_channels():
  expected = expected_peers()
  with ready_cond:
    while (len(send_channels) < expected or len(recv_channels) < expected):
      ready_cond.wait()
