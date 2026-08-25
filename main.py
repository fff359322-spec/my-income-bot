elif text == "👥 রেফার করুন":
        bot_name = bot.get_me().username
        ref_link = f"https://t.me/{bot_name}?start=ref_{user_id}"
        
        # শেয়ার করার মেসেজের টেক্সট (উপরে লেখা, নিচে লিংক)
        share_text = f"🔥 এখনই জয়েন করুন এবং রেফার করে প্রতিদিন টাকা ইনকাম করুন!\n\n👇 জয়েন লিংক:\n{ref_link}"
        
        # টেলিগ্রাম শেয়ার URL (urllib.parse ব্যবহার করে এনকোড করা)
        share_url = f"https://t.me/share/url?url=&text={urllib.parse.quote(share_text)}"
        
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
