import asyncio
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, ApplicationBuilder, ContextTypes
import requests

from config import *

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="I'm a bot, please talk to me!"
    )
WAITING_FOR_TEXT = "waiting_for_text"
async def start_comment_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data[WAITING_FOR_TEXT] = True
    await update.message.reply_text('Пожалуйста, отправьте текст, который будет нв стикере')
    
async def comment_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get(WAITING_FOR_TEXT):
        text = update.message.text
        user = update.message.from_user
        comment_text = f"Комментарий от {user.first_name} {user.last_name}: {text}"
        # Miro API endpoint for creating a comment
        url = f"https://api.miro.com/v2/boards/{MIRO_BOARD_ID}/sticky_notes"
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {MIRO_API_TOKEN}"
        }
        payload = {
            "data": {
                "content": comment_text
            }
    }
        response = requests.post(url, headers=headers, json=payload)
        print(response)
        if response.status_code == 201:
            await update.message.reply_text('Стикер успешно создан в Miro.')
        else:
            await update.message.reply_text('Произошла ошибка при создании стикера')
    context.user_data[WAITING_FOR_TEXT] = False
        
WAITING_FOR_PHOTO = "waiting_for_photo"
async def start_photo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /photo, который запрашивает фото."""
    context.user_data[WAITING_FOR_PHOTO] = True
    await update.message.reply_text('Пожалуйста, отправьте фото, чтобы я мог загрузить его на Miro.')

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get(WAITING_FOR_PHOTO):
        try:
            message: Message = update.message
            print(f"Получено сообщение: {message}")

            # Проверка наличия фото
            if message.photo:
                photo_file = await message.photo[-1].get_file()
                photo_bytes = await photo_file.download_as_bytearray()
                print("Фото успешно загружено")
             
                # Подготовка запроса к Miro API
                url = f"https://api.miro.com/v2/boards/{MIRO_BOARD_ID}/images"
                headers = {
                    "accept": "application/json",
                    "authorization": f"Bearer {MIRO_API_TOKEN}"
                }
                files = {
                    "resource": ('image.jpg', photo_bytes, 'image/jpeg')
                }

                # Отправка запроса
                response = requests.post(url, files=files, headers=headers)
                print(f"Ответ от Miro API: {response.status_code}")

                if response.status_code == 201:
                    await message.reply_text('Фотография успешно добавлена на доску Miro.')
                
                else:
                    await message.reply_text(f'Произошла ошибка при добавлении фотографии: {response.text}')
                context.user_data[WAITING_FOR_PHOTO] = False
            else:
                await message.reply_text('Пожалуйста, отправьте фото.')

        except: 
            pass

def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    comment_handler = CommandHandler('comment', start_comment_command)
    application.add_handler(start_handler)
    application.add_handler( comment_handler)

    photo_command_handler = CommandHandler("photo", start_photo_command)
    application.add_handler(photo_command_handler)
    photo_handler = MessageHandler(filters.PHOTO, handle_photo)
    handler_comment = MessageHandler(filters.TEXT, comment_command)
    application.add_handler(photo_handler)
    application.add_handler(handler_comment)
    application.run_polling()

if __name__ == '__main__':
    main()
   
