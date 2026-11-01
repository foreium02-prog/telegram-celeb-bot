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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        
        [InlineKeyboardButton("⭐ පියුමාලි එදිරිසිංහ", callback_data="menu_piyumali")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    target_chat_id = update.effective_chat.id
    
    await context.bot.send_message(
        chat_id=target_chat_id,
        text="✨ **Please select who you'd like (Celebrity crush):**",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

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


async def send_single_photo(update: Update, context: ContextTypes.DEFAULT_TYPE, celeb_name: str):
    query = update.callback_query
    user_id = query.from_user.id  
    
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
        await context.bot.send_photo(
            chat_id=user_id,
            photo=photo,
            caption=f"❤️ {celeb_name.capitalize()} ({current_index + 1} of {len(image_files)})",
            reply_markup=reply_markup
        )

    context.user_data[index_key] = (current_index + 1) % len(image_files)


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


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
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
            await context.post.send_message(
                chat_id=user_id,
                text="✨ **Please select who you'd like (Celebrity crush):**",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )

async def post_init(application: ApplicationBuilder):
    commands = [
        BotCommand("start", "Start the bot and choose celebrity crush"),
    ]
    await application.bot.set_my_commands(commands)

def main():
    
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN environment variable not set!")
        return

    custom_request = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0,
        pool_timeout=30.0
    )

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .request(custom_request)
        .post_init(post_init)
        .build()
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot is running safely...")
    app.run_polling()

if __name__ == '__main__':
    main()
