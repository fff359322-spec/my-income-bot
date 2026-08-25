import os
import telebot
from telebot import types
from flask import Flask
from threading import Thread

# আপনার টেলিগ্রাম বট টোকেন এবং এডমিন আইডি
TOKEN = "8858854627:AAHeJbgMFU_9cxmtnZyisRwzmmJ8UB1JIWI"
ADMIN_ID = 8454171811  # Jahid Hassan

bot = telebot.TeleBot(TOKEN)
app = Flask('')

@app.route('/')
def home():
    return "Jahid Hassan Console: Bot is running..."

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ইউজার ডেটা সংরক্ষণের জন্য সহজ ডিকশনারি (টেম্পোরারি)
users_data = {}

# গ্রুপ লিংক
GROUP_1 = "https://t.me/wf_rahim_69_ff"
GROUP_2 = "https://t.me/public_group_chate"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    if user_id not in users_data:
        users_data[user_id] = {
            'balance': 0.0,
            'referred_by': None,
            'referrals': []
        }
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("📢 ১নং গ্রুপে জয়েন করুন", url=GROUP_1)
    btn2 = types.InlineKeyboardButton("📢 ২নং গ্রুপে জয়েন করুন", url=GROUP_2)
    btn_verify = types.InlineKeyboardButton("✅ ভেরিফাই করুন", callback_data="verify_join")
    markup.add(btn1, btn2, btn_verify)
    
    bot.send_message(
        message.chat.id,
        f"স্বাগতম {user_name}!\n\nবট ব্যবহারের জন্য প্রথমে নিচের দুটি গ্রুপে জয়েন করুন এবং তারপর ভেরিফাই বাটনে ক্লিক করুন।",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "verify_join")
def verify_join(call):
    user_id = call.from_user.id
    
    # এখানে চাইলে ইউজারের গ্রুপ মেম্বারশিপ চেক করার কোড বসানো যায়, আপাতত সিম্পল ভেরিফিকেশন রাখা হলো
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("💰 ব্যালেন্স", "👥 রেফার করুন")
    markup.add("📤 উইথড্র (Withdraw)", "ℹ️ নিয়মাবলী")
    
    bot.answer_callback_query(call.id, "ভেরিফিকেশন সফল হয়েছে!")
    bot.send_message(
        call.message.chat.id,
        "অভিনন্দন! আপনার অ্যাকাউন্ট ভেরিফাইড হয়েছে। এখন নিচের মেনু থেকে কাজ করতে পারেন:",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    text = message.text
    
    if user_id not in users_data:
        users_data[user_id] = {'balance': 0.0, 'referrals': []}
        
    if text == "💰 ব্যালেন্স":
        bal = users_data[user_id]['balance']
        bot.send_message(message.chat.id, f"আপনার বর্তমান ব্যালেন্স: ৳{bal}")
        
    elif text == "👥 রেফার করুন":
        ref_link = f"https://t.me/{bot.get_me().username}?start=ref_{user_id}"
        bot.send_message(
            message.chat.id,
            f"আপনার রেফার লিংক:\n{ref_link}\n\nপ্রতিটি রেফারে পাবেন ২০ টাকা করে বোনাস!"
        )
        
    elif text == "📤 উইথড্র (Withdraw)":
        bal = users_data[user_id]['balance']
        if bal >= 1000:
            bot.send_message(message.chat.id, "আপনার উইথড্র রিকোয়েস্ট সফলভাবে জমা হয়েছে। এডমিন শীঘ্রই আপনার পেমেন্ট চেক করবেন।")
            # এডমিনকে নোটিফিকেশন পাঠানো
            bot.send_message(ADMIN_ID, f"🚨 নতুন উইথড্র রিকোয়েস্ট!\nইউজার আইডি: {user_id}\nটাকা: ৳{bal}")
        else:
            needed = 1000 - bal
            bot.send_message(message.chat.id, f"❌ উইথড্র করতে হলে আপনার কমপক্ষে ১০০০ টাকা হতে হবে। আপনার আর মাত্র ৳{needed} প্রয়োজন।")
            
    elif text == "ℹ️ নিয়মাবলী":
        bot.send_message(message.chat.id, "নিয়মাবলী:\n১. দুটি গ্রুপে জয়েন বাধ্যতামূলক।\n২. প্রতি রেফারে ২০ টাকা বোনাস।\n৩. ন্যূনতম ১০০০ টাকা হলে উইথড্র করতে পারবেন।")

if __name__ == '__main__':
    keep_alive()
    bot.infinity_polling()
