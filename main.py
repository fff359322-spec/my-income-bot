elif text == "👥 রেফার করুন":
        bot_name = bot.get_me().username
        ref_link = f"https://t.me/{bot_name}?start=ref_{user_id}"
        
        # শেয়ার ইনলাইন বাটন তৈরি
        share_markup = types.InlineKeyboardMarkup()
        share_url = f"https://t.me/share/url?url={ref_link}&text=এই%20বট%20থেকে%20রেফার%20করে%20টাকা%20ইনকাম%20করুন!"
        share_btn = types.InlineKeyboardButton("🚀 শেয়ার করুন (Share)", url=share_url)
        share_markup.add(share_btn)
        
        # লিংক ফরম্যাট ও মেসেজ
        msg_text = (
            f"🔗 **আপনার রেফার লিংক:**\n"
            f"[এখানে ক্লিক করে কপি করুন]({ref_link})\n\n"
            f"`{ref_link}`\n\n"
            f"📢 প্রতি সফল রেফারে পাবেন **২০ টাকা** বোনাস!"
        )
        
        bot.send_message(
            message.chat.id,
            msg_text,
            parse_mode="Markdown",
            reply_markup=share_markup,
            disable_web_page_preview=True
        )
