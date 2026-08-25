import os
import urllib.parse
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
    return "Jahid Hassan Bot is Active 24/7!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ডেটাবেজ
users_data = {}
all_users = set()

# গ্রুপ ও চ্যানেল ইউজারনেম (@ সহ)
CHANNEL_USERNAME = "@wf_rahim_69_ff"
GROUP_USERNAME = "@public_group_chate"

CHANNEL_LINK = "https://t.me/wf_rahim_69_ff"
GROUP_LINK = "https://t.me/public_group_chate"

def is_user_joined(user_id):
    """ টেলিগ্রামের মাধ্যমে চেক করবে ইউজার গ্রুপে ও চ্যানেলে আছে কিনা """
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
        f"স্বাগতম {first_name}!\n\nবটটি ব্যবহার করতে আমাদের চ্যানেল ও গ্রুপে জয়েন করে **ভেরিফাই করুন** বাটনে চাপ দিন।",
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
            
            ref_msg = (
                f"🔔 **নতুন রেফার জয়েন করেছে!**\n\n"
                f"👤 **রেফারকারী (Referrer):**\n"
                f"• আইডি: `{referrer_id}`\n\n"
                f"📥 **নতুন ইউজার:**\n"
                f"• নাম: {first_name}\n"
                f"• আইডি: `{user_id}`\n"
                f"• ইউজারনেম: @{call.from_user.username if call.from_user.username else 'নেই'}\n\n"
                f"💰 রেফারকারী ২০ টাকা বোনাস পেয়েছেন।"
            )
            try:
                bot.send_message(ADMIN_ID, ref_msg, parse_mode="Markdown")
                bot.send_message(referrer_id, f"🎉 আপনার রেফারকৃত ইউজার {first_name} ভেরিফাই সম্পন্ন করেছেন! আপনি ২০ টাকা বোনাস পেয়েছেন।")
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
            "✅ আপনার ভেরিফিকেশন সফল হয়েছে! নিচের মেনু থেকে অপশন নির্বাচন করুন:",
            reply_markup=markup
        )
    else:
        bot.answer_callback_query(call.id, "❌ আপনি এখনও গ্রুপ বা চ্যানেলে জয়েন করেননি!", show_alert=True)

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
        bot.send_message(call.message.chat.id, f"📈 **মোট ইউজার:** {len(all_users)} জন", parse_mode="Markdown")
        
    elif call.data == "admin_broadcast":
        msg = bot.send_message(call.message.chat.id, "📢 ব্রডকাস্ট মেসেজটি লিখুন:")
        bot.register_next_step_handler(msg, process_broadcast)

    elif call.data == "admin_addbal":
        msg = bot.send_message(call.message.chat.id, "➕ টাকা দিতে লিখুন: `আইডি পরিমাণ` (যেমন: `123456 50`)", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_addbal)

    elif call.data == "admin_cutbal":
        msg = bot.send_message(call.message.chat.id, "➖ টাকা কাটতে লিখুন: `আইডি পরিমাণ`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_cutbal)

def process_broadcast(message):
    count = 0
    for u_id in all_users:
        try:
            bot.send_message(u_id, f"📢 **এডমিন মেসেজ:**\n\n{message.text}", parse_mode="Markdown")
            count += 1
        except Exception:
            pass
    bot.send_message(message.chat.id, f"✅ {count} জনের কাছে পাঠানো হয়েছে!")

def process_addbal(message):
    try:
        u_id, amount = map(float, message.text.split())
        u_id = int(u_id)
        if u_id in users_data:
            users_data[u_id]['balance'] += amount
            bot.send_message(message.chat.id, f"✅ ইউজার `{u_id}`-কে ৳{amount} টাকা দেওয়া হয়েছে।", parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, "❌ ইউজার খুঁজে পাওয়া যায়নি!")
    except Exception:
        bot.send_message(message.chat.id, "❌ ভুল ফরম্যাট!")

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
        bot.send_message(message.chat.id, "❌ ভুল ফরম্যাট!")

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
            f"👤 **অ্যাকাউন্ট বিবরণী:**\n\n💰 বর্তমান ব্যালেন্স: ৳{bal} টাকা\n👥 সফল রেফারেল: {ref_count} জন",
            parse_mode="Markdown"
        )
        
    elif text == "👥 রেফার করুন":
        bot_name = bot.get_me().username
        ref_link = f"https://t.me/{bot_name}?start=ref_{user_id}"
        
        # অটোমেটিক ফ্রেন্ড লিস্টে শেয়ার হওয়ার বাটন
        share_text = f"🔥 এখনই জয়েন করুন এবং রেফার করে প্রতিদিন টাকা ইনকাম করুন!\n\n👇 জয়েন লিংক:"
        share_url = f"https://t.me/share/url?url={urllib.parse.quote(ref_link)}&text={urllib.parse.quote(share_text)}"
        
        share_markup = types.InlineKeyboardMarkup()
        share_markup.add(types.InlineKeyboardButton("🔗 শেয়ার করুন (Share)", url=share_url))
        
        msg_text = (
            f"🔗 **আপনার রেফার লিংক:**\n\n"
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
        bal = users_data[user_id]['balance']
        if bal >= 1000:
            bot.send_message(
                message.chat.id,
                "✅ আপনার উইথড্র রিকোয়েস্ট জমা নেওয়া হয়েছে! এডমিন খুব শীঘ্রই চেক করবেন।"
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
            "📜 **নিয়মাবলী:**\n\n১. চ্যানেল ও গ্রুপে জয়েন থাকা বাধ্যতামূলক।\n২. প্রতি রেফারে ২০ টাকা বোনাস পাবেন।\n৩. ১০০০ টাকা হলে উইথড্র করা যাবে।"
        )

if __name__ == '__main__':
    keep_alive()
    bot.infinity_polling()
