import os
import urllib.parse
import telebot
from telebot import types
from flask import Flask
from threading import Thread

TOKEN = "8858854627:AAHeJbgMFU_9cxmtnZyisRwzmmJ8UB1JIWI"
ADMIN_ID = 8454171811

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

@app.route('/')
def home():
    return "Jahid Hassan Bot is Active 24/7!"

users_data = {}
all_users = set()
withdraw_temp = {}  # ইউজারের সাময়িক ডেটা জমানোর জন্য

CHANNEL_USERNAME = "@wf_rahim_69_ff"
GROUP_USERNAME = "@public_group_chate"

CHANNEL_LINK = "https://t.me/wf_rahim_69_ff"
GROUP_LINK = "https://t.me/public_group_chate"

def is_user_joined(user_id):
    if user_id == ADMIN_ID:
        return True
    try:
        ch_member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        grp_member = bot.get_chat_member(GROUP_USERNAME, user_id)
        
        ch_ok = ch_member.status in ['member', 'administrator', 'creator']
        grp_ok = grp_member.status in ['member', 'administrator', 'creator']
        
        return ch_ok and grp_ok
    except Exception as e:
        print(f"Check Member Error: {e}")
        return False

@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    all_users.add(user_id)
    
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

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📢 ১নং চ্যানেল জয়েন করুন", url=CHANNEL_LINK),
        types.InlineKeyboardButton("💬 ২নং গ্রুপ জয়েন করুন", url=GROUP_LINK),
        types.InlineKeyboardButton("✅ ভেরিফাই করুন", callback_data="verify_membership")
    )
    
    bot.send_message(
        message.chat.id,
        f"✨ **স্বাগতম, {first_name}!**\n\nবটটি সম্পূর্ণ ব্যবহারের জন্য আমাদের চ্যানেল ও গ্রুপে জয়েন করে নিচের **ভেরিফাই করুন** বাটনে ক্লিক করুন। 👇",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "verify_membership")
def verify_callback(call):
    user_id = call.from_user.id
    first_name = call.from_user.first_name
    
    if is_user_joined(user_id):
        referrer_id = users_data[user_id].get('referred_by')
        if referrer_id and referrer_id in users_data and not users_data[user_id]['bonus_given']:
            users_data[referrer_id]['balance'] += 20.0
            users_data[user_id]['bonus_given'] = True
            
            users_data[referrer_id]['referrals'].append({
                'name': first_name,
                'id': user_id,
                'username': call.from_user.username
            })
            
            try:
                bot.send_message(referrer_id, f"🎉 অভিনন্দন! আপনার রেফারকৃত ইউজার {first_name} ভেরিফাই সম্পন্ন করেছেন। আপনি ২০ টাকা বোনাস পেয়েছেন।")
            except Exception:
                pass

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("💰 আমার ব্যালেন্স", "👥 রেফার করুন")
        markup.row("📤 উইথড্র (Withdraw)", "ℹ️ নিয়মাবলী")
        if user_id == ADMIN_ID:
            markup.row("⚙️ এডমিন প্যানেল")
        
        bot.answer_callback_query(call.id, "✅ ভেরিফিকেশন সফল হয়েছে!")
        bot.send_message(
            call.message.chat.id,
            "🚀 **ভেরিফিকেশন সফল!**\n\nনিচের মেনু থেকে আপনার পছন্দমত অপশন বেছে নিন:",
            parse_mode="Markdown",
            reply_markup=markup
        )
    else:
        bot.answer_callback_query(call.id, "❌ আপনি এখনও চ্যানেল বা গ্রুপে জয়েন করেননি!", show_alert=True)

# ----------------- এডমিন প্যানেল -----------------

