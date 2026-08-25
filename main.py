import telebot
import sqlite3
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread
import os
import time

# 🌐 Flask ওয়েব সার্ভার সেটআপ (24/7 অন রাখার জন্য)
app = Flask('')

@app.route('/')
def home():
    return "WF Rahim Console: Bot is Running 24/7!"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ----------------- বটের কনফিগারেশন -----------------

API_TOKEN = os.environ.get('BOT_TOKEN', '7610582828:AAEmh9rOgUnVAR-7Qt6H9UEEYnUCuw-Idsw')
ADMIN_ID = 8961605027

CHANNEL_ID = "@wf_rahim_69_ff"  
CHANNEL_LINK = "https://t.me/wf_rahim_69_ff"

GROUP_ID = "@public_group_chate"
GROUP_LINK = "https://t.me/public_group_chate"

BONUS_AMOUNT = 5.0            # প্রতি রেফারে ৫ টাকা
MIN_WITHDRAW = 1000.0         # মিনিমাম উইথড্র অ্যামাউন্ট

bot = telebot.TeleBot(API_TOKEN)
BOT_USERNAME = "Mobile_Panel_bot"

try:
    BOT_USERNAME = bot.get_me().username
except Exception as e:
    print(f"Error getting bot username: {e}")

# 🔒 ডাটাবেজ হ্যান্ডলার
def db_query(query, params=(), fetchone=False, fetchall=False, commit=False):
    conn = sqlite3.connect('dynamic_bot_v2.db', timeout=10)
    cursor = conn.cursor()
    result = None
    try:
        cursor.execute(query, params)
        if commit:
            conn.commit()
        if fetchone:
            result = cursor.fetchone()
        elif fetchall:
            result = cursor.fetchall()
    except Exception as e:
        print(f"Database Error: {e}")
    finally:
        conn.close()
    return result

