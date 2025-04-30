import argparse
from typing import Sequence


def parse(args: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="A RCON Client let you connect to a Minecraft Server via RCON Protocol or Secure RCON.")

    networkGroup = parser.add_argument_group('Network')
    networkGroup.add_argument('hostname', type=str, help=f"server hostname or IP")
    networkGroup.add_argument('--port', '-p', type=int, default=25575, help="RCON Port")
    networkGroup.add_argument('--password', '--pwd', type=str, default="test", help="RCON Password")
    networkGroup.add_argument('--dynmaic', '--dpwd', action='store_true', default=False, help="Use dynmaic password")

    encryptGroup = parser.add_argument_group('Encrypt')
    encryptGroup.add_argument('--encrypt', '-e', action='store_true', default=False,
                              help=f"Enable encrypt (need server support)")

    miscGroup = parser.add_argument_group('Misc')
    miscGroup.add_argument('--chat', '-c', action='store_true', default=False,
                           help="Enter chat mode (need server support)")

    return parser.parse_args(args)
