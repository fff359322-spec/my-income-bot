import os
import telebot
from telebot import types
from flask import Flask
from threading import Thread

# কনফিগারেশন
TOKEN = "8858854627:AAHeJbgMFU_9cxmtnZyisRwzmmJ8UB1JIWI"
ADMIN_ID = 8454171811  # Jahid Hassan

bot = telebot.TeleBot(TOKEN)
app = Flask('')

@app.route('/')
def home():
    return "Jahid Hassan Bot is Running 24/7!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ইউজার ডেটা স্টোর করার ডাটাবেজ/ডিকশনারি
users_data = {}

CHANNEL_1 = "https://t.me/wf_rahim_69_ff"
GROUP_2 = "https://t.me/public_group_chate"

@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    
    # রেফারেল হ্যান্ডেল করা
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
        
        # যদি কেউ রেফার করে থাকে এবং এটি নতুন ইউজার হয়
        if referrer_id and referrer_id in users_data:
            if not users_data[user_id]['bonus_given']:
                users_data[referrer_id]['balance'] += 20.0
                users_data[user_id]['bonus_given'] = True
                
                # রেফারের ডিটেইলস ইউজারের লিস্টে যোগ করা
                users_data[referrer_id]['referrals'].append({
                    'name': first_name,
                    'id': user_id,
                    'username': message.from_user.username
                })
                
                # এডমিনকে নোটিফিকেশন পাঠানো (রেফার দাতা ও নতুন ইউজারের নাম-ডিটেইলসসহ)
                ref_msg = (
                    f"🔔 **নতুন রেফার জয়েন করেছে!**\n\n"
                    f"👤 **রেফারকারী (Referrer):**\n"
                    f"• আইডি: `{referrer_id}`\n\n"
                    f"📥 **নতুন সদস্য (New User):**\n"
                    f"• নাম: {first_name}\n"
                    f"• আইডি: `{user_id}`\n"
                    f"• ইউজারনেম: @{message.from_user.username if message.from_user.username else 'নেই'}\n\n"
                    f"💰 রেফারকারী ২০ টাকা বোনাস পেয়েছে!"
                )
                try:
                    bot.send_message(ADMIN_ID, ref_msg, parse_mode="Markdown")
                except Exception:
                    pass

    # জয়েন করার জন্য বাটন
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📢 চ্যানেল জয়েন করুন", url=CHANNEL_1),
        types.InlineKeyboardButton("💬 গ্রুপ জয়েন করুন", url=GROUP_2),
        types.InlineKeyboardButton("✅ ভেরিফাই করুন", callback_data="verify_membership")
    )
    
    bot.send_message(
        message.chat.id,
        f"স্বাগতম {first_name} ভাই!\n\nবটটি ব্যবহার করতে প্রথমে আমাদের চ্যানেল ও গ্রুপে জয়েন করুন, তারপর নিচের **ভেরিফাই করুন** বাটনে ক্লিক করুন।",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data == "verify_membership")
def verify_callback(call):
    user_id = call.from_user.id
    
    # মূল মেনু কিবোর্ড
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("💰 আমার ব্যালেন্স", "👥 রেফার করুন")
    markup.row("📤 উইথড্র (Withdraw)", "ℹ️ নিয়মাবলী")
    
    bot.answer_callback_query(call.id, "ভেরিফিকেশন সফল হয়েছে!")
    bot.send_message(
        call.message.chat.id,
        "✅ আপনার ভেরিফিকেশন সফল হয়েছে! এখন নিচের মেনু থেকে অপশনগুলো ব্যবহার করুন:",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: True)
def main_handler(message):
    user_id = message.from_user.id
    text = message.text
    
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
            f"👤 একাউন্ট স্ট্যাটাস:\n\n💰 বর্তমান ব্যালেন্স: ৳{bal} টাকা\n👥 মোট সফল রেফার: {ref_count} জন"
        )
        
    elif text == "👥 রেফার করুন":
        bot_username = bot.get_me().username
        ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
        bot.send_message(
            message.chat.id,
            f"🔗 আপনার রেফার লিংক:\n`{ref_link}`\n\n📢 প্রতি রেফারে আপনি পাবেন **২০ টাকা** করে বোনাস!\nবন্ধুদের মাঝে শেয়ার করুন।",
            parse_mode="Markdown"
        )
        
    elif text == "📤 উইথড্র (Withdraw)":
        bal = users_data[user_id]['balance']
        if bal >= 1000:
            bot.send_message(
                message.chat.id,
                "✅ আপনার উইথড্র রিকোয়েস্ট সফলভাবে জমা হয়েছে! এডমিন খুব শীঘ্রই পেমেন্ট চেক করে পাঠিয়ে দেবেন।"
            )
            # এডমিনকে উইথড্র নোটিফিকেশন পাঠানো
            admin_withdraw_msg = (
                f"🚨 **নতুন উইথড্র রিকোয়েস্ট!**\n\n"
                f"👤 নাম: {message.from_user.first_name}\n"
                f"🆔 আইডি: `{user_id}`\n"
                f"💰 পরিমাণ: ৳{bal} টাকা"
            )
            bot.send_message(ADMIN_ID, admin_withdraw_msg, parse_mode="Markdown")
        else:
            needed = 1000 - bal
            bot.send_message(
                message.chat.id,
                f"❌ উইথড্র করতে হলে আপনার অ্যাকাউন্টে কমপক্ষে **১০০০ টাকা** থাকতে হবে!\n\n"
                f"• আপনার বর্তমান ব্যালেন্স: ৳{bal} টাকা\n"
                f"• আরও প্রয়োজন: ৳{needed} টাকা"
            )
            
    elif text == "ℹ️ নিয়মাবলী":
        bot.send_message(
            message.chat.id,
            "📜 **বটের নিয়মাবলী:**\n\n"
            "১. চ্যানেল ও গ্রুপে জয়েন করে ভেরিফাই করা বাধ্যতামূলক।\n"
            "২. প্রতি রেফারে ২০ টাকা ক্যাশ বোনাস পাবেন।\n"
            "৩. ব্যালেন্স ন্যূনতম ১০০০ টাকা হলে উইথড্র করতে পারবেন।"
        )

if __name__ == '__main__':
    keep_alive()
    bot.infinity_polling()
