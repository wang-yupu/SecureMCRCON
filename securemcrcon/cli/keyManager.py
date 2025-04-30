import os


def verifyKey(name: str, key: str, write=False) -> bool | None:
    userHome = os.path.expanduser('~')

    fixedFolder = os.path.join(userHome, '.mcrconkeys')
    os.makedirs(fixedFolder, exist_ok=True)

    filePath = os.path.join(fixedFolder, f'{name}')

    if os.path.exists(filePath):
        with open(filePath, 'r', encoding='utf-8') as file:
            existingContent = file.read()
            return existingContent == key

    if write:
        with open(filePath, 'w', encoding='utf-8') as file:
            file.write(key)
    return None
