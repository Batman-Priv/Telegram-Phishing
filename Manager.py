import os
import sys
import asyncio
import shlex
import sqlite3
import getpass
from datetime import datetime
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, FloodWaitError, PeerFloodError, RPCError

API_ID = 2040
API_HASH = 'b18441a1ff607e10a989891a5462e627'
VERSION = "2.0.0"
DB_PATH = "telegram_manager.db"

C = {
    'R': '\033[91m', 'G': '\033[92m', 'Y': '\033[93m', 'B': '\033[94m',
    'M': '\033[95m', 'C': '\033[96m', 'W': '\033[97m', 'GR': '\033[90m',
    'BD': '\033[1m', 'RS': '\033[0m'
}


class AccountSession:
    def __init__(self, alias, client, session_name):
        self.alias = alias
        self.client = client
        self.session_name = session_name
        self.user_info = None
        self.monitoring = False
        self.monitor_mode = None
        self.monitor_target = None
        self.handler_registered = False


class TelegramAccountManager:
    def __init__(self):
        self.accounts = {} 
        self.active_alias = None
        self.history = []
        self.commands = {}
        self.db = None
        self.setup_commands()
        self.init_db()

    def p(self, text, color='W', bold=False):
        prefix = C['BD'] if bold else ''
        print(f"{prefix}{C[color]}{text}{C['RS']}")

    def p_header(self, text):
        self.p("=" * 70, 'C', True)
        self.p(f" {text}", 'C', True)
        self.p("=" * 70, 'C', True)

    def p_success(self, text):
        self.p(f"[+] {text}", 'G')

    def p_error(self, text):
        self.p(f"[!] {text}", 'R')

    def p_info(self, text):
        self.p(f"[*] {text}", 'Y')

    def p_debug(self, text):
        self.p(f"[#] {text}", 'GR')

    async def ainput(self, prompt=""):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, input, prompt)

    async def apassword(self, prompt="Password: "):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, getpass.getpass, prompt)

    def p_prompt(self):
        if self.active_alias and self.active_alias in self.accounts:
            acc = self.accounts[self.active_alias]
            name = (acc.user_info.username or acc.user_info.first_name) if acc.user_info else acc.alias
            n_active = len(self.accounts)
            return (f"{C['G']}┌─[{C['C']}{name}{C['GR']}:{acc.alias}{C['Y']} "
                    f"({n_active} acc){C['RS']}]\n{C['G']}└──╼ {C['W']}")
        return f"{C['G']}┌─[{C['R']}disconnected{C['RS']}]\n{C['G']}└──╼ {C['W']}"

    def init_db(self):
        self.db = sqlite3.connect(DB_PATH)
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account TEXT,
                timestamp TEXT,
                sender TEXT,
                chat TEXT,
                text TEXT,
                is_media INTEGER
            )
        """)
        self.db.commit()

    def log_message(self, account, sender, chat, text, is_media):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.db.execute(
            "INSERT INTO messages (account, timestamp, sender, chat, text, is_media) VALUES (?,?,?,?,?,?)",
            (account, ts, sender, chat, text, 1 if is_media else 0)
        )
        self.db.commit()

    def setup_commands(self):
        self.commands = {
            'help': {'func': self.cmd_help, 'desc': 'Show this help menu'},
            '?': {'func': self.cmd_help, 'desc': 'Alias for help'},
            'sessions': {'func': self.cmd_sessions, 'desc': 'List .session/.string files on disk'},
            'connect': {'func': self.cmd_connect, 'desc': 'connect <session_name> [alias] - use existing .session file'},
            'string': {'func': self.cmd_string, 'desc': 'string <file|token> [alias] - use existing string session'},
            'create': {'func': self.cmd_create, 'desc': 'create <session_name> [alias] - LOGIN and create a new .session file'},
            'create_string': {'func': self.cmd_create_string, 'desc': 'create_string [alias] [save_file] - LOGIN and create a new String Session'},
            'export_string': {'func': self.cmd_export_string, 'desc': 'export_string [:alias] [save_file] - dump an active account as a String Session'},
            'logout': {'func': self.cmd_logout, 'desc': 'logout [:alias] - fully revoke session (not just disconnect)'},
            'accounts': {'func': self.cmd_accounts, 'desc': 'List currently connected accounts'},
            'switch': {'func': self.cmd_switch, 'desc': 'switch <alias> - set active account'},
            'info': {'func': self.cmd_info, 'desc': 'info [:alias] - account info'},
            'monitor': {'func': self.cmd_monitor, 'desc': 'monitor [:alias] <mode> [target]'},
            'watchall': {'func': self.cmd_watchall, 'desc': 'watchall <mode> [target] - monitor on every connected account'},
            'stop': {'func': self.cmd_stop, 'desc': 'stop [:alias|all] - stop monitoring'},
            'send': {'func': self.cmd_send, 'desc': 'send [:alias] <target> <message>'},
            'send_media': {'func': self.cmd_send_media, 'desc': 'send_media [:alias] <target> <file> [caption]'},
            'whois': {'func': self.cmd_whois, 'desc': 'whois [:alias] <username|id|phone>'},
            'dialogs': {'func': self.cmd_dialogs, 'desc': 'dialogs [:alias] [n] - list recent chats'},
            'join': {'func': self.cmd_join, 'desc': 'join [:alias] <invite_link|username>'},
            'leave': {'func': self.cmd_leave, 'desc': 'leave [:alias] <chat>'},
            'download': {'func': self.cmd_download, 'desc': 'download [:alias] <chat> [message_id] - fetch last/specific media'},
            'logs': {'func': self.cmd_logs, 'desc': 'logs [:alias] [n] - show recent logged messages'},
            'history': {'func': self.cmd_history, 'desc': 'Show command history'},
            'clear': {'func': self.cmd_clear, 'desc': 'Clear the screen'},
            'disconnect': {'func': self.cmd_disconnect, 'desc': 'disconnect [:alias|all]'},
            'exit': {'func': self.cmd_exit, 'desc': 'Exit the program'},
            'quit': {'func': self.cmd_exit, 'desc': 'Alias for exit'},
        }

    def parse_alias(self, args):
        """If first arg looks like ':alias', pull it out. Returns (alias_or_None, rest_args)."""
        if args and args[0].startswith(':'):
            return args[0][1:], args[1:]
        return None, args

    def get_account(self, alias=None, silent=False):
        alias = alias or self.active_alias
        if not alias or alias not in self.accounts:
            if not silent:
                self.p_error("No active/valid account. Use 'connect', 'string' or 'switch'.")
            return None
        return self.accounts[alias]

    def find_all_sessions(self):
        normal, string_files = [], []
        for file in os.listdir('.'):
            if file.endswith('.session'):
                normal.append(file.replace('.session', ''))
            elif file.endswith('_string.txt') or file.endswith('.string.txt'):
                string_files.append(file)
        return normal, string_files

    def show_banner(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        banner = f"""
{C['C']}██████ ▄▄▄▄▄ ▄▄    ▄▄▄▄▄  ▄▄▄▄ ▄▄▄▄   ▄▄▄  ▄▄   ▄▄   ██▄  ▄██  ▄████  
  ██   ██▄▄  ██    ██▄▄  ██ ▄▄ ██▄█▄ ██▀██ ██▀▄▀██   ██ ▀▀ ██ ██  ▄▄▄ 
  ██   ██▄▄▄ ██▄▄▄ ██▄▄▄ ▀███▀ ██ ██ ██▀██ ██   ██   ██    ██  ▀███▀  

        ACCOUNT MANAGER FRAMEWORK v{VERSION} (multi-account)
{C['RS']}
"""
        print(banner)
        self.p("Type 'help' for available commands", 'Y')
        self.p("Type 'sessions' to see available session files", 'Y')
        self.p("Prefix any command's args with ':alias' to target a specific account", 'Y')
        self.p("=" * 70, 'C')

    async def cmd_help(self, args):
        self.p_header("COMMAND REFERENCE")
        self.p("  " + "─" * 66, 'C')
        for cmd, data in sorted(self.commands.items()):
            self.p(f"  {cmd:<14}{data['desc']}", 'W')
        self.p("  " + "─" * 66, 'C')
        self.p("\n[+] Multi-account examples:", 'G')
        self.p("  create acc1.session main       # login by phone -> new .session file", 'W')
        self.p("  create_string work mywork.txt  # login by phone -> new string session", 'W')
        self.p("  connect acc1.session main", 'W')
        self.p("  string acc2_string.txt work", 'W')
        self.p("  switch work", 'W')
        self.p("  send :main @username Hello", 'W')
        self.p("  watchall all", 'W')
        self.p("  dialogs :main 10", 'W')
        self.p("  export_string :main backup.txt", 'W')

    async def cmd_sessions(self, args):
        normal, string_files = self.find_all_sessions()
        self.p_header("SESSION FILES ON DISK")
        if normal:
            self.p("\n  [.session files]", 'C', True)
            for i, s in enumerate(normal, 1):
                tag = " (connected)" if s in [a.session_name for a in self.accounts.values()] else ""
                self.p(f"    {i}. {s}.session{tag}", 'G')
        if string_files:
            self.p("\n  [String Session files]", 'C', True)
            for i, s in enumerate(string_files, 1):
                self.p(f"    {i}. {s}", 'M')
        if not normal and not string_files:
            self.p("\n  No session files found!", 'Y')

    async def cmd_connect(self, args):
        if not args:
            self.p_info("Usage: connect <session_name> [alias]")
            return
        session_name = args[0]
        alias = args[1] if len(args) > 1 else session_name
        if alias in self.accounts:
            self.p_error(f"Alias '{alias}' is already connected. Pick another alias or disconnect it first.")
            return
        try:
            client = TelegramClient(session_name, API_ID, API_HASH)
            await client.connect()
            if await client.is_user_authorized():
                acc = AccountSession(alias, client, session_name)
                acc.user_info = await client.get_me()
                self.accounts[alias] = acc
                self.active_alias = alias
                self.p_success(f"[{alias}] Connected as: {acc.user_info.first_name}"
                                f" (@{acc.user_info.username or '-'}) — set active")
            else:
                self.p_error("Session is not authorized!")
                await client.disconnect()
        except Exception as e:
            self.p_error(f"Connection failed: {str(e)}")

    async def cmd_string(self, args):
        if not args:
            self.p_info("Usage: string <file|token> [alias]")
            return
        string_input = args[0]
        alias = args[1] if len(args) > 1 else f"str{len(self.accounts) + 1}"
        if alias in self.accounts:
            self.p_error(f"Alias '{alias}' already in use.")
            return

        string_session = None
        if os.path.exists(string_input):
            try:
                with open(string_input, 'r') as f:
                    string_session = f.read().strip()
                self.p_info(f"Loaded String Session from: {string_input}")
            except Exception as e:
                self.p_error(f"Failed to read file: {str(e)}")
                return
        else:
            string_session = string_input

        if not string_session:
            self.p_error("Empty String Session!")
            return

        try:
            client = TelegramClient(StringSession(string_session), API_ID, API_HASH)
            await client.connect()
            if await client.is_user_authorized():
                acc = AccountSession(alias, client, f"string:{alias}")
                acc.user_info = await client.get_me()
                self.accounts[alias] = acc
                self.active_alias = alias
                self.p_success(f"[{alias}] Connected as: {acc.user_info.first_name}"
                                f" (@{acc.user_info.username or '-'}) — set active")
            else:
                self.p_error("String Session is invalid!")
                await client.disconnect()
        except Exception as e:
            self.p_error(f"Connection failed: {str(e)}")

    async def _login_flow(self, client):
        try:
            phone = await self.ainput("  Phone number (with country code, e.g. +989121234567): ")
            phone = phone.strip()
            await client.send_code_request(phone)
            code = await self.ainput("  Login code sent by Telegram: ")
            try:
                await client.sign_in(phone=phone, code=code.strip())
            except SessionPasswordNeededError:
                pw = await self.apassword("  Two-step verification password: ")
                await client.sign_in(password=pw)
            return True
        except RPCError as e:
            self.p_error(f"Login failed: {str(e)}")
            return False
        except Exception as e:
            self.p_error(f"Login failed: {str(e)}")
            return False

    async def cmd_create(self, args):
        if not args:
            self.p_info("Usage: create <session_name> [alias]")
            return
        session_name = args[0]
        alias = args[1] if len(args) > 1 else session_name
        if alias in self.accounts:
            self.p_error(f"Alias '{alias}' already connected.")
            return
        if os.path.exists(f"{session_name}.session"):
            self.p_error(f"'{session_name}.session' already exists. Use 'connect' instead, or pick another name.")
            return

        client = TelegramClient(session_name, API_ID, API_HASH)
        await client.connect()
        self.p_info(f"Creating new session file '{session_name}.session' — starting login...")
        ok = await self._login_flow(client)
        if not ok or not await client.is_user_authorized():
            await client.disconnect()
            if os.path.exists(f"{session_name}.session"):
                try:
                    os.remove(f"{session_name}.session")
                except OSError:
                    pass
            self.p_error("Session creation aborted.")
            return

        acc = AccountSession(alias, client, session_name)
        acc.user_info = await client.get_me()
        self.accounts[alias] = acc
        self.active_alias = alias
        self.p_success(f"[{alias}] New session file created & connected as: "
                        f"{acc.user_info.first_name} (@{acc.user_info.username or '-'})")

    async def cmd_create_string(self, args):
        alias = args[0] if args else f"str{len(self.accounts) + 1}"
        save_file = args[1] if len(args) > 1 else None
        if alias in self.accounts:
            self.p_error(f"Alias '{alias}' already connected.")
            return

        client = TelegramClient(StringSession(), API_ID, API_HASH)
        await client.connect()
        self.p_info("Creating new String Session — starting login...")
        ok = await self._login_flow(client)
        if not ok or not await client.is_user_authorized():
            await client.disconnect()
            self.p_error("String session creation aborted.")
            return

        string_session = client.session.save()
        acc = AccountSession(alias, client, f"string:{alias}")
        acc.user_info = await client.get_me()
        self.accounts[alias] = acc
        self.active_alias = alias

        self.p_success(f"[{alias}] New String Session created & connected as: "
                        f"{acc.user_info.first_name} (@{acc.user_info.username or '-'})")
        self.p_header("STRING SESSION (keep this secret!)")
        self.p(f"  {string_session}", 'M')
        if save_file:
            try:
                with open(save_file, 'w') as f:
                    f.write(string_session)
                self.p_success(f"Saved to file: {save_file}")
            except Exception as e:
                self.p_error(f"Could not save to file: {e}")

    async def cmd_export_string(self, args):
        alias, args = self.parse_alias(args)
        acc = self.get_account(alias)
        if not acc:
            return
        save_file = args[0] if args else None
        try:
            string_session = StringSession.save(acc.client.session)
            self.p_header(f"STRING SESSION FOR [{acc.alias}] (keep this secret!)")
            self.p(f"  {string_session}", 'M')
            if save_file:
                with open(save_file, 'w') as f:
                    f.write(string_session)
                self.p_success(f"Saved to file: {save_file}")
        except Exception as e:
            self.p_error(f"Could not export session: {e}")

    async def cmd_logout(self, args):
        alias, args = self.parse_alias(args)
        acc = self.get_account(alias)
        if not acc:
            return
        try:
            await acc.client.log_out()
        except Exception as e:
            self.p_error(f"Logout failed: {e}")
            return
        acc.monitoring = False
        del self.accounts[acc.alias]
        if self.active_alias == acc.alias:
            self.active_alias = next(iter(self.accounts), None)
        if acc.session_name and not acc.session_name.startswith("string:") and os.path.exists(f"{acc.session_name}.session"):
            try:
                os.remove(f"{acc.session_name}.session")
            except OSError:
                pass
        self.p_success(f"[{alias or acc.alias}] Logged out and session revoked.")

    async def cmd_accounts(self, args):
        if not self.accounts:
            self.p_info("No accounts connected yet. Use 'connect' or 'string'.")
            return
        self.p_header("CONNECTED ACCOUNTS")
        for alias, acc in self.accounts.items():
            marker = f"{C['G']}*{C['RS']}" if alias == self.active_alias else " "
            uname = f"@{acc.user_info.username}" if acc.user_info and acc.user_info.username else "-"
            mon = f"{C['M']}[monitoring:{acc.monitor_mode}]{C['RS']}" if acc.monitoring else ""
            self.p(f" {marker} {alias:<12} {uname:<20} id={acc.user_info.id if acc.user_info else '?'} {mon}", 'W')

    async def cmd_switch(self, args):
        if not args:
            self.p_info("Usage: switch <alias>")
            return
        alias = args[0]
        if alias not in self.accounts:
            self.p_error(f"No connected account with alias '{alias}'. See 'accounts'.")
            return
        self.active_alias = alias
        self.p_success(f"Active account switched to: {alias}")

    async def cmd_info(self, args):
        alias, args = self.parse_alias(args)
        acc = self.get_account(alias)
        if not acc:
            return
        me = await acc.client.get_me()
        self.p_header(f"ACCOUNT INFORMATION [{acc.alias}]")
        self.p(f"  ID: {me.id}", 'W')
        self.p(f"  Name: {me.first_name} {me.last_name or ''}", 'W')
        self.p(f"  Username: @{me.username if me.username else 'None'}", 'W')
        self.p(f"  Phone: {me.phone if hasattr(me, 'phone') else 'Hidden'}", 'W')
        self.p(f"  Verified: {getattr(me, 'verified', False)}", 'W')
        self.p(f"  Premium: {getattr(me, 'premium', False)}", 'W')

    def _register_handler(self, acc):
        if acc.handler_registered:
            return

        @acc.client.on(events.NewMessage())
        async def handle_message(event, acc=acc):
            if not acc.monitoring:
                return
            message = event.message
            sender = await event.get_sender()
            chat = await event.get_chat()
            mode, target = acc.monitor_mode, acc.monitor_target

            should_process = False
            if mode == 'all':
                should_process = True
            elif mode == 'user':
                if target and sender:
                    if (sender.id == target or
                            (getattr(sender, 'username', None) and
                             sender.username == str(target).replace('@', ''))):
                        should_process = True
                elif not target:
                    should_process = True
            elif mode in ('group', 'channel'):
                if target and chat:
                    if (chat.id == target or
                            (getattr(chat, 'username', None) and
                             chat.username == str(target).replace('@', ''))):
                        should_process = True
                elif not target:
                    should_process = True

            if not should_process:
                return

            sender_info = "Unknown"
            if sender:
                if getattr(sender, 'username', None):
                    sender_info = f"@{sender.username}"
                elif hasattr(sender, 'first_name'):
                    sender_info = f"{sender.first_name} {sender.last_name or ''} ({sender.id})"
                else:
                    sender_info = f"ID: {sender.id}"

            chat_info = "Unknown"
            if chat:
                if getattr(chat, 'title', None):
                    chat_info = chat.title
                elif getattr(chat, 'username', None):
                    chat_info = f"@{chat.username}"
                else:
                    chat_info = f"ID: {chat.id}"

            text = message.text or ""
            is_media = bool(message.media)
            self.log_message(acc.alias, sender_info, chat_info, text, is_media)

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.p("\n" + "=" * 70, 'M')
            self.p(f"[{timestamp}] account={acc.alias}", 'C')
            self.p_info(f"From: {sender_info}")
            self.p_info(f"Chat: {chat_info}")
            if text:
                self.p(f"Message: {text}", 'W')
            elif is_media:
                self.p("Media message", 'W')
            self.p("=" * 70, 'M')

        acc.handler_registered = True

    async def cmd_monitor(self, args):
        alias, args = self.parse_alias(args)
        acc = self.get_account(alias)
        if not acc:
            return
        if acc.monitoring:
            self.p_info(f"[{acc.alias}] Already monitoring.")
            return
        if not args:
            self.p_info("Usage: monitor [:alias] <all|user|group|channel> [target]")
            return

        mode = args[0].lower()
        target = None
        if len(args) > 1:
            target = args[1]
            if target.isdigit():
                target = int(target)

        acc.monitor_mode = mode
        acc.monitor_target = target
        acc.monitoring = True
        self._register_handler(acc)

        self.p_success(f"[{acc.alias}] Monitoring started! Mode: {mode}" + (f" target={target}" if target else ""))

    async def cmd_watchall(self, args):
        if not self.accounts:
            self.p_error("No connected accounts.")
            return
        if not args:
            self.p_info("Usage: watchall <all|user|group|channel> [target]")
            return
        for alias, acc in self.accounts.items():
            if acc.monitoring:
                continue
            mode = args[0].lower()
            target = args[1] if len(args) > 1 else None
            if target and target.isdigit():
                target = int(target)
            acc.monitor_mode = mode
            acc.monitor_target = target
            acc.monitoring = True
            self._register_handler(acc)
        self.p_success(f"Monitoring started on {len(self.accounts)} account(s).")

    async def cmd_stop(self, args):
        alias, args = self.parse_alias(args)
        if alias == "all" or (args and args[0] == "all"):
            for acc in self.accounts.values():
                acc.monitoring = False
            self.p_success("Monitoring stopped on all accounts.")
            return
        acc = self.get_account(alias)
        if not acc:
            return
        if not acc.monitoring:
            self.p_info(f"[{acc.alias}] Monitoring is not running.")
            return
        acc.monitoring = False
        self.p_success(f"[{acc.alias}] Monitoring stopped!")

    async def cmd_send(self, args):
        alias, args = self.parse_alias(args)
        acc = self.get_account(alias)
        if not acc:
            return
        if len(args) < 2:
            self.p_info("Usage: send [:alias] <target> <message>")
            return
        target = args[0]
        message = ' '.join(args[1:])
        try:
            entity = await acc.client.get_entity(target)
            await acc.client.send_message(entity, message)
            self.p_success(f"[{acc.alias}] Message sent to: {target}")
        except FloodWaitError as e:
            self.p_error(f"Flood wait: Telegram wants you to wait {e.seconds}s before sending again.")
        except PeerFloodError:
            self.p_error("Peer flood: too many requests to this user/chat recently. Slow down.")
        except Exception as e:
            self.p_error(f"Failed: {str(e)}")

    async def cmd_send_media(self, args):
        alias, args = self.parse_alias(args)
        acc = self.get_account(alias)
        if not acc:
            return
        if len(args) < 2:
            self.p_info("Usage: send_media [:alias] <target> <file_path> [caption]")
            return
        target = args[0]
        file_path = args[1]
        caption = ' '.join(args[2:]) if len(args) > 2 else ""
        if not os.path.exists(file_path):
            self.p_error(f"File not found: {file_path}")
            return
        try:
            entity = await acc.client.get_entity(target)
            await acc.client.send_file(entity, file_path, caption=caption)
            self.p_success(f"[{acc.alias}] Media sent to: {target}")
        except FloodWaitError as e:
            self.p_error(f"Flood wait: Telegram wants you to wait {e.seconds}s before sending again.")
        except Exception as e:
            self.p_error(f"Failed: {str(e)}")

    async def cmd_whois(self, args):
        alias, args = self.parse_alias(args)
        acc = self.get_account(alias)
        if not acc:
            return
        if not args:
            self.p_info("Usage: whois [:alias] <username|id|phone>")
            return
        target = args[0]
        try:
            entity = await acc.client.get_entity(target)
            self.p_header(f"ENTITY INFORMATION [{acc.alias}]")
            self.p(f"  ID: {entity.id}", 'W')
            if hasattr(entity, 'first_name'):
                self.p(f"  Name: {entity.first_name} {entity.last_name or ''}", 'W')
            if getattr(entity, 'username', None):
                self.p(f"  Username: @{entity.username}", 'W')
            if hasattr(entity, 'title'):
                self.p(f"  Title: {entity.title}", 'W')
            if hasattr(entity, 'bot'):
                self.p(f"  Is Bot: {entity.bot}", 'W')
            if hasattr(entity, 'verified'):
                self.p(f"  Verified: {entity.verified}", 'W')
            if hasattr(entity, 'participants_count'):
                self.p(f"  Members: {entity.participants_count}", 'W')
            if hasattr(entity, 'dc_id'):
                self.p(f"  DC ID: {entity.dc_id}", 'W')
        except Exception as e:
            self.p_error(f"Failed: {str(e)}")

    async def cmd_dialogs(self, args):
        alias, args = self.parse_alias(args)
        acc = self.get_account(alias)
        if not acc:
            return
        limit = int(args[0]) if args and args[0].isdigit() else 15
        try:
            self.p_header(f"RECENT CHATS [{acc.alias}]")
            async for dialog in acc.client.iter_dialogs(limit=limit):
                kind = "Group/Channel" if dialog.is_group or dialog.is_channel else "User"
                unread = f" ({dialog.unread_count} unread)" if dialog.unread_count else ""
                self.p(f"  [{dialog.id}] {dialog.name}  <{kind}>{unread}", 'W')
        except Exception as e:
            self.p_error(f"Failed: {str(e)}")

    async def cmd_join(self, args):
        alias, args = self.parse_alias(args)
        acc = self.get_account(alias)
        if not acc:
            return
        if not args:
            self.p_info("Usage: join [:alias] <invite_link|username>")
            return
        target = args[0]
        try:
            if 'joinchat' in target or '+' in target.split('/')[-1]:
                from telethon.tl.functions.messages import ImportChatInviteRequest
                invite_hash = target.rstrip('/').split('/')[-1].lstrip('+')
                await acc.client(ImportChatInviteRequest(invite_hash))
            else:
                from telethon.tl.functions.channels import JoinChannelRequest
                entity = await acc.client.get_entity(target)
                await acc.client(JoinChannelRequest(entity))
            self.p_success(f"[{acc.alias}] Joined: {target}")
        except FloodWaitError as e:
            self.p_error(f"Flood wait: wait {e.seconds}s before joining again.")
        except Exception as e:
            self.p_error(f"Failed to join: {str(e)}")

    async def cmd_leave(self, args):
        alias, args = self.parse_alias(args)
        acc = self.get_account(alias)
        if not acc:
            return
        if not args:
            self.p_info("Usage: leave [:alias] <chat>")
            return
        target = args[0]
        try:
            entity = await acc.client.get_entity(target)
            await acc.client.delete_dialog(entity)
            self.p_success(f"[{acc.alias}] Left: {target}")
        except Exception as e:
            self.p_error(f"Failed: {str(e)}")

    async def cmd_download(self, args):
        alias, args = self.parse_alias(args)
        acc = self.get_account(alias)
        if not acc:
            return
        if not args:
            self.p_info("Usage: download [:alias] <chat> [message_id]")
            return
        chat = args[0]
        msg_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
        try:
            entity = await acc.client.get_entity(chat)
            if msg_id:
                message = await acc.client.get_messages(entity, ids=msg_id)
            else:
                message = None
                async for m in acc.client.iter_messages(entity, limit=50):
                    if m.media:
                        message = m
                        break
            if not message or not message.media:
                self.p_error("No media found.")
                return
            os.makedirs("downloads", exist_ok=True)
            path = await acc.client.download_media(message, file="downloads/")
            self.p_success(f"[{acc.alias}] Downloaded to: {path}")
        except Exception as e:
            self.p_error(f"Failed: {str(e)}")

    async def cmd_logs(self, args):
        alias, args = self.parse_alias(args)
        limit = 20
        if args and args[0].isdigit():
            limit = int(args[0])
        query = "SELECT timestamp, account, sender, chat, text, is_media FROM messages"
        params = ()
        if alias:
            query += " WHERE account = ?"
            params = (alias,)
        query += " ORDER BY id DESC LIMIT ?"
        params = params + (limit,)
        rows = self.db.execute(query, params).fetchall()
        if not rows:
            self.p_info("No logged messages yet.")
            return
        self.p_header(f"RECENT LOGGED MESSAGES{' [' + alias + ']' if alias else ''}")
        for ts, account, sender, chat, text, is_media in reversed(rows):
            body = text if text else "<media>"
            self.p(f"  [{ts}] ({account}) {sender} -> {chat}: {body}", 'W')

    async def cmd_history(self, args):
        if not self.history:
            self.p_info("No command history.")
            return
        self.p_header("COMMAND HISTORY")
        for i, cmd in enumerate(self.history[-20:], 1):
            self.p(f"  {i:3}. {cmd}", 'W')

    async def cmd_clear(self, args):
        os.system('cls' if os.name == 'nt' else 'clear')

    async def cmd_disconnect(self, args):
        alias, args = self.parse_alias(args)
        target = alias or (args[0] if args else None)

        if target == "all":
            for a in list(self.accounts.keys()):
                acc = self.accounts.pop(a)
                acc.monitoring = False
                await acc.client.disconnect()
            self.active_alias = None
            self.p_success("Disconnected all accounts.")
            return

        acc = self.get_account(target)
        if not acc:
            return
        acc.monitoring = False
        await acc.client.disconnect()
        del self.accounts[acc.alias]
        if self.active_alias == acc.alias:
            self.active_alias = next(iter(self.accounts), None)
        self.p_success(f"Disconnected: {acc.alias}")

    async def cmd_exit(self, args):
        for acc in self.accounts.values():
            acc.monitoring = False
            await acc.client.disconnect()
        if self.db:
            self.db.close()
        self.p("Goodbye!", 'C', True)
        sys.exit(0)

    async def execute_command(self, command_line):
        if not command_line.strip():
            return
        self.history.append(command_line)
        try:
            parts = shlex.split(command_line)
        except ValueError as e:
            self.p_error(f"Parse error: {e}")
            return
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        if cmd in self.commands:
            try:
                await self.commands[cmd]['func'](args)
            except Exception as e:
                self.p_error(f"Command error: {str(e)}")
        else:
            self.p_error(f"Unknown command: {cmd}")
            self.p_info("Type 'help' for available commands")

    async def run(self):
        self.show_banner()
        normal, string_files = self.find_all_sessions()
        if normal or string_files:
            self.p_info(f"Found {len(normal)} .session file(s) and {len(string_files)} string session file(s)")
        else:
            self.p_info("No session files found on disk yet.")
        self.p("=" * 70, 'C')

        loop = asyncio.get_event_loop()
        while True:
            try:
                command = await loop.run_in_executor(None, input, self.p_prompt())
                await self.execute_command(command)
            except KeyboardInterrupt:
                self.p("\n[!] Interrupted", 'Y')
                continue
            except EOFError:
                self.p("\n[!] EOF", 'Y')
                break
            except Exception as e:
                self.p_error(f"Error: {str(e)}")


async def main():
    manager = TelegramAccountManager()
    await manager.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{C['R']}[!] Exited{C['RS']}")
    except Exception as e:
        print(f"\n{C['R']}[!] Fatal error: {str(e)}{C['RS']}")
