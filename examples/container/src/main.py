import config
import peers

def main():
  config.parse()
  config.log()

  peers.start_listener()
  peers.dial()

  peers.wait_for_all_channels()

if __name__ == "__main__":
  main()
