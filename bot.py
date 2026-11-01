import glob
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.request import HTTPXRequest
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes


# Set up logging to monitor output in console
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# /start විධානය මඟින් ප්‍රධාන මෙනුව පෙන්වීම (Private හෝ Group කොතැනක දැමුවත් DM එකට හෝ Chat එකට වැඩ කරයි)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("⭐ Zendaya", callback_data="menu_zendaya")],
        [InlineKeyboardButton("⭐ Emma Watson", callback_data="menu_emma")],
        [InlineKeyboardButton("⭐ Taylor Swift", callback_data="menu_taylor")],
        [InlineKeyboardButton("⭐ පියුමාලි එදිරිසිංහ", callback_data="menu_piyumali")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # ගෘප් එකකදී වුණත් කෙනෙක් start කළොත් ඊට අදාළව පිළිතුරු දීම
    target_chat_id = update.effective_chat.id
    
    await context.bot.send_message(
        chat_id=target_chat_id,
        text="✨ **Please select who you'd like (Celebrity crush):**",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# උප මෙනුව (Sub-menu) පෙන්වීම - මෙය ක්ලික් කළ පුද්ගලයාගේ DM (Private Chat) වෙත යැවීමට සකසා ඇත
async def show_celebrity_submenu(update: Update, context: ContextTypes.DEFAULT_TYPE, celeb_name: str):
    query = update.callback_query
    user_id = query.from_user.id  
    
    context.user_data['current_celeb'] = celeb_name
    context.user_data[f'{celeb_name}_index'] = 0  
    
    keyboard = [
        [InlineKeyboardButton("📸 Get Single Photo", callback_data=f"single_{celeb_name}")],
        [InlineKeyboardButton(f"🖼️ Gallery", callback_data=f"gallery_{celeb_name}")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # සිංහල හෝ වෙනත් නම් සමඟ ඇති වන ගැටළු මඟහරවා ගැනීමට parse_mode ඉවත් කර ඇත
    try:
        await query.message.edit_text(
            f"✨ You selected {celeb_name.capitalize()}! Please choose an option:",
            reply_markup=reply_markup
        )
    except Exception:
        await query.message.delete()
        await context.bot.send_message(
            chat_id=user_id,
            text=f"✨ You selected {celeb_name.capitalize()}! Please choose an option:",
            reply_markup=reply_markup
        )

# තනි පින්තූරයක් පෙන්වීම (ක්ලික් කළ කෙනාගේ Private Chat / DM වෙත යැවීම සඳහා user_id පාවිච්චි කරයි)
async def send_single_photo(update: Update, context: ContextTypes.DEFAULT_TYPE, celeb_name: str):
    query = update.callback_query
    user_id = query.from_user.id  # ක්ලික් කළ තැනැත්තාගේ ID එක
    
    folder_path = os.path.join(os.getcwd(), celeb_name)
    image_files = sorted(glob.glob(os.path.join(folder_path, 'photo*.jpg')), key=lambda name: int(''.join(filter(str.isdigit, name))))
    
    if not image_files:
        image_files = sorted(glob.glob(f'{celeb_name}*.jpg'))
        
    if not image_files:
        await context.bot.send_message(chat_id=user_id, text=f"No photos found for {celeb_name}!")
        return

    index_key = f'{celeb_name}_index'
    if index_key not in context.user_data:
        context.user_data[index_key] = 0

    current_index = context.user_data[index_key]
    img_path = image_files[current_index]

    keyboard = [
        [InlineKeyboardButton("⏭️ Get Next Photo", callback_data=f"single_{celeb_name}")],
        [InlineKeyboardButton("🔙 Back to Sub-menu", callback_data=f"menu_{celeb_name}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    with open(img_path, 'rb') as photo:
        # පින්තූරය ගෘප් එකේ පෙන්වන්නේ නැතුව, ක්ලික් කළ කෙනාගේ DM (user_id) එකට පමණක් යවයි
        await context.bot.send_photo(
            chat_id=user_id,
            photo=photo,
            caption=f"❤️ {celeb_name.capitalize()} ({current_index + 1} of {len(image_files)})",
            reply_markup=reply_markup
        )

    context.user_data[index_key] = (current_index + 1) % len(image_files)

# සම්පූර්ණ ගැලරිය පෙන්වීම (ක්ලික් කළ කෙනාගේ DM එකට පමණක් යැවීම)
async def send_gallery(update: Update, context: ContextTypes.DEFAULT_TYPE, celeb_name: str):
    query = update.callback_query
    user_id = query.from_user.id
    
    folder_path = os.path.join(os.getcwd(), celeb_name)
    image_files = sorted(glob.glob(os.path.join(folder_path, 'photo*.jpg')), key=lambda name: int(''.join(filter(str.isdigit, name))))
    
    if not image_files:
        image_files = sorted(glob.glob(f'{celeb_name}*.jpg'))

    if not image_files:
        await context.bot.send_message(chat_id=user_id, text=f"No photos found for {celeb_name} gallery!")
        return

    # සියලුම පින්තූර අදාළ පුද්ගලයාගේ Private DM එකට පමණක් එකින් එක යැවීම
    for img_path in image_files:
        with open(img_path, 'rb') as photo:
            await context.bot.send_photo(
                chat_id=user_id,
                photo=photo,
                caption=f"{celeb_name.capitalize()} Gallery Photo"
            )

    keyboard = [
        [InlineKeyboardButton("📸 Get Single Photo", callback_data=f"single_{celeb_name}")],
        [InlineKeyboardButton(f"🖼️ {celeb_name.capitalize()} Gallery", callback_data=f"gallery_{celeb_name}")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=user_id,
        text=f"✨ You selected **{celeb_name.capitalize()}**! Please choose an option:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# බොත්තම් ක්ලික් කිරීම් පාලනය කිරීම
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() # Telegram වෙත loading සංඥාව ඉවත් කිරීමට
    
    data = query.data
    
    if data.startswith("menu_"):
        celeb_name = data.replace("menu_", "")
        await show_celebrity_submenu(update, context, celeb_name)
    elif data.startswith("single_"):
        celeb_name = data.replace("single_", "")
        await send_single_photo(update, context, celeb_name)
    elif data.startswith("gallery_"):
        celeb_name = data.replace("gallery_", "")
        await send_gallery(update, context, celeb_name)
    elif data == "back_to_main":
        user_id = query.from_user.id
        keyboard = [
            [InlineKeyboardButton("⭐ Zendaya", callback_data="menu_zendaya")],
            [InlineKeyboardButton("⭐ Emma Watson", callback_data="menu_emma")],
            [InlineKeyboardButton("⭐ Taylor Swift", callback_data="menu_taylor")],
            [InlineKeyboardButton("⭐ පියුමාලි එදිරිසිංහ", callback_data="menu_piyumali")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            await query.message.edit_text(
                "✨ **Please select who you'd like (Celebrity crush):**",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        except Exception:
            await context.bot.send_message(
                chat_id=user_id,
                text="✨ **Please select who you'd like (Celebrity crush):**",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )

# Telegram චැට් එකේ Menu එක ක්ලික් කළ විට /start විධානය පමණක් පෙන්වීම
async def post_init(application: ApplicationBuilder):
    commands = [
        BotCommand("start", "Start the bot and choose celebrity crush"),
    ]
    await application.bot.set_my_commands(commands)

def main():
    BOT_TOKEN = "9203764858:AAGWQL9gZncmHFTNDXW-Nrw8gHp5mQq7q5U"

    custom_request = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=30.0
    )

    app = (
    ApplicationBuilder()
    .token("9203764858:AAGWQL9gZncmHFTNDXW-Nrw8gHp5mQq7q5U")
    .read_timeout(30)
    .write_timeout(30)
    .connect_timeout(30)
    .pool_timeout(30)
    .build()
)
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot is running with private DM responses for groups...")
    app.run_polling()

if __name__ == '__main__':
    main()