@bot.message_handler(func=lambda message: message.text == "⚙️ এডমিন প্যানেল" and message.from_user.id == ADMIN_ID)
def admin_panel(message):
    admin_markup = types.InlineKeyboardMarkup(row_width=2)
    admin_markup.add(
        types.InlineKeyboardButton("📊 মোট ইউজার", callback_data="admin_stats"),
        types.InlineKeyboardButton("📢 ব্রডকাস্ট মেসেজ", callback_data="admin_broadcast"),
        types.InlineKeyboardButton("➕ ব্যালেন্স দিন", callback_data="admin_addbal"),
        types.InlineKeyboardButton("➖ ব্যালেন্স কাটুন", callback_data="admin_cutbal")
    )
    bot.send_message(message.chat.id, "👑 **এডমিন কন্ট্রোল প্যানেল**", reply_markup=admin_markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def admin_callbacks(call):
    if call.from_user.id != ADMIN_ID:
        return
        
    if call.data == "admin_stats":
        bot.send_message(call.message.chat.id, f"📈 **মোট ইউজার:** `{len(all_users)}` জন", parse_mode="Markdown")
        
    elif call.data == "admin_broadcast":
        msg = bot.send_message(call.message.chat.id, "📢 ব্রডকাস্ট মেসেজটি লিখুন (যা সবার কাছে যাবে):")
        bot.register_next_step_handler(msg, process_broadcast)

    elif call.data == "admin_addbal":
        msg = bot.send_message(call.message.chat.id, "➕ টাকা দিতে লিখুন: `আইডি পরিমাণ` (যেমন: `8454171811 50`)", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_addbal)

    elif call.data == "admin_cutbal":
        msg = bot.send_message(call.message.chat.id, "➖ টাকা কাটতে লিখুন: `আইডি পরিমাণ` (যেমন: `8454171811 20`)", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_cutbal)

def process_broadcast(message):
    count = 0
    for u_id in all_users:
        try:
            bot.send_message(u_id, f"📢 **এডমিন নোটিশ:**\n\n{message.text}", parse_mode="Markdown")
            count += 1
        except Exception:
            pass
    bot.send_message(message.chat.id, f"✅ সফলভাবে `{count}` জন ইউজারের কাছে মেসেজ পাঠানো হয়েছে!")

def process_addbal(message):
    try:
        u_id, amount = map(float, message.text.split())
        u_id = int(u_id)
        if u_id in users_data:
            users_data[u_id]['balance'] += amount
            bot.send_message(message.chat.id, f"✅ ইউজার `{u_id}`-কে ৳`{amount}` টাকা ব্যালেন্স যুক্ত করা হয়েছে।", parse_mode="Markdown")
            try:
                bot.send_message(u_id, f"🎉 এডমিন আপনার অ্যাকাউন্টে ৳`{amount}` টাকা যুক্ত করেছেন!")
            except Exception:
                pass
        else:
            bot.send_message(message.chat.id, "❌ ইউজার খুঁজে পাওয়া যায়নি!")
    except Exception:
        bot.send_message(message.chat.id, "❌ ভুল ফরম্যাট! সঠিকভাবে লিখুন।")

def process_cutbal(message):
    try:
        u_id, amount = map(float, message.text.split())
        u_id = int(u_id)
        if u_id in users_data:
            users_data[u_id]['balance'] -= amount
            bot.send_message(message.chat.id, f"✅ ইউজার `{u_id}` থেকে ৳`{amount}` টাকা কেটে নেওয়া হয়েছে।", parse_mode="Markdown")
            try:
                bot.send_message(u_id, f"⚠️ এডমিন আপনার অ্যাকাউন্ট থেকে ৳`{amount}` টাকা কেটে নিয়েছেন।")
            except Exception:
                pass
        else:
            bot.send_message(message.chat.id, "❌ ইউজার খুঁজে পাওয়া যায়নি!")
    except Exception:
        bot.send_message(message.chat.id, "❌ ভুল ফরম্যাট! সঠিকভাবে লিখুন।")

# ----------------- সাধারণ ইউজার হ্যান্ডলার -----------------

@bot.message_handler(func=lambda message: True)
def user_handlers(message):
    user_id = message.from_user.id
    text = message.text
    all_users.add(user_id)

    if not is_user_joined(user_id):
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("📢 ১নং চ্যানেল জয়েন করুন", url=CHANNEL_LINK),
            types.InlineKeyboardButton("💬 ২নং গ্রুপ জয়েন করুন", url=GROUP_LINK),
            types.InlineKeyboardButton("✅ ভেরিফাই করুন", callback_data="verify_membership")
        )
        bot.send_message(message.chat.id, "⚠️ বট ব্যবহারের জন্য আপনাকে অবশ্যই আমাদের চ্যানেল ও গ্রুপে জয়েন করতে হবে!", reply_markup=markup)
        return

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
            f"👤 **আপনার অ্যাকাউন্ট বিবরণী:**\n\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"💰 **বর্তমান ব্যালেন্স:** ৳{bal} টাকা\n"
            f"👥 **সফল রেফারেল:** {ref_count} জন\n"
            f"━━━━━━━━━━━━━━━━━━━",
            parse_mode="Markdown"
        )
        
    elif text == "👥 রেফার করুন":
        bot_name = bot.get_me().username
        ref_link = f"https://t.me/{bot_name}?start=ref_{user_id}"
        
        share_text = (
            f"🔥 এখনই জয়েন করুন এবং রেফার করে প্রতিদিন টাকা ইনকাম করুন!\n\n"
            f"👇 জয়েন লিংক:\n"
            f"{ref_link}"
        )
        
        share_url = f"https://t.me/share/url?url=&text={urllib.parse.quote(share_text)}"
        
        share_markup = types.InlineKeyboardMarkup()
        share_markup.add(types.InlineKeyboardButton("🔗 শেয়ার করুন (Share)", url=share_url))
        
        msg_text = (
            f"🔗 **আপনার ব্যক্তিগত রেফার লিংক:**\n\n"
            f"`{ref_link}`\n\n"
            f"📢 প্রতি সফল রেফারে পাবেন **২০ টাকা** বোনাস!\n"
            f"👇 বন্ধুদের কাছে পাঠাতে নিচের **শেয়ার করুন** বাটনে চাপ দিন।"
        )
        
        bot.send_message(
            message.chat.id,
            msg_text,
            parse_mode="Markdown",
            reply_markup=share_markup
        )
        
    elif text == "📤 উইথড্র (Withdraw)":
        withdraw_markup = types.InlineKeyboardMarkup(row_width=2)
        withdraw_markup.add(
            types.InlineKeyboardButton("💵 বিকাশ (Bkash)", callback_data="withdraw_bkash"),
            types.InlineKeyboardButton("📱 নগদ (Nagad)", callback_data="withdraw_nagad")
        )
        bot.send_message(
            message.chat.id,
            "💸 **পেমেন্ট মেথড নির্বাচন করুন:**\n\nআপনি কোন মাধ্যমে টাকা নিতে চান তা নিচের বাটন থেকে সিলেক্ট করুন। 👇",
            parse_mode="Markdown",
            reply_markup=withdraw_markup
        )
            
    elif text == "ℹ️ নিয়মাবলী":
        bot.send_message(
            message.chat.id,
            "📜 **বট ব্যবহারের নিয়মাবলী:**\n\n"
            "১. আমাদের চ্যানেল ও গ্রুপে অবশ্যই জয়েন থাকতে হবে।\n"
            "২. প্রতি রেফারে পাবেন **২০ টাকা** বোনাস।\n"
            "৩. সর্বনিম্ন **১০০০ টাকা** হলে বিকাশ বা নগদে উইথড্র করতে পারবেন।",
            parse_mode="Markdown"
        )

