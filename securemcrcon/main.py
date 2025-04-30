import json
import sys
from datetime import datetime

from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

from .cli import argParser
from .cli.keyManager import verifyKey
from .client.encryptedRCON import EncryptedRCON
from .client.legacyRCON import LegacyRCON
from .utils.exchange import getPasswordNow


def main():
    args = argParser.parse(sys.argv)
    session = PromptSession()

    pwd = args.password
    if args.dynmaic:
        pwd = getPasswordNow(args.password)
    client = None
    if not args.encrypt:
        client = LegacyRCON()
        try:
            connectResult = client.connect(args.hostname, args.port, pwd, False)
        except Exception as error:
            print("Login failed. (0)")
            print(error)
            quit(1)
        else:
            if not connectResult:
                print("Login failed. (1)")
                quit(1)
    elif args.encrypt:
        client = EncryptedRCON()
        try:
            client.connect(args.hostname, args.port, pwd, True)  # 先获取key
            if client.getPublicKeyHash():
                verifyResult = verifyKey(f"{args.hostname}_{args.port}", client.getPublicKeyHash().hex(), False)
                if verifyResult is False:
                    print(
                        f"WARNING!!! Different public key hash from first login and this login! If server was changed, delete ~/{args.hostname}:{args.port}.mcrconkey sure.")
                    quit(2)
                elif verifyResult is None:
                    print(
                        "Confirm public key of server. If you using SecureRCON MCDR plugin, type `!!RCONkey` to get public key hash and confirm it.")
                    print(f"Server public key hash (SHA256): {client.getPublicKeyHash().hex()}")
                    print(f"Server hostname and port: {args.hostname}:{args.port}")
                    result = input("Type your choice(Y/n): ")
                    if not result.upper() == "Y":
                        print(f"Server public key not confirmed.")
                        quit(1)
                    verifyKey(f"{args.hostname}_{args.port}", client.getPublicKeyHash().hex(), True)
            else:
                print("Failed to verify key.")
                quit(1)
            client = EncryptedRCON()
            connectResult = client.connect(args.hostname, args.port, pwd, False)
        except Exception as error:
            print("Login failed. (0)")
            print(error)
            quit(1)
        else:
            if not connectResult:
                print("Login failed. (1)")
                quit(1)

    def chatCallback(content):
        willPrint = ""
        try:
            content = json.loads(content)
            time = datetime.fromtimestamp(content['time']).strftime('%H:%M:%S')
            willPrint = f"[{time}] <{content.get('source', '???')}> {content.get('content', '???')}"
        except:
            willPrint = content
        with patch_stdout():
            print(willPrint)

    chat = False
    if args.chat:
        chat = True
        if client:
            client.setChat()
    if args.encrypt and isinstance(client, EncryptedRCON):
        print(f"Server public key hash (SHA256): {client.getPublicKeyHash().hex()}")
    print("Type `$exit` or press Ctrl+C to exit; Type `$chat` to enter chat mode.")
    while True:
        try:
            command = session.prompt('> ').strip()
            if command == '$exit':
                raise EOFError
            elif command == '$chat':
                if client:
                    if not chat:
                        client.setChat()
                        client.setChatCallback(chatCallback)
                        print("Enter chat")
                        chat = True
                    else:
                        client.setChat()
                        print("Leave chat")
                        chat = False
            else:
                if client:
                    if chat:
                        client.chat(command)
                    else:
                        result = client.sendCommand(command)
                        print(result)
        except (KeyboardInterrupt, EOFError):
            print('\nBye!')
            break


if __name__ == '__main__':
    main()
