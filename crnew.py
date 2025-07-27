import telebot
from telebot import types
import random
import string
import json
import os
import threading
import time

# ====== BOT CONFIGURATION ======
BOT_TOKEN = "7308448311:AAH8PKkA9q-NAygvgZn-xtMv4AgJeEY2EAU"
OWNER_ID = 5727462573
bot = telebot.TeleBot(BOT_TOKEN)

# ====== DATA STORAGE ======
DATA_FILE = "bot_data.json"
admins = {OWNER_ID}
user_ids = set()
broadcast_temp = {}
accounts = []
active_codes = {}
redeemed_users = {}

# ====== HELPERS ======
def save_data():
    data = {
        "BOT_TOKEN": BOT_TOKEN,
        "OWNER_ID": OWNER_ID,
        "admins": list(admins),
        "user_ids": list(user_ids),
        "broadcast_temp": broadcast_temp,
        "accounts": accounts,
        "active_codes": active_codes,
        "redeemed_users": redeemed_users
    }
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_data():
    global admins, user_ids, broadcast_temp, accounts, active_codes, redeemed_users
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            admins = set(data.get("admins", []))
            user_ids = set(data.get("user_ids", []))
            broadcast_temp = data.get("broadcast_temp", {})
            accounts = data.get("accounts", [])
            active_codes = data.get("active_codes", {})
            redeemed_users = data.get("redeemed_users", {})

def auto_save():
    while True:
        time.sleep(300)  # 5 minutes
        save_data()

def auto_send_data():
    while True:
        time.sleep(300)  # 5 minutes
        try:
            save_data()
            if os.path.exists(DATA_FILE):
                bot.send_document(OWNER_ID, open(DATA_FILE, "rb"), caption="🔄 Auto-backup of bot data")
        except Exception as e:
            print(f"Error sending data: {e}")

def is_owner(user_id):
    return user_id == OWNER_ID

def is_admin(user_id):
    return user_id in admins

def add_user(user_id):
    user_ids.add(user_id)

def gen_code():
    part1 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    part2 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"BHAINKAR-{part1}-{part2}"

def notify_admins(msg, photo=None):
    targets = list(admins)
    for t in targets:
        try:
            if photo:
                bot.send_photo(t, photo, caption=msg)
            else:
                bot.send_message(t, msg, parse_mode="Markdown")
        except:
            pass

# ====== COMMANDS ======
@bot.message_handler(commands=['start'])
def start_cmd(message):
    add_user(message.from_user.id)
    save_data()
    bot.reply_to(message, "👋 Welcome! Use  /redeem `BHAINKAR-XXXX-XXXX` to claim rewards.\nType /help to see available commands.")

@bot.message_handler(commands=['help', 'cmd'])
def help_cmd(message):
    bot.send_message(
        message.chat.id,
        "📜 *User Commands:*\n\n"
        "☄️ <b>Start:</b> Use /start to start the bot\n"
        "🎁 <b>Redeem:</b> Use /redeem `BHAINKAR-XXXX-XXXX` to redeem a code to get rewards\n"
        "🆘 <b>Guide:</b> Use /help or /cmd to show this help menu\n"
        "ℹ️ <b>Details:</b> Use /details to check your info.",
        parse_mode="HTML"
    )

@bot.message_handler(commands=['addadmin'])
def add_admin_cmd(message):
    if not is_owner(message.from_user.id):
        return bot.reply_to(message, "❌ Only the owner can add admins.")
    try:
        chat_id = int(message.text.split()[1])
        admins.add(chat_id)
        save_data()
        bot.reply_to(message, f"✅ Added new admin: `{chat_id}`", parse_mode="Markdown")
    except:
        bot.reply_to(message, "❌ Usage: /addadmin <chat_id>")