# ----------------- ধাপভিত্তিক উইথড্র প্রসেসিং -----------------

@bot.callback_query_handler(func=lambda call: call.data.startswith("withdraw_"))
def withdraw_method_callback(call):
    user_id = call.from_user.id
    method = "বিকাশ (Bkash)" if call.data == "withdraw_bkash" else "নগদ (Nagad)"
    
    withdraw_temp[user_id] = {'method': method}
    
    msg = bot.send_message(
        call.message.chat.id,
        f"✅ আপনি **{method}** সিলেক্ট করেছেন।\n\n"
        f"📱 এখন আপনার সঠিক **বিকাশ/নগদ অ্যাকাউন্ট নম্বরটি** লিখে পাঠান:",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, get_withdraw_number)

def get_withdraw_number(message):
    user_id = message.from_user.id
    phone_number = message.text.strip()
    
    if user_id not in withdraw_temp:
        bot.send_message(message.chat.id, "❌ সময়সীমা শেষ! দয়া করে আবার উইথড্র মেনুতে যান।")
        return
        
    withdraw_temp[user_id]['phone'] = phone_number
    
    bal = users_data[user_id]['balance']
    msg = bot.send_message(
        message.chat.id,
        f"💳 আপনার নম্বর: `{phone_number}`\n\n"
        f"💰 আপনার বর্তমান ব্যালেন্স: ৳`{bal}` টাকা\n\n"
        f"💵 এখন আপনি কত টাকা উইথড্র করতে চান তা **সংখ্যার মাধ্যমে** লিখে পাঠান:\n"
        f"*(যেমন: `1000` বা `1500`)*",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, get_withdraw_amount)

