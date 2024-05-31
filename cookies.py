import sqlite3

from Cryptodome.Cipher import AES
from Cryptodome.Protocol.KDF import PBKDF2

def export_all_chrome_linux_cookies(path_to_db):
    connection = sqlite3.connect(path_to_db)
    cursor = connection.cursor()
    result = cursor.execute("SELECT * from cookies")
    data = result.fetchall()
    return data

def decrypt_chrome_linux_cookie(encrypted_value):
    # Trim off the 'v10' that Chrome/ium prepends
    encrypted_value = encrypted_value[3:]
    # Default values used by both Chrome and Chromium in OSX and Linux
    salt = b'saltysalt'
    iv = b' ' * 16
    length = 16
    # On Mac, replace with your password from Keychain
    my_pass = "peanuts"
    my_pass = my_pass.encode('utf8')
    # 1003 on Mac, 1 on Linux
    iterations = 1

    key = PBKDF2(my_pass, salt, length, iterations)
    cipher = AES.new(key, AES.MODE_CBC, IV=iv)

    decrypted = cipher.decrypt(encrypted_value)

    # Function to get rid of padding
    def clean(x):
        return x[:-x[-1]].decode('utf8')

    cleaned = clean(decrypted)
    return cleaned
