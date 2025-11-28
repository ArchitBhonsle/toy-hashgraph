import socket
import config
import threading
import time

ready_lock = threading.Lock()
ready_cond = threading.Condition(ready_lock)

# Event that is set once the server socket has been bound & is listening.
server_ready = threading.Event()

def dial(retries=10, backoff=0.5):
  """Attempt to connect to each peer with retries/backoff.

  This makes containers resilient to startup order: peers will retry
  connecting if a remote listener isn't ready yet.
  """
  for host in config.PEERS.keys():
    if host == config.NAME:
      continue

    attempt = 0
    while attempt < retries:
      try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2.0)
        s.connect((host, config.PORT))
        # success
        config.PEERS[host]["send_channel"] = s
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
  ip, port = addr
  print(f"[RECV] Incoming connection from {ip}:{port}")

  try:
    hostname = socket.gethostbyaddr(ip)[0]
  except socket.herror:
    hostname = ip  # fallback if no reverse DNS

  print(f"[RECV] Resolved hostname: {hostname}")

  peer_name = extract_peer_name(hostname)
  config.PEERS[peer_name]["recv_channel"] = conn

  with ready_cond:
    ready_cond.notify_all()

def extract_peer_name(hostname: str) -> str:
  try:
    return hostname.split('.')[0].split('-')[1]
  except Exception:
    return hostname

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

def expected_peers():
  return len(config.PEER_NAMES) - 1

def wait_for_all_channels():
  expected = expected_peers()
  with ready_cond:
    while True:
      # Count how many send_channels are established
      send_channels = sum(
        1 for host, ch in config.PEERS.items() if ch.get("send_channel") is not None
      )

      recv_channels = sum(
        1 for host, ch in config.PEERS.items() if ch.get("recv_channel") is not None
      )

      if send_channels == expected and recv_channels == expected:
        break

      ready_cond.wait()
