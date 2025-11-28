import argparse
import keys

# System parameters
ID = 0
PORT = 5000
PEERS = ["alpha", "bravo", "charlie", "delta"]
PUBLIC_KEY = ""
PRIVATE_KEY = ""

def parse():
  global ID
  global PUBLIC_KEY
  global PRIVATE_KEY

  parser = argparse.ArgumentParser()
  parser.add_argument("-id", type=int, help="Node id")

  args = parser.parse_args()

  if args.id is not None:
    ID = args.id

  PRIVATE_KEY, PUBLIC_KEY = keys.generate()

def log():
  print("=== Node Configuration ===")
  print(f"ID:          {ID}")
  print(f"PORT:        {PORT}")
  print(f"PEERS:       {', '.join(PEERS)}")
  print(f"PRIVATE_KEY: {PRIVATE_KEY}")
  print(f"PUBLIC_KEY:  {PUBLIC_KEY}")
  print("==========================")
