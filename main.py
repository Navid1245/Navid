import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Updater,
    CallbackContext,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler,
)
import logging
from flask import Flask
import threading

# اطلاعات ربات
TOKEN = '8119410307:AAF7uNxE1vM_TqdjjXJiA4nuh408MlqlQrI'
ADMIN_ID = 859497308  # 

# لیست کاربران بلاک‌شده
blocked_users = set()

# ذخیره پیام‌هایی که بهشون پاسخ داده میشه
reply_mapping = {}

# تنظیم لاگ
logging.basicConfig(level=logging.INFO)

# ساخت بات
bot = telegram.Bot(token=TOKEN)
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

# وب‌سرور برای روشن نگه‌داشتن ربات
app = Flask(__name__)

@app.route('/')
def index():
    return 'Bot is running!'

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# مدیریت استارت
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        update.message.reply_text(
            "خوش اومدی نوید ☀️\n\nبا این دو تا گزینه می‌تونی ربات رو مدیریت کنی:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("لیست بلاکی‌ها 🔒", callback_data="show_blocks")]
            ])
        )
    else:
        update.message.reply_text("پیامت ارسال شد ✅")
        if user_id in blocked_users:
            update.message.reply_text("شما متاسفانه بلاک شدید و پیامتون ارسال نشد❌")
            return
        username = update.effective_user.username
        name = update.effective_user.full_name
        user_link = f"@{username}" if username else f"<a href='tg://user?id={user_id}'>{name}</a>"

        context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📨 پیام جدید از {user_link}",
            parse_mode='HTML'
        )
        context.bot.send_message(
            chat_id=ADMIN_ID,
            text=update.message.text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("پاسخ🟢", callback_data=f"reply_{user_id}"),
                 InlineKeyboardButton("بلاک🔴", callback_data=f"block_{user_id}")]
            ])
        )

# مدیریت پیام‌ها
def handle_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        update.message.reply_text("برای پاسخ به پیام، از دکمه پاسخ استفاده کن.")
        return
    if user_id in blocked_users:
        update.message.reply_text("شما متاسفانه بلاک شدید و پیامتون ارسال نشد❌")
        return

    update.message.reply_text("پیامت ارسال شد ✅")

    username = update.effective_user.username
    name = update.effective_user.full_name
    user_link = f"@{username}" if username else f"<a href='tg://user?id={user_id}'>{name}</a>"

    context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📨 پیام جدید از {user_link}",
        parse_mode='HTML'
    )
    msg = context.bot.send_message(
        chat_id=ADMIN_ID,
        text=update.message.text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("پاسخ🟢", callback_data=f"reply_{user_id}"),
             InlineKeyboardButton("بلاک🔴", callback_data=f"block_{user_id}")]
        ])
    )
    reply_mapping[user_id] = msg.message_id

# مدیریت کلیک روی دکمه‌ها
def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    data = query.data

    if data.startswith("reply_"):
        target_id = int(data.split("_")[1])
        context.user_data["reply_to"] = target_id
        query.message.reply_text("متن پاسخ‌تو بفرست (یا عکس/ویس/ویدیو...)")

    elif data.startswith("block_"):
        blocked_id = int(data.split("_")[1])
        blocked_users.add(blocked_id)
        query.message.reply_text("کاربر با موفقیت بلاک شد ✅")

    elif data.startswith("unblock_"):
        unblocked_id = int(data.split("_")[1])
        blocked_users.discard(unblocked_id)
        context.bot.send_message(chat_id=unblocked_id,
                                 text="شما از بلاک خارج شدید و می‌تونید از این به بعد به نوید پیام بدید 🤝")
        query.message.reply_text("کاربر از بلاک خارج شد ✅")

    elif data == "show_blocks":
        if not blocked_users:
            query.message.reply_text("هیچ کاربری بلاک نیست.")
        else:
            for uid in blocked_users:
                try:
                    user = bot.get_chat(uid)
                    username = user.username
                    name = user.full_name
                    user_link = f"@{username}" if username else f"<a href='tg://user?id={uid}'>{name}</a>"
                    context.bot.send_message(
                        chat_id=ADMIN_ID,
                        text=f"شخص با آیدی زیر توسط شما بلاک شده:\n{user_link}",
                        parse_mode='HTML',
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("خارج کردن از بلاک", callback_data=f"unblock_{uid}")]
                        ])
                    )
                except:
                    continue

# مدیریت پاسخ ادمین
def admin_response(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return

    if "reply_to" in context.user_data:
        target_id = context.user_data["reply_to"]
        del context.user_data["reply_to"]
        context.bot.send_message(chat_id=target_id, text="نوید جوابتو داد 👇")
        sent_msg = context.bot.send_message(chat_id=target_id, text=update.message.text,
                                            reply_markup=InlineKeyboardMarkup([
                                                [InlineKeyboardButton("پاسخ🟢", callback_data=f"reply_{ADMIN_ID}")]
                                            ]))
        reply_mapping[target_id] = sent_msg.message_id
        update.message.reply_text("پیامت ارسال شد ✅")
    else:
        update.message.reply_text("ابتدا روی دکمه «پاسخ» کلیک کن.")

# راه‌اندازی هندلرها
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CallbackQueryHandler(button_handler))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
dispatcher.add_handler(MessageHandler(Filters.text & Filters.user(user_id=ADMIN_ID), admin_response))

# شروع سرور تلگرام و فل ask
threading.Thread(target=run_flask).start()
updater.start_polling()