def get_withdraw_amount(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username if message.from_user.username else "নেই"
    
    if user_id not in withdraw_temp:
        bot.send_message(message.chat.id, "❌ একটি সমস্যা হয়েছে! দয়া করে আবার চেষ্টা করুন।")
        return
        
    method = withdraw_temp[user_id]['method']
    phone_number = withdraw_temp[user_id]['phone']
    bal = users_data[user_id]['balance']
    
    try:
        amount = float(message.text.strip())
        
        # সর্বনিম্ন ১০০০ টাকা না হলে ব্যর্থ মেসেজ এবং এডমিন নোটিফিকেশন
        if amount < 1000:
            bot.send_message(
                message.chat.id,
                f"❌ **উইথড্র ব্যর্থ হয়েছে!**\n\nসর্বনিম্ন **১০০০ টাকা** হলে উইথড্র করতে পারবেন।\n• আপনি দিতে চেয়েছেন: ৳`{amount}`\n• আপনার বর্তমান ব্যালেন্স: ৳`{bal}`",
                parse_mode="Markdown"
            )
            failed_notice = (
                f"⚠️ **ব্যর্থ উইথড্র চেষ্টা!**\n\n"
                f"👤 **ইউজার:** {first_name}\n"
                f"🆔 **আইডি:** `{user_id}`\n"
                f"🏷️ **ইউজারনেম:** @{username}\n"
                f"💳 **মেথড:** {method}\n"
                f"📞 **নম্বর:** `{phone_number}`\n"
                f"💵 **চেষ্টা করা পরিমাণ:** ৳`{amount}` (১০০০ এর কম)\n"
                f"💰 **বর্তমান ব্যালেন্স:** ৳`{bal}`"
            )
            bot.send_message(ADMIN_ID, failed_notice, parse_mode="Markdown")
            return

        if amount > bal:
            bot.send_message(
                message.chat.id,
                f"❌ **পর্যাপ্ত ব্যালেন্স নেই!**\n\nআপনার অ্যাকাউন্টে আছে ৳`{bal}` টাকা, কিন্তু আপনি উইথড্র করতে চাচ্ছেন ৳`{amount}` টাকা।",
                parse_mode="Markdown"
            )
            return

        # সফল উইথড্র প্রসেস
        users_data[user_id]['balance'] -= amount
        
        bot.send_message(
            message.chat.id,
            f"🎉 **উইথড্র রিকোয়েস্ট সফলভাবে জমা হয়েছে!**\n\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"💳 **মেথড:** {method}\n"
            f"📞 **নম্বর:** `{phone_number}`\n"
            f"💵 **পরিমাণ:** ৳`{amount}` টাকা\n"
            f"📌 **স্ট্যাটাস:** পেন্ডিং (Pending)\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
            f"এডমিন খুব শীঘ্রই আপনার পেমেন্টটি চেক করে পাঠিয়ে দেবেন। ধন্যবাদ!",
            parse_mode="Markdown"
        )
        
        success_notice = (
            f"🚨 **নতুন উইথড্র রিকোয়েস্ট!**\n\n"
            f"👤 **ইউজার:** {first_name}\n"
            f"🆔 **আইডি:** `{user_id}`\n"
            f"🏷️ **ইউজারনেম:** @{username}\n"
            f"💳 **মেথড:** {method}\n"
            f"📞 **নম্বর:** `{phone_number}`\n"
            f"💰 **উইথড্র পরিমাণ:** ৳`{amount}` টাকা\n"
            f"📉 **অবশিষ্ট ব্যালেন্স:** ৳`{users_data[user_id]['balance']}` টাকা"
        )
        bot.send_message(ADMIN_ID, success_notice, parse_mode="Markdown")
        
    except Exception:
        bot.send_message(
            message.chat.id,
            "❌ **ভুল পরিমাণ!** দয়া করে শুধু সঠিক সংখ্যায় টাকার পরিমাণ লিখুন (যেমন: `1000`)।",
            parse_mode="Markdown"
        )

def run_bot():
    bot.infinity_polling(timeout=20, long_polling_timeout=20)

t = Thread(target=run_bot)
t.daemon = True
t.start()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