def init_db():
    db_query('''
        CREATE TABLE IF NOT EXISTS buttons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            message_text TEXT,
            parent_id INTEGER DEFAULT 0
        )
    ''', commit=True)
    
    db_query('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT DEFAULT 'Unknown',
            balance REAL DEFAULT 0.0,
            total_refers INTEGER DEFAULT 0,
            referred_by INTEGER DEFAULT 0,
            is_bonus_claimed INTEGER DEFAULT 0,
            is_banned INTEGER DEFAULT 0
        )
    ''', commit=True)
    
    db_query('''
        CREATE TABLE IF NOT EXISTS packages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            panel_name TEXT,
            duration TEXT,
            price REAL
        )
    ''', commit=True)
    
    db_query('''
        CREATE TABLE IF NOT EXISTS stock_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            package_id INTEGER,
            secret_key TEXT,
            is_sold INTEGER DEFAULT 0
        )
    ''', commit=True)
    
    db_query('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''', commit=True)
    
    default_welcome = (
        "╔════════════════════╗\n"
        "♨️   𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐓𝐎 𝐎𝐔𝐑 𝐁𝐎𝐓   ♨️\n"
        "╚════════════════════╝\n\n"
        "👋 হ্যালো {name} ভাই, আশা করি ভালো আছেন!\n\n"
        "💵 আপনার অ্যাকাউন্ট ব্যালেন্স: ৳{balance} 💵\n"
        "👥 আপনার মোট রেফার: {refers} জন\n"
        "🔗 আপনার রেফারেল লিংক: {reflink}\n\n"
        "🛒 প্যানেল কিনতে বা কাজ করতে নিচের বাটনগুলো ব্যবহার করুন।"
    )
    db_query("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ('welcome_message', default_welcome), commit=True)

init_db()

user_states = {}

def is_user_banned(user_id):
    res = db_query("SELECT is_banned FROM users WHERE user_id=?", (user_id,), fetchone=True)
    return res and res[0] == 1

def is_user_joined(user_id):
    if user_id == ADMIN_ID:
        return True
    try:
        ch_member = bot.get_chat_member(CHANNEL_ID, user_id)
        grp_member = bot.get_chat_member(GROUP_ID, user_id)
        
        ch_ok = ch_member.status in ['member', 'administrator', 'creator']
        grp_ok = grp_member.status in ['member', 'administrator', 'creator']
        
        return ch_ok and grp_ok
    except Exception as e:
        print(f"Check Member Error: {e}")
        return False

def format_user_message(text, user_id, first_name):
    if not text:
        return ""
    reflink = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    res = db_query("SELECT balance, total_refers FROM users WHERE user_id=?", (user_id,), fetchone=True)
    balance = res[0] if res else 0.0
    refers = res[1] if res else 0
    
    formatted_text = text.replace("{name}", str(first_name if first_name else "User"))
    formatted_text = formatted_text.replace("{balance}", str(balance))
    formatted_text = formatted_text.replace("{refers}", str(refers))
    formatted_text = formatted_text.replace("{reflink}", reflink)
    formatted_text = formatted_text.replace("{bonus_amount}", str(BONUS_AMOUNT))
    return formatted_text

def get_main_reply_keyboard(user_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    rows = db_query("SELECT name FROM buttons WHERE parent_id=0", fetchall=True)
    
    temp_row = []
    if rows:
        for row in rows:
            temp_row.append(KeyboardButton(row[0]))
            if len(temp_row) == 2:
                markup.row(*temp_row)
                temp_row = []
        if temp_row:
            markup.row(*temp_row)
        
    markup.row(KeyboardButton("💳 Withdraw"), KeyboardButton("🛒 Buy Panel Keys"))
    if user_id == ADMIN_ID:
        markup.row(KeyboardButton("⚙️ Admin Panel"))
    return markup

def get_inline_keyboard_for_level(parent_id, is_admin=False):
    rows = db_query("SELECT id, name FROM buttons WHERE parent_id=?", (parent_id,), fetchall=True)
    markup = InlineKeyboardMarkup(row_width=2)
    if rows:
        for row in rows:
            markup.add(InlineKeyboardButton(row[1], callback_data=f"btn_{row[0]}"))
    if is_admin:
        markup.row(InlineKeyboardButton("➕ Add Sub-Button", callback_data=f"adm_add_{parent_id}"),
                   InlineKeyboardButton("✏️ Edit Text", callback_data=f"adm_edit_txt_{parent_id}"))
        markup.row(InlineKeyboardButton("❌ Delete This Button", callback_data=f"adm_del_{parent_id}"))
    if parent_id != 0:
        res = db_query("SELECT parent_id FROM buttons WHERE id=?", (parent_id,), fetchone=True)
        back_id = res[0] if res else 0
        markup.row(InlineKeyboardButton("⬅️ Go Back", callback_data=f"btn_{back_id}" if back_id != 0 else "go_main_menu"))
    return markup

# 💰 রেফার বোনাস এবং অ্যাডমিন নোটিফিকেশন (ভেরিফাই ক্লিক করার পর কাজ করবে)
def award_referral_bonus_if_eligible(user_id, first_name, username):
    user_info = db_query("SELECT referred_by, is_bonus_claimed FROM users WHERE user_id=?", (user_id,), fetchone=True)
    if user_info:
        referrer_id, is_claimed = user_info
        if referrer_id and int(referrer_id) != 0 and int(is_claimed) == 0:
            # রেফারকারীর অ্যাকাউন্টে পয়েন্ট যোগ
            db_query("UPDATE users SET balance = balance + ? WHERE user_id=?", (BONUS_AMOUNT, referrer_id), commit=True)
            db_query("UPDATE users SET total_refers = total_refers + 1 WHERE user_id=?", (referrer_id,), commit=True)
            db_query("UPDATE users SET is_bonus_claimed = 1 WHERE user_id=?", (user_id,), commit=True)
            
            try:
                ref_res = db_query("SELECT first_name FROM users WHERE user_id=?", (referrer_id,), fetchone=True)
                referrer_name = ref_res[0] if ref_res else "Unknown User"

                joined_name = first_name if first_name else "User"
                joined_username = f"@{username}" if username else "No Username"
                
                ref_alert_msg = (
                    "╔════════════════════╗\n"
                    "🔔   NEW REFERRAL SUCCESS   🔔\n"
                    "╚════════════════════╝\n\n"
                    "👤 রেফারকারী (Referrer):\n"
                    f"├─ নাম: {referrer_name}\n"
                    f"└─ আইডি: {referrer_id}\n\n"
                    "📥 নতুন মেম্বার (Accepted Member):\n"
                    f"├─ নাম: {joined_name}\n"
                    f"├─ আইডি: {user_id}\n"
                    f"└─ ইউজারনেম: {joined_username}\n\n"
                    f"💰 রেফারকারী বোনাস পেয়েছেন: +৳{BONUS_AMOUNT} টাকা!"
                )
                
                # অ্যাডমিনকে নোটিফিকেশন পাঠানো
                bot.send_message(ADMIN_ID, ref_alert_msg, disable_web_page_preview=True)
                
            except Exception as e:
                print(f"Referral alert notification error: {e}")

            # রেফারকারীকে মেসেজ
            try:
                msg = (
                    "╔════════════════════╗\n"
                    "🎁   REFERRAL BONUS   🎁\n"
                    "╚════════════════════╝\n\n"
                    "⚡ নতুন রেফারাল বোনাস পেয়েছেন!\n"
                    f"👤 আপনার রেফারেল লিঙ্কে {first_name} ভেরিফাই সম্পূর্ণ করেছে।\n"
                    f"💰 আপনি পেয়েছেন: +৳{BONUS_AMOUNT} টাকা!"
                )
                bot.send_message(referrer_id, msg, disable_web_page_preview=True)
            except Exception:
                pass

@bot.message_handler(commands=['start'])
def start_cmd(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    current_name = message.from_user.first_name if message.from_user.first_name else "User"
    
    if is_user_banned(user_id):
        bot.send_message(chat_id, "🚫 দুঃখিত ভাই, আপনাকে এই বটের ভেতর ব্যান করা হয়েছে!")
        return

    text_parts = message.text.split()
    new_ref_id = int(text_parts[1]) if len(text_parts) > 1 and text_parts[1].isdigit() and int(text_parts[1]) != user_id else 0

    user_exists = db_query("SELECT user_id, is_bonus_claimed FROM users WHERE user_id=?", (user_id,), fetchone=True)
    
    if not user_exists:
        db_query("INSERT INTO users (user_id, first_name, referred_by, is_bonus_claimed) VALUES (?, ?, ?, 0)", (user_id, current_name, new_ref_id), commit=True)
    else:
        if new_ref_id != 0:
            db_query("UPDATE users SET first_name=?, referred_by=?, is_bonus_claimed=0 WHERE user_id=?", (current_name, new_ref_id, user_id), commit=True)
        else:
            db_query("UPDATE users SET first_name=? WHERE user_id=?", (current_name, user_id), commit=True)
    
    user_states[chat_id] = None
    welcome_text = db_query("SELECT value FROM settings WHERE key='welcome_message'", fetchone=True)[0]
    formatted_welcome = format_user_message(welcome_text, user_id, message.from_user.first_name)
    
    if user_id == ADMIN_ID or is_user_joined(user_id):
        if user_id != ADMIN_ID:
            award_referral_bonus_if_eligible(user_id, message.from_user.first_name, message.from_user.username)
        bot.send_message(chat_id, formatted_welcome, reply_markup=get_main_reply_keyboard(user_id), disable_web_page_preview=True)
    else:
        join_markup = InlineKeyboardMarkup()
        join_markup.add(InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK))
        join_markup.add(InlineKeyboardButton("💬 Join Group", url=GROUP_LINK))
        join_markup.add(InlineKeyboardButton("✅ Verify", callback_data="verify_and_claim"))
        
        verify_text = (
            "╔════════════════════╗\n"
            "⚠️    JOIN OUR CHANNEL & GROUP    ⚠️\n"
            "╚════════════════════╝\n\n"
            "বটটি ব্যবহার করতে এবং বোনাস ক্লেইম করতে আপনাকে অবশ্যই আমাদের অফিশিয়াল চ্যানেল ও গ্রুপে জয়েন করতে হবে।\n\n"
            f"📢 চ্যানেল: {CHANNEL_LINK}\n"
            f"💬 গ্রুপ: {GROUP_LINK}\n\n"
            "উভয় স্থানে জয়েন করার পর নিচের Verify বাটনে ক্লিক করুন।"
        )
        bot.send_message(chat_id, verify_text, reply_markup=join_markup, disable_web_page_preview=True)

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    text = message.text
    is_admin = (user_id == ADMIN_ID)

    if is_user_banned(user_id):
        bot.send_message(chat_id, "🚫 দুঃখিত ভাই, আপনাকে এই বটের ভেতর ব্যান করা হয়েছে!")
        return

    if not is_user_joined(user_id) and not is_admin:
        join_markup = InlineKeyboardMarkup()
        join_markup.add(InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK))
        join_markup.add(InlineKeyboardButton("💬 Join Group", url=GROUP_LINK))
        join_markup.add(InlineKeyboardButton("✅ Verify", callback_data="verify_and_claim"))
        bot.send_message(chat_id, "⚠️ বট ব্যবহার করতে প্রথমে আমাদের চ্যানেল ও গ্রুপে জয়েন করুন!", reply_markup=join_markup, disable_web_page_preview=True)
        return

    if chat_id in user_states and user_states[chat_id] is not None:
        handle_admin_inputs(message)
        return

    if text == "💳 Withdraw":
        res = db_query("SELECT balance FROM users WHERE user_id=?", (user_id,), fetchone=True)
        user_bal = res[0] if res else 0.0
        
        if user_bal >= MIN_WITHDRAW:
            bot.send_message(chat_id, f"✅ আপনার বর্তমান ব্যালেন্স ৳{user_bal} টাকা। উইথড্র করতে এডমিনের সাথে যোগাযোগ করুন।")
        else:
            bot.send_message(chat_id, f"⚠️ উইথড্র করতে সর্বনিম্ন ১০০০ টাকা কমপ্লিট করতে হবে!\n\n💵 আপনার বর্তমান ব্যালেন্স: ৳{user_bal} টাকা।")
        return

    if text == "🛒 Buy Panel Keys":
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⚡ NON-ROOT", callback_data="shop_cat_NON-ROOT"),
                   InlineKeyboardButton("🔥 ROOT", callback_data="shop_cat_ROOT"))
        markup.add(InlineKeyboardButton("🍏 IPHONE", callback_data="shop_cat_IPHONE"),
                   InlineKeyboardButton("💻 PC", callback_data="shop_cat_PC"))
        
        shop_title = (
            "╔════════════════════╗\n"
            "🛒    PANEL STORE (SHOP)   🛒\n"
            "╚════════════════════╝\n\n"
            "📂 অনুগ্রহ করে আপনার ক্যাটাগরি সিলেক্ট করুন:"
        )
        bot.send_message(chat_id, shop_title, reply_markup=markup, disable_web_page_preview=True)
        return

    if text == "⚙️ Admin Panel" and is_admin:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("➕ Add Main Button", callback_data="adm_add_0"),
                   InlineKeyboardButton("❌ Delete Main Button", callback_data="adm_del_main_start"))
        markup.add(InlineKeyboardButton("💰 Edit User Balance", callback_data="adm_bal_start"),
                   InlineKeyboardButton("📦 Manage Stock & Keys", callback_data="adm_manage_stock"))
        markup.add(InlineKeyboardButton("📊 Bot Statistics", callback_data="adm_stats"),
                   InlineKeyboardButton("📢 Broadcast to All Users", callback_data="adm_broadcast"))
        markup.add(InlineKeyboardButton("🚫 Ban/Unban User", callback_data="adm_ban_start"),
                   InlineKeyboardButton("✍️ Edit Welcome Message", callback_data="adm_edit_welcome"))
        markup.add(InlineKeyboardButton("⚠️ Reset Bot", callback_data="adm_clear_all"))
        bot.send_message(chat_id, "⚙️ Admin Control Panel:", reply_markup=markup, disable_web_page_preview=True)
        return

    res = db_query("SELECT id, name, message_text FROM buttons WHERE parent_id=0 AND name=?", (text,), fetchone=True)
    if res:
        btn_id, btn_name, msg_text = res
        raw_text = msg_text if msg_text else f"📂 {btn_name}"
        formatted_text = format_user_message(raw_text, user_id, message.from_user.first_name)
        bot.send_message(chat_id, formatted_text, reply_markup=get_inline_keyboard_for_level(btn_id, is_admin), disable_web_page_preview=True)

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    data = call.data
    is_admin = (user_id == ADMIN_ID)
    bot.answer_callback_query(call.id)
    if is_user_banned(user_id):
        return

    if data == "verify_and_claim":
        if is_user_joined(user_id) or is_admin:
            if user_id != ADMIN_ID:
                award_referral_bonus_if_eligible(user_id, call.from_user.first_name, call.from_user.username)
            welcome_text = db_query("SELECT value FROM settings WHERE key='welcome_message'", fetchone=True)[0]
            formatted_welcome = format_user_message(welcome_text, user_id, call.from_user.first_name)
            try: bot.delete_message(chat_id, call.message.message_id)
            except Exception: pass
            bot.send_message(chat_id, "✅ ভেরিফিকেশন সফল হয়েছে!", reply_markup=get_main_reply_keyboard(user_id))
            bot.send_message(chat_id, formatted_welcome, disable_web_page_preview=True)
        else:
            bot.send_message(chat_id, f"❌ আপনি চ্যানেল অথবা গ্রুপে জয়েন করেননি!\n📢 চ্যানেল: {CHANNEL_LINK}\n💬 গ্রুপ: {GROUP_LINK}", disable_web_page_preview=True)

    elif data == "go_main_menu":
        try: bot.delete_message(chat_id, call.message.message_id)
        except Exception: pass
        welcome_text = db_query("SELECT value FROM settings WHERE key='welcome_message'", fetchone=True)[0]
        bot.send_message(chat_id, format_user_message(welcome_text, user_id, call.from_user.first_name), reply_markup=get_main_reply_keyboard(user_id), disable_web_page_preview=True)

    elif data.startswith("shop_cat_"):
        cat = data.split("_")[2]
        panels = db_query("SELECT DISTINCT panel_name FROM packages WHERE category=?", (cat,), fetchall=True)
        markup = InlineKeyboardMarkup()
        if panels:
            for p in panels:
                markup.add(InlineKeyboardButton(f"✨ {p[0]}", callback_data=f"shop_panel_{cat}_{p[0]}"))
            markup.add(InlineKeyboardButton("⬅️ Back", callback_data="go_main_menu"))
            bot.edit_message_text(f"🚀 Category: {cat}\n\n📂 অনুগ্রহ করে প্যানেলের নাম সিলেক্ট করুন:", chat_id, call.message.message_id, reply_markup=markup)
        else:
            markup.add(InlineKeyboardButton("⬅️ Back", callback_data="go_main_menu"))
            bot.edit_message_text("⚠️ এই ক্যাটাগরিতে বর্তমানে কোনো একটিভ প্যানেল নেই।", chat_id, call.message.message_id, reply_markup=markup)

    elif data.startswith("shop_panel_"):
        parts = data.split("_")
        cat, panel = parts[2], parts[3]
        pkgs = db_query("SELECT id, duration, price FROM packages WHERE category=? AND panel_name=?", (cat, panel), fetchall=True)
        markup = InlineKeyboardMarkup()
        if pkgs:
            for p in pkgs:
                pkg_id, dur, prc = p
                markup.add(InlineKeyboardButton(f"⏰ {dur} - ৳{prc} 💵", callback_data=f"shop_buy_{pkg_id}"))
            markup.add(InlineKeyboardButton("⬅️ Back", callback_data=f"shop_cat_{cat}"))
            bot.edit_message_text(f"📋 Panel: {panel} ({cat})\n\nকিনতে আপনার কাঙ্ক্ষিত প্যাকেজ ও সময় সিলেক্ট করুন:", chat_id, call.message.message_id, reply_markup=markup)

    elif data.startswith("shop_buy_"):
        pkg_id = int(data.split("_")[2])
        pkg = db_query("SELECT category, panel_name, duration, price FROM packages WHERE id=?", (pkg_id,), fetchone=True)
        if pkg:
            cat, p_name, dur, price = pkg
            user_res = db_query("SELECT balance, total_refers FROM users WHERE user_id=?", (user_id,), fetchone=True)
            user_bal = user_res[0] if user_res else 0.0
            total_refers = user_res[1] if user_res else 0
            
            if user_bal >= price:
                key_avail = db_query("SELECT id, secret_key FROM stock_keys WHERE package_id=? AND is_sold=0 LIMIT 1", (pkg_id,), fetchone=True)
                if key_avail:
                    key_db_id, secret_key = key_avail
                    new_balance = user_bal - price
                    db_query("UPDATE users SET balance = balance - ? WHERE user_id=?", (price, user_id), commit=True)
                    db_query("UPDATE stock_keys SET is_sold=1 WHERE id=?", (key_db_id,), commit=True)
                    
                    success_msg = (
                        f"╔════════════════════╗\n"
                        f"🎉   PURCHASE SUCCESSFUL   🎉\n"
                        f"╚════════════════════╝\n\n"
                        f"📦 প্রোডাক্ট: {p_name} ({cat})\n"
                        f"⏰ মেয়াদ: {dur}\n"
                        f"💰 পরিশোধিত মূল্য: ৳{price} 💵\n\n"
                        f"🔑 আপনার গোপন কী (Key):\n`{secret_key}`\n\n"
                        f"আমাদের থেকে প্রোডাক্ট কেনার জন্য ধন্যবাদ!"
                    )
                    bot.send_message(chat_id, success_msg, parse_mode="Markdown")

                    try:
                        u_name = call.from_user.first_name if call.from_user.first_name else "User"
                        u_username = f"@{call.from_user.username}" if call.from_user.username else "No Username"
                        
                        admin_buy_msg = (
                            "╔════════════════════╗\n"
                            "🛍️   NEW PANEL PURCHASE   🛍️\n"
                            "╚════════════════════╝\n\n"
                            f"📦 প্রোডাক্ট ডিটেইলস:\n"
                            f"├─ প্যানেল: {p_name} ({cat})\n"
                            f"├─ মেয়াদ: {dur}\n"
                            f"└─ মূল্য: ৳{price} টাকা\n\n"
                            f"👤 গ্রাহকের প্রোফাইল ডিটেইলস:\n"
                            f"├─ নাম: {u_name}\n"
                            f"├─ আইডি: {user_id}\n"
                            f"├─ ইউজারনেম: {u_username}\n"
                            f"├─ বর্তমান ব্যালেন্স: ৳{new_balance} টাকা\n"
                            f"└─ মোট রেফার সংখ্যা: {total_refers} টি\n\n"
                            f"🔑 বিক্রি হওয়া কী (Sold Key):\n{secret_key}"
                        )
                        bot.send_message(ADMIN_ID, admin_buy_msg)
                    except Exception as e:
                        print(f"Admin purchase alert error: {e}")
                else:
                    bot.send_message(chat_id, "❌ দুঃখিত! এই প্যাকেজটি বর্তমানে আউট অফ স্টক। এডমিনের সাথে যোগাযোগ করুন।")
            else:
                bot.send_message(chat_id, f"❌ আপনার অ্যাকাউন্টে পর্যাপ্ত ব্যালেন্স নেই!\n\nপ্রয়োজনীয় ব্যালেন্স: ৳{price} 💵\nআপনার বর্তমান ব্যালেন্স: ৳{user_bal} 💵")

    elif data.startswith("btn_"):
        btn_id = int(data.split("_")[1])
        res = db_query("SELECT name, message_text FROM buttons WHERE id=?", (btn_id,), fetchone=True)
        if res:
            raw_text = res[1] if res[1] else f"📂 {res[0]}"
            formatted_text = format_user_message(raw_text, user_id, call.from_user.first_name)
            bot.edit_message_text(formatted_text, chat_id, call.message.message_id, reply_markup=get_inline_keyboard_for_level(btn_id, is_admin), disable_web_page_preview=True)

    elif is_admin:
        if data == "adm_broadcast":
            user_states[chat_id] = {'action': 'broadcast_msg'}
            bot.send_message(chat_id, "📢 সব ইউজারের কাছে যে মেসেজটি পাঠাতে চান তা লিখে পাঠান:")

        elif data == "adm_manage_stock":
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("➕ Create New Package", callback_data="adm_pkg_create"))
            markup.add(InlineKeyboardButton("🔑 Add Keys To Stock", callback_data="adm_key_add_start"))
            markup.add(InlineKeyboardButton("❌ Delete Packages", callback_data="adm_pkg_del_start"))
            bot.send_message(chat_id, "📦 Stock Control Panel", reply_markup=markup)
            
        elif data == "adm_pkg_create":
            user_states[chat_id] = {'action': 'get_pkg_cat'}
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("NON-ROOT", callback_data="setcat_NON-ROOT"), InlineKeyboardButton("ROOT", callback_data="setcat_ROOT"))
            markup.add(InlineKeyboardButton("IPHONE", callback_data="setcat_IPHONE"), InlineKeyboardButton("PC", callback_data="setcat_PC"))
            bot.send_message(chat_id, "Select Category for new package:", reply_markup=markup)

        elif data.startswith("setcat_"):
            cat = data.split("_")[1]
            user_states[chat_id] = {'action': 'get_pkg_name', 'cat': cat}
            bot.send_message(chat_id, f"Category {cat} selected.\nNow enter Panel Name:")

        elif data == "adm_pkg_del_start":
            pkgs = db_query("SELECT id, category, panel_name, duration, price FROM packages", fetchall=True)
            markup = InlineKeyboardMarkup()
            if pkgs:
                for p in pkgs:
                    markup.add(InlineKeyboardButton(f"🗑️ {p[1]} | {p[2]} ({p[3]}) - ৳{p[4]}", callback_data=f"delpkg_{p[0]}"))
                bot.send_message(chat_id, "সিলেক্ট করুন কোন প্যাকেজটি সম্পূর্ণ ডিলিট করতে চান:", reply_markup=markup)
            else:
                bot.send_message(chat_id, "❌ ডিলিট করার মতো কোনো প্যাকেজ পাওয়া যায়নি!")

        elif data.startswith("delpkg_"):
            pkg_id = int(data.split("_")[1])
            db_query("DELETE FROM packages WHERE id=?", (pkg_id,), commit=True)
            db_query("DELETE FROM stock_keys WHERE package_id=?", (pkg_id,), commit=True)
            bot.send_message(chat_id, "✅ প্যাকেজ এবং ওই প্যাকেজের সব কী (Keys) সফলভাবে ডিলিট করা হয়েছে!")

        elif data == "adm_key_add_start":
            pkgs = db_query("SELECT id, category, panel_name, duration FROM packages", fetchall=True)
            markup = InlineKeyboardMarkup()
            if pkgs:
                for p in pkgs:
                    markup.add(InlineKeyboardButton(f"{p[1]} | {p[2]} ({p[3]})", callback_data=f"addkeyto_{p[0]}"))
                bot.send_message(chat_id, "Select the package to load keys into:", reply_markup=markup)
            else:
                bot.send_message(chat_id, "❌ No packages found. Please create a package first!")

        elif data.startswith("addkeyto_"):
            pkg_id = int(data.split("_")[1])
            user_states[chat_id] = {'action': 'get_bulk_keys', 'pkg_id': pkg_id}
            bot.send_message(chat_id, "🔑 Send your keys. (One key per line):")

        elif data == "adm_stats":
            total_users = db_query("SELECT COUNT(*) FROM users", fetchone=True)[0]
            banned_users = db_query("SELECT COUNT(*) FROM users WHERE is_banned=1", fetchone=True)[0]
            total_refers = db_query("SELECT SUM(total_refers) FROM users", fetchone=True)[0] or 0
            bot.send_message(chat_id, f"📊 Bot Stats:\nTotal Users: {total_users}\nBanned: {banned_users}\nTotal Refers: {total_refers}")
            
        elif data == "adm_ban_start":
            user_states[chat_id] = {'action': 'ban_user_id'}
            bot.send_message(chat_id, "Send Telegram User ID to Ban/Unban:")
        elif data == "adm_bal_start":
            user_states[chat_id] = {'action': 'bal_user_id'}
            bot.send_message(chat_id, "Send the User ID:")
        elif data == "adm_edit_welcome":
            user_states[chat_id] = {'action': 'edit_welcome'}
            bot.send_message(chat_id, "Send the new Welcome Message (Use {name}, {balance}, {refers}, {reflink}):")
        elif data.startswith("adm_add_"):
            user_states[chat_id] = {'action': 'add_btn', 'parent_id': int(data.split("_")[2])}
            bot.send_message(chat_id, "Send the button name:")
        elif data.startswith("adm_edit_txt_"):
            user_states[chat_id] = {'action': 'edit_txt', 'btn_id': int(data.split("_")[3])}
            bot.send_message(chat_id, "Send the text content:")
        elif data == "adm_del_main_start":
            rows = db_query("SELECT id, name FROM buttons WHERE parent_id=0", fetchall=True)
            markup = InlineKeyboardMarkup()
            if rows:
                for row in rows:
                    markup.add(InlineKeyboardButton(f"🗑️ {row[1]}", callback_data=f"adm_del_{row[0]}"))
                bot.send_message(chat_id, "সিলেক্ট করুন কোন মেইন বাটনটি ডিলিট করতে চান:", reply_markup=markup)
            else:
                bot.send_message(chat_id, "❌ ডিলিট করার মতো কোনো মেইন বাটন পাওয়া যায়নি!")
        elif data.startswith("adm_del_"):
            btn_id = int(data.split("_")[2])
            db_query("DELETE FROM buttons WHERE id=? OR parent_id=?", (btn_id, btn_id), commit=True)
            bot.send_message(chat_id, "✅ বাটনটি এবং এর অধীনস্থ সকল সাব-বাটন সফলভাবে ডিলিট করা হয়েছে!", reply_markup=get_main_reply_keyboard(user_id))
        elif data == "adm_clear_all":
            db_query("DELETE FROM buttons", commit=True)
            db_query("DELETE FROM packages", commit=True)
            db_query("DELETE FROM stock_keys", commit=True)
            bot.send_message(chat_id, "Buttons and Stock reset completely!", reply_markup=get_main_reply_keyboard(user_id))

