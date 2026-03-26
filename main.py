import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import random
import os
from flask import Flask
import threading

# Yahan apna bot token dalein
TOKEN = '8694277322:AAHHDn1OR1cnwkZlpIHv3UwQ8GeMT99sjMQ'
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

# Aapki Admin ID
ADMIN_ID = 1484173564

# Database Setup
conn = sqlite3.connect('webseries_bot.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS channels (channel_id TEXT, link TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS join_reqs (user_id INTEGER, channel_id TEXT)''')
conn.commit()

# ================= FLASK WEB SERVER (For Render Free Tier) =================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running perfectly on Render!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ================= ADMIN PANEL =================

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id != ADMIN_ID:
        return 
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("➕ Add Channel", callback_data="add_channel"))
    markup.add(InlineKeyboardButton("➖ Remove Channel", callback_data="remove_channel"))
    markup.add(InlineKeyboardButton("📋 View Added Channels", callback_data="view_channels"))
    
    bot.send_message(message.chat.id, "👨‍💻 <b>Admin Panel</b>\n\nKya karna chahte ho?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["add_channel", "remove_channel", "view_channels"])
def admin_callbacks(call):
    if call.message.chat.id != ADMIN_ID:
        return

    if call.data == "add_channel":
        msg = bot.send_message(call.message.chat.id, "🤖 Pehle bot ko channel me Admin banao!\n\nPhir mujhe sirf Channel ID send karo (Example: <code>-100123456789</code>):")
        bot.register_next_step_handler(msg, process_add_channel)
        
    elif call.data == "view_channels":
        c.execute("SELECT channel_id, link FROM channels")
        channels = c.fetchall()
        if not channels:
            bot.send_message(call.message.chat.id, "❌ Koi channel added nahi hai.")
            return
        text = "📋 <b>Added Channels:</b>\n\n"
        for ch in channels:
            text += f"ID: <code>{ch[0]}</code>\nLink: {ch[1]}\n\n"
        bot.send_message(call.message.chat.id, text, disable_web_page_preview=True)
        
    elif call.data == "remove_channel":
        msg = bot.send_message(call.message.chat.id, "🗑️ Jisko remove karna hai uska Channel ID send karo:")
        bot.register_next_step_handler(msg, process_remove_channel)

def process_add_channel(message):
    ch_id = message.text.strip()
    try:
        bot_member = bot.get_chat_member(ch_id, bot.get_me().id)
        if bot_member.status != 'administrator':
            bot.send_message(message.chat.id, "❌ Bot is channel me Admin nahi hai! Pehle bot ko us channel me admin banao phir try karo.")
            return
        
        invite_link = bot.create_chat_invite_link(ch_id, creates_join_request=True)
        
        c.execute("INSERT INTO channels (channel_id, link) VALUES (?, ?)", (ch_id, invite_link.invite_link))
        conn.commit()
        bot.send_message(message.chat.id, f"✅ Channel <code>{ch_id}</code> add ho gaya!\nBot ne khud link bana liya hai: {invite_link.invite_link}")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error aaya! Check karo:\n1. Kya ID sahi hai? (-100 se shuru hoti hai)\n2. Kya bot us channel me admin hai?\n\n(Error detail: {e})")

def process_remove_channel(message):
    ch_id = message.text.strip()
    c.execute("DELETE FROM channels WHERE channel_id=?", (ch_id,))
    conn.commit()
    bot.send_message(message.chat.id, f"✅ Channel <code>{ch_id}</code> ko list se remove kar diya gaya hai!")

# ================= JOIN REQUEST HANDLER =================

@bot.chat_join_request_handler()
def handle_join_request(message: telebot.types.ChatJoinRequest):
    user_id = message.from_user.id
    channel_id = str(message.chat.id)
    c.execute("INSERT INTO join_reqs (user_id, channel_id) VALUES (?, ?)", (user_id, channel_id))
    conn.commit()

# ================= USER START & VERIFY =================

@bot.message_handler(commands=['start'])
def start_cmd(message):
    send_force_sub(message.chat.id, message.from_user.id)

def check_user_status(user_id):
    c.execute("SELECT channel_id FROM channels")
    channels = c.fetchall()
    
    if not channels:
        return True 
        
    for ch in channels:
        ch_id = ch[0]
        joined = False
        try:
            status = bot.get_chat_member(ch_id, user_id).status
            if status in ['member', 'administrator', 'creator']:
                joined = True
        except:
            pass
        
        if not joined:
            c.execute("SELECT * FROM join_reqs WHERE user_id=? AND channel_id=?", (user_id, ch_id))
            if not c.fetchone():
                return False 
    return True

def send_force_sub(chat_id, user_id):
    if check_user_status(user_id):
        send_key(chat_id)
        return

    image_url = "https://files.catbox.moe/wcfmqd.jpg"
    caption = (
        "𝗛ᴇʟʟᴏ 𝗨ꜱᴇʀ 👻 𝐁𝐎𝐓\n\n"
        "ALL CHANNEL JOIN 🥰\n\n"
        "<a href='https://t.me/setupchanel_0/60'>𝐇𝐎𝐖 𝐓𝐎 𝐆𝐄𝐍𝐄𝐑𝐀𝐓𝐄 𝐊𝐄𝐘 💀\n"
        "𝐂𝐋𝐈𝐂𝐊 𝐇𝐄𝐑𝐄</a>\n\n"
        "👻 Sab channels join karo phir VERIFY dabao"
    )
    
    markup = InlineKeyboardMarkup()
    c.execute("SELECT link FROM channels")
    channels = c.fetchall()
    
    for i, ch in enumerate(channels):
        markup.add(InlineKeyboardButton(f"🔔 Join Channel {i+1}", url=ch[0]))
        
    markup.add(InlineKeyboardButton("✅ VERIFY", callback_data="verify_channels"))
    
    bot.send_photo(chat_id, image_url, caption=caption, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "verify_channels")
def verify_callback(call):
    if check_user_status(call.from_user.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        send_key(call.message.chat.id)
    else:
        bot.answer_callback_query(call.id, "❌ Aapne abhi tak sabhi channels me Join Request nahi bheji hai!", show_alert=True)

# ================= KEY GENERATOR =================

def send_key(chat_id):
    key = f"{random.randint(1000000000, 9999999999)}"
    text = (
        f"Key - <code>{key}</code>\n\n"
        "<a href='https://t.me/+MkNcxGuk-w43MzBl'>DRIP SCINET APK - https://www.mediafire.com/file/if3uvvwjbj87lo2/DRIPCLIENT_v6.2_GLOBAL_AP.apks/file</a>"
    )
    bot.send_message(chat_id, text, disable_web_page_preview=True)

# ================= START SYSTEM =================
if __name__ == "__main__":
    # Web server ko alag thread me chalana taaki Render port detect kar le
    threading.Thread(target=run_web).start()
    
    print("Bot is running...")
    bot.infinity_polling(allowed_updates=telebot.util.update_types)
