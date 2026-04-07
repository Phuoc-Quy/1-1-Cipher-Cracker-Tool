import random

def encrypter(plaintext, key):
    plaintext = plaintext.upper()
    plaintext = ''.join(filter(str.isalpha, plaintext))
    key = key.upper()

    encrypted = ''
    for i in range(len(plaintext)):
        encrypted += key[ord(plaintext[i])-ord('A')]

    return encrypted

def decrypter(encrypted, key):
    encrypted = encrypted.upper()
    encrypted = ''.join(filter(str.isalpha, encrypted))
    key = key.upper()

    decrypted = ''
    for i in range(len(encrypted)):
        decrypted += chr(key.index(encrypted[i])+ord('A'))

    return decrypted

def key_generator():
    alphabet = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    random.shuffle(alphabet)
    key = ''.join(alphabet)
    return key

def read_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def main():
    file_path = "plaintext_code.txt"
    lines = read_file(file_path).strip()
    for line in lines.split('\n\n'):
        key = key_generator()
        encrypted = encrypter(line, key)
        decrypted = decrypter(encrypted, key)
        print("Plaintext: ", line)
        print("Key: ", key)
        print("Encrypted: ", encrypted)
        print("Decrypted: ", decrypted)
        print()

main()