def handle_admin_inputs(message):
    chat_id = message.chat.id
    state = user_states[chat_id]
    text = message.text

    if state['action'] == 'broadcast_msg':
        users = db_query("SELECT user_id FROM users WHERE is_banned=0", fetchall=True)
        success = 0
        failed = 0
        
        bot.send_message(chat_id, "⏳ ব্রডকাস্টিং শুরু হয়েছে, অনুগ্রহ করে অপেক্ষা করুন...")
        
        if users:
            for u in users:
                uid = u[0]
                try:
                    bot.send_message(uid, text, disable_web_page_preview=True)
                    success += 1
                    time.sleep(0.05)
                except Exception:
                    failed += 1
        
        bot.send_message(chat_id, f"✅ **ব্রডকাস্ট সম্পন্ন হয়েছে!**\n\n🎯 সফলভাবে পাঠানো হয়েছে: {success} জন\n❌ ব্যর্থ: {failed} জন")
        user_states[chat_id] = None

    elif state['action'] == 'get_pkg_name':
        state['panel_name'] = text
        state['action'] = 'get_pkg_duration'
        bot.send_message(chat_id, "Now enter Duration (e.g., 1 Day, 7 Day):")

    elif state['action'] == 'get_pkg_duration':
        state['duration'] = text
        state['action'] = 'get_pkg_price'
        bot.send_message(chat_id, "Now enter Price (Number only):")

    elif state['action'] == 'get_pkg_price':
        try:
            price = float(text)
            db_query("INSERT INTO packages (category, panel_name, duration, price) VALUES (?, ?, ?, ?)",
                     (state['cat'], state['panel_name'], state['duration'], price), commit=True)
            bot.send_message(chat_id, f"✅ Package created!\n`{state['panel_name']} - {state['duration']} (৳{price})`", parse_mode="Markdown")
        except ValueError:
            bot.send_message(chat_id, "❌ Price must be a number! Try again.")
        user_states[chat_id] = None

    elif state['action'] == 'get_bulk_keys':
        pkg_id = state['pkg_id']
        keys = text.split('\n')
        inserted = 0
        for k in keys:
            if k.strip():
                db_query("INSERT INTO stock_keys (package_id, secret_key) VALUES (?, ?)", (pkg_id, k.strip()), commit=True)
                inserted += 1
        bot.send_message(chat_id, f"✅ Successfully loaded {inserted} keys!")
        user_states[chat_id] = None

    elif state['action'] == 'ban_user_id':
        try:
            target_id = int(text)
            user_info = db_query("SELECT is_banned FROM users WHERE user_id=?", (target_id,), fetchone=True)
            if user_info:
                status = 1 if user_info[0] == 0 else 0
                db_query("UPDATE users SET is_banned=? WHERE user_id=?", (status, target_id), commit=True)
                bot.send_message(chat_id, f"✅ User status updated to {'Banned' if status == 1 else 'Unbanned'}!")
            else:
                bot.send_message(chat_id, "❌ ID not found.")
        except ValueError:
            bot.send_message(chat_id, "❌ Invalid ID format.")
        user_states[chat_id] = None

    elif state['action'] == 'edit_welcome':
        db_query("UPDATE settings SET value=? WHERE key='welcome_message'", (text,), commit=True)
        bot.send_message(chat_id, "✅ Welcome message updated!")
        user_states[chat_id] = None

    elif state['action'] == 'bal_user_id':
        res = db_query("SELECT balance FROM users WHERE user_id=?", (text,), fetchone=True)
        if res:
            state['target_uid'] = text
            state['action'] = 'bal_amount'
            bot.send_message(chat_id, f"Current Balance: {res[0]} points.\nEnter amount to add/subtract (e.g. 50 or -50):")
        else:
            bot.send_message(chat_id, "❌ User not found!")
            user_states[chat_id] = None

    elif state['action'] == 'bal_amount':
        try:
            amount = float(text)
            db_query("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, state['target_uid']), commit=True)
            bot.send_message(chat_id, "✅ Balance updated!")
        except Exception:
            bot.send_message(chat_id, "❌ Invalid number.")
        user_states[chat_id] = None

    elif state['action'] == 'add_btn':
        db_query("INSERT INTO buttons (name, parent_id) VALUES (?, ?)", (text, state['parent_id']), commit=True)
        bot.send_message(chat_id, "✅ Button added successfully!", reply_markup=get_main_reply_keyboard(message.from_user.id))
        user_states[chat_id] = None

    elif state['action'] == 'edit_txt':
        db_query("UPDATE buttons SET message_text=? WHERE id=?", (text, state['btn_id']), commit=True)
        bot.send_message(chat_id, "✅ Text updated!")
        user_states[chat_id] = None

if __name__ == "__main__":
    keep_alive()
    print("WF Rahim Console: Super Advanced Shop Bot is running...")
    bot.infinity_polling()
