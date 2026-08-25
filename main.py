import os
import telebot
from telebot import types
from flask import Flask
from threading import Thread

# কনফিগারেশন
TOKEN = "8858854627:AAHeJbgMFU_9cxmtnZyisRwzmmJ8UB1JIWI"
ADMIN_ID = 8454171811  # Jahid Hassan Admin ID

bot = telebot.TeleBot(TOKEN)
app = Flask('')

@app.route('/')
def home():
    return "Jahid Hassan Admin Panel Bot is Active 24/7!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ডেটাবেজ (ইউজার ও সিস্টেম সেটিংস)
users_data = {}
all_users = set()

CHANNEL_1 = "https://t.me/wf_rahim_69_ff"
GROUP_2 = "https://t.me/public_group_chate"

@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    all_users.add(user_id)
    
    # রেফারেল প্রসেস
    text_parts = message.text.split()
    referrer_id = None
    if len(text_parts) > 1 and text_parts[1].startswith("ref_"):
        try:
            ref_id = int(text_parts[1].replace("ref_", ""))
            if ref_id != user_id:
                referrer_id = ref_id
        except ValueError:
            pass

    if user_id not in users_data:
        users_data[user_id] = {
            'first_name': first_name,
            'username': message.from_user.username,
            'balance': 0.0,
            'referrals': [],
            'referred_by': referrer_id,
            'bonus_given': False
        }
        
        if referrer_id and referrer_id in users_data:
            if not users_data[user_id]['bonus_given']:
                users_data[referrer_id]['balance'] += 20.0
                users_data[user_id]['bonus_given'] = True
                
                users_data[referrer_id]['referrals'].append({
                    'name': first_name,
                    'id': user_id,
                    'username': message.from_user.username
                })
                
                # এডমিন নোটিফিকেশন
                ref_msg = (
                    f"🔔 **নতুন রেফার রেজিস্টার হয়েছে!**\n\n"
                    f"👤 **রেফারকারী (Referrer):**\n"
                    f"• আইডি: `{referrer_id}`\n\n"
                    f"📥 **নতুন ইউজার:**\n"
                    f"• নাম: {first_name}\n"
                    f"• আইডি: `{user_id}`\n"
                    f"• ইউজারনেম: @{message.from_user.username if message.from_user.username else 'নেই'}\n\n"
                    f"💰 রেফারকারীকে ২০ টাকা বোনাস দেওয়া হয়েছে।"
                )
                try:
                    bot.send_message(ADMIN_ID, ref_msg, parse_mode="Markdown")
                except Exception:
                    pass

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📢 ১নং গ্রুপ/চ্যানেল জয়েন করুন", url=CHANNEL_1),
        types.InlineKeyboardButton("💬 ২নং গ্রুপ জয়েন করুন", url=GROUP_2),
        types.InlineKeyboardButton("✅ ভেরিফাই করুন", callback_data="verify_membership")
    )
    
    bot.send_message(
        message.chat.id,
        f"স্বাগতম {first_name}!\n\nবটটি ব্যবহার করতে নিচের গ্রুপ দুটিতে জয়েন করে **ভেরিফাই করুন** বাটনে চাপ দিন।",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "verify_membership")
def verify_callback(call):
    user_id = call.from_user.id
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("💰 আমার ব্যালেন্স", "👥 রেফার করুন")
    markup.row("📤 উইথড্র (Withdraw)", "ℹ️ নিয়মাবলী")
    
    # এডমিন হলে স্পেশাল বাটন দেখাবে
    if user_id == ADMIN_ID:
        markup.row("⚙️ এডমিন প্যানেল")
    
    bot.answer_callback_query(call.id, "ভেরিফিকেশন সফল হয়েছে!")
    bot.send_message(
        call.message.chat.id,
        "✅ আপনার একাউন্ট ভেরিফাইড! নিচের অপশন থেকে সার্ভিস ব্যবহার করুন:",
        reply_markup=markup
    )

# ----------------- এডমিন কমান্ড ও কন্ট্রোল -----------------