@bot.message_handler(commands=['radmin'])
def remove_admin_cmd(message):
    if not is_owner(message.from_user.id):
        return bot.reply_to(message, "❌ Only the owner can remove admins.")
    try:
        chat_id = int(message.text.split()[1])
        if chat_id in admins and chat_id != OWNER_ID:
            admins.remove(chat_id)
            save_data()
            bot.reply_to(message, f"✅ Removed admin: `{chat_id}`", parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ That user is not an admin or is the owner.")
    except:
        bot.reply_to(message, "❌ Usage: /radmin <chat_id>")

@bot.message_handler(commands=['addacc'])
def addacc_cmd(message):
    if not is_admin(message.from_user.id):
        return bot.reply_to(message, "❌ Only admins or owner can add accounts.")
    try:
        acc = message.text.split(' ', 1)[1]
        accounts.append(acc.strip())
        save_data()
        bot.reply_to(message, f"✅ Account added to stock:\n`{acc}`", parse_mode="Markdown")
    except:
        bot.reply_to(message, "❌ Usage: /addacc email:password")

@bot.message_handler(commands=['maddacc'])
def maddacc_cmd(message):
    if not is_admin(message.from_user.id):
        return bot.reply_to(message, "❌ Only admins or owner can add accounts.")
    try:
        data = message.text.split(' ', 1)[1]
        lines = [line.strip() for line in data.split('\n') if ':' in line]
        accounts.extend(lines)
        save_data()
        bot.reply_to(message, f"✅ Added {len(lines)} accounts to stock.", parse_mode="Markdown")
    except:
        bot.reply_to(message, "❌ Usage: /maddacc email:pass\\nemail:pass\\nemail:pass")

@bot.message_handler(commands=['delacc'])
def delacc_cmd(message):
    if not is_admin(message.from_user.id):
        return bot.reply_to(message, "❌ Only admins or owner can delete accounts.")
    try:
        acc = message.text.split(' ', 1)[1]
        if acc in accounts:
            accounts.remove(acc)
            save_data()
            bot.reply_to(message, f"✅ Account removed:\n`{acc}`", parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ Account not found.")
    except:
        bot.reply_to(message, "❌ Usage: /delacc email:password")

@bot.message_handler(commands=['stock'])
def stock_cmd(message):
    if not is_admin(message.from_user.id):
        return bot.reply_to(message, "❌ Only admins or owner can view stock.")
    if not accounts:
        return bot.reply_to(message, "📦 No stock available.")
    stock_list = "\n".join([f"{i+1}. {acc}" for i, acc in enumerate(accounts)])
    bot.send_message(message.chat.id, f"📦 *Stock Accounts:*\n\n```\n{stock_list}\n```", parse_mode="Markdown")

@bot.message_handler(commands=['gencode'])
def gencode_cmd(message):
    if not is_owner(message.from_user.id):
        return bot.reply_to(message, "❌ Only the owner can generate codes.")
    try:
        amount = int(message.text.split()[1])
    except:
        return bot.reply_to(message, "❌ Usage: /gencode <amount>")
    codes = []
    for _ in range(amount):
        code = gen_code()
        reward = accounts.pop(0) if accounts else "No Reward"
        active_codes[code] = {"used": False, "reward": reward, "redeemed_by": None}
        codes.append(f"➟ `{code}`")
    save_data()
    msg = "✅ *Redeem Codes Generated*\n\n" + "\n".join(codes) + "\n\n➟ To Redeem: @crunchyrollaccbot\nType: `/redeem BHAINKAR-XXXX-XXXX`"
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

@bot.message_handler(commands=['redeem'])
def redeem_cmd(message):
    try:
        code = message.text.split()[1].strip().upper()
    except:
        return bot.reply_to(message, "❌ Usage: /redeem <code>")
    if code not in active_codes:
        return bot.reply_to(message, "❌ Invalid redeem code.")
    if active_codes[code]["used"]:
        return bot.reply_to(message, "⚠️ This code has already been used.")
    reward = active_codes[code]["reward"]
    active_codes[code]["used"] = True
    active_codes[code]["redeemed_by"] = message.from_user.id
    redeemed_users[message.from_user.id] = code
    save_data()
    if reward == "No Reward":
        return bot.reply_to(message, "❌ No reward linked with this code.")
    try:
        email, password = reward.split(":", 1)
    except:
        email, password = reward, "N/A"
    msg = (
        "Cʀᴜɴᴄʜʏʀᴏʟʟ ᥫ᭡ Pʀᴇᴍɪᴜᴍ\n\n"
        f"Eᴍᴀɪɪ ✉️: `{email}`\n"
        f"Pᴀssᴡᴏʀᴅ 🔑: `{password}`\n\n"
        "Bᴏᴛ ʙʏ @bhainkar"
    )
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")
    bot.send_message(message.chat.id, "📸 Send your proof screenshot here to complete verification.")

@bot.message_handler(content_types=['photo'])
def handle_proof(message):
    user_id = message.from_user.id
    if user_id not in redeemed_users:
        return bot.reply_to(message, "❌ You can only send proof after redeeming a code.")
    code = redeemed_users[user_id]
    caption = f"📢 Proof submitted by {message.from_user.first_name} (ID: {user_id})\nRedeemed Code: `{code}`"
    file_id = message.photo[-1].file_id
    notify_admins(caption, photo=file_id)
    bot.reply_to(message, "✅ Your proof has been sent to the admins.")

@bot.message_handler(commands=['getdata'])
def send_data_file(message):
    if not is_owner(message.from_user.id):
        return bot.reply_to(message, "❌ Only owner can get data.")
    save_data()
    bot.send_document(message.chat.id, open(DATA_FILE, "rb"))

@bot.message_handler(commands=['broadcast'])
def start_broadcast(message):
    if not is_owner(message.from_user.id):
        return bot.reply_to(message, "❌ Only owner can broadcast.")
    msg = bot.send_message(message.chat.id, "✏️ Send the message you want to broadcast:")
    bot.register_next_step_handler(msg, receive_broadcast_text)

def receive_broadcast_text(message):
    if not is_owner(message.from_user.id):
        return
    text = message.text
    broadcast_temp[message.from_user.id] = {"text": text}
    save_data()
    bot.send_message(
        message.chat.id,
        "✅ Message saved for broadcast.\n\nUse:\n"
        "`/preview` - Show the broadcast message\n"
        "`/confirm` - Send the broadcast\n"
        "`/cancel` - Cancel broadcast",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['preview'])
def preview_broadcast(message):
    if not is_owner(message.from_user.id):
        return
    if message.from_user.id not in broadcast_temp:
        return bot.reply_to(message, "❌ No broadcast message saved.")
    text = broadcast_temp[message.from_user.id]["text"]
    bot.send_message(message.chat.id, f"**Broadcast Preview:**\n\n{text}", parse_mode="Markdown")

@bot.message_handler(commands=['confirm'])
def confirm_broadcast(message):
    if not is_owner(message.from_user.id):
        return
    if message.from_user.id not in broadcast_temp:
        return bot.reply_to(message, "❌ No broadcast message saved.")
    text = broadcast_temp.pop(message.from_user.id)["text"]
    save_data()
    bot.send_message(message.chat.id, "📢 Sending broadcast...")
    sent = 0
    for uid in list(user_ids):
        try:
            bot.send_message(uid, text)
            sent += 1
        except:
            pass
    bot.send_message(message.chat.id, f"✅ Broadcast sent to {sent} users.")

@bot.message_handler(commands=['cancel'])
def cancel_broadcast(message):
    if not is_owner(message.from_user.id):
        return
    if message.from_user.id not in broadcast_temp:
        return bot.reply_to(message, "❌ No broadcast message to cancel.")
    broadcast_temp.pop(message.from_user.id)
    save_data()
    bot.send_message(message.chat.id, "❌ Broadcast canceled.")

@bot.message_handler(commands=['details'])
def details(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    chat_id = message.chat.id
    gif_url = "https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExNWt0YWZyaHRrbG5xNzN4MTlkOWZmeDRyZ2ZjcmlwMjhlcnE1azVlNiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/2FHr56vo08zbq8ac0C/giphy.gif"
    bot.send_animation(chat_id, gif_url, caption=f"𝗬𝗼𝘂𝗿 𝗗𝗲𝘁𝗮𝗶𝗹𝘀:\n<b>Username:</b> @{username}\n<b>Chat ID:</b> <code>{user_id}</code>\n\n<b>Bᴏᴛ ʙʏ</b> @bhainkar", parse_mode="HTML")

# ====== RUN BOT ======
print("🤖 Bot is running...")
load_data()
threading.Thread(target=auto_save, daemon=True).start()
threading.Thread(target=auto_send_data, daemon=True).start()
bot.infinity_polling()
