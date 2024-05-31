import sqlite3

from Cryptodome.Cipher import AES
from Cryptodome.Protocol.KDF import PBKDF2

def export_all_chrome_linux_cookies(path_to_db):
    connection = sqlite3.connect(path_to_db)
    cursor = connection.cursor()
    result = cursor.execute("SELECT * from cookies")
    data = result.fetchall()
    data_as_dicts = []
    for row in data:
        # TODO: Does sqlite3's Python bindings have a way to do this directly?
        data_as_dicts.append({
            'creation_utc': row[0],
            'host_key': row[1],
            'top_frame_site_key': row[2],
            'name': row[3],
            'unencrypted_value': row[4],
            'value': decrypt_chrome_linux_cookie(row[5]) if row[5] else "",
            'path': row[6],
            'expires_utc': row[7],
            'is_secure': row[8],
            'is_httponly': row[9],
            'last_access_utc': row[10],
            'has_expires': row[11],
            'is_persistent': row[12],
            'priority': row[13],
            'samesite': row[14],
            'source_scheme': row[15],
            'source_port': row[16],
            'last_update_utc': row[17],
            'source_type': row[18],
            'has_cross_site_ancestor': row[19],
        })
    return data_as_dicts

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