@bot.message_handler(func=lambda message: message.text == "⚙️ এডমিন প্যানেল" and message.from_user.id == ADMIN_ID)
def admin_panel(message):
    admin_markup = types.InlineKeyboardMarkup(row_width=2)
    admin_markup.add(
        types.InlineKeyboardButton("📊 মোট ইউজার", callback_data="admin_stats"),
        types.InlineKeyboardButton("📢 ব্রডকাস্ট মেসেজ", callback_data="admin_broadcast"),
        types.InlineKeyboardButton("➕ ব্যালেন্স দিন", callback_data="admin_addbal"),
        types.InlineKeyboardButton("➖ ব্যালেন্স কাটুন", callback_data="admin_cutbal")
    )
    bot.send_message(
        message.chat.id,
        "👑 **এডমিন কন্ট্রোল প্যানেল**\n\nএখান থেকে আপনি বটের সব কার্যকলাপ পরিচালনা করতে পারবেন:",
        reply_markup=admin_markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def admin_callbacks(call):
    if call.from_user.id != ADMIN_ID:
        return
        
    if call.data == "admin_stats":
        total_u = len(all_users)
        bot.send_message(call.message.chat.id, f"📈 **বট স্ট্যাটাস:**\n\nমোট ইউজার সংখ্যা: **{total_u}** জন", parse_mode="Markdown")
        
    elif call.data == "admin_broadcast":
        msg = bot.send_message(call.message.chat.id, "📢 সব ইউজারের কাছে যে মেসেজটি পাঠাতে চান তা লিখে রিপ্লাই দিন:")
        bot.register_next_step_handler(msg, process_broadcast)

    elif call.data == "admin_addbal":
        msg = bot.send_message(call.message.chat.id, "➕ টাকা যোগ করতে এই ফরম্যাটে লিখুন:\n`ইউজার_আইডি পরিমাণ`\n\nউদাহরণ: `123456789 50`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_addbal)

    elif call.data == "admin_cutbal":
        msg = bot.send_message(call.message.chat.id, "➖ টাকা কাটতে এই ফরম্যাটে লিখুন:\n`ইউজার_আইডি পরিমাণ`\n\nউদাহরণ: `123456789 20`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_cutbal)

def process_broadcast(message):
    count = 0
    for u_id in all_users:
        try:
            bot.send_message(u_id, f"📢 **এডমিন মেসেজ:**\n\n{message.text}", parse_mode="Markdown")
            count += 1
        except Exception:
            pass
    bot.send_message(message.chat.id, f"✅ মোট {count} জন ইউজারের কাছে মেসেজ পাঠানো হয়েছে!")

def process_addbal(message):
    try:
        u_id, amount = map(float, message.text.split())
        u_id = int(u_id)
        if u_id in users_data:
            users_data[u_id]['balance'] += amount
            bot.send_message(message.chat.id, f"✅ ইউজার `{u_id}` কে ৳{amount} টাকা যোগ করা হয়েছে।", parse_mode="Markdown")
            bot.send_message(u_id, f"🎉 এডমিন আপনার ব্যালেন্সে ৳{amount} টাকা যোগ করেছেন!")
        else:
            bot.send_message(message.chat.id, "❌ ইউজার খুঁজে পাওয়া যায়নি!")
    except Exception:
        bot.send_message(message.chat.id, "❌ ভুল ফরম্যাট! আবার চেষ্টা করুন।")

def process_cutbal(message):
    try:
        u_id, amount = map(float, message.text.split())
        u_id = int(u_id)
        if u_id in users_data:
            users_data[u_id]['balance'] -= amount
            bot.send_message(message.chat.id, f"✅ ইউজার `{u_id}` থেকে ৳{amount} টাকা কাটা হয়েছে।", parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, "❌ ইউজার খুঁজে পাওয়া যায়নি!")
    except Exception:
        bot.send_message(message.chat.id, "❌ ভুল ফরম্যাট! আবার চেষ্টা করুন।")

# ----------------- সাধারণ ইউজার হ্যান্ডলার -----------------

@bot.message_handler(func=lambda message: True)
def user_handlers(message):
    user_id = message.from_user.id
    text = message.text
    all_users.add(user_id)
    
    if user_id not in users_data:
        users_data[user_id] = {
            'first_name': message.from_user.first_name,
            'username': message.from_user.username,
            'balance': 0.0,
            'referrals': [],
            'referred_by': None,
            'bonus_given': True
        }
    
    if text == "💰 আমার ব্যালেন্স":
        bal = users_data[user_id]['balance']
        ref_count = len(users_data[user_id]['referrals'])
        bot.send_message(
            message.chat.id,
            f"👤 **অ্যাকাউন্ট বিবরণী:**\n\n💰 বর্তমান ব্যালেন্স: ৳{bal} টাকা\n👥 সফল রেফারেল: {ref_count} জন",
            parse_mode="Markdown"
        )
        
    elif text == "👥 রেফার করুন":
        bot_name = bot.get_me().username
        ref_link = f"https://t.me/{bot_name}?start=ref_{user_id}"
        bot.send_message(
            message.chat.id,
            f"🔗 **আপনার রেফার লিংক:**\n`{ref_link}`\n\n📢 প্রতি সফল রেফারে পাবেন **২০ টাকা** বোনাস!",
            parse_mode="Markdown"
        )
        
    elif text == "📤 উইথড্র (Withdraw)":
        bal = users_data[user_id]['balance']
        if bal >= 1000:
            bot.send_message(
                message.chat.id,
                "✅ আপনার উইথড্র রিকোয়েস্ট জমা নেওয়া হয়েছে! এডমিন দ্রুত পেমেন্ট প্রসেস করবেন।"
            )
            bot.send_message(
                ADMIN_ID,
                f"🚨 **নতুন উইথড্র রিকোয়েস্ট!**\n\n👤 নাম: {message.from_user.first_name}\n🆔 আইডি: `{user_id}`\n💰 পরিমাণ: ৳{bal} টাকা",
                parse_mode="Markdown"
            )
        else:
            needed = 1000 - bal
            bot.send_message(
                message.chat.id,
                f"❌ উইথড্র করার জন্য আপনার ব্যালেন্সে কমপক্ষে **১০০০ টাকা** থাকতে হবে।\n\n• বর্তমান ব্যালেন্স: ৳{bal}\n• আরও প্রয়োজন: ৳{needed}",
                parse_mode="Markdown"
            )
            
    elif text == "ℹ️ নিয়মাবলী":
        bot.send_message(
            message.chat.id,
            "📜 **নিয়মাবলী:**\n\n১. গ্রুপে জয়েন থাকা বাধ্যতামূলক।\n২. প্রতি রেফারে ২০ টাকা বোনাস পাবেন।\n৩. ১০০০ টাকা হলে উইথড্র করা যাবে।"
        )

if __name__ == '__main__':
    keep_alive()
    bot.infinity_polling()
