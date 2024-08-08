
import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from telegram.ext import CommandHandler, MessageHandler, filters, ApplicationBuilder, ContextTypes, CallbackQueryHandler
import requests, re
from config import *
from constants import sticker_colors
import random
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="I'm a bot, please talk to me!"
    )
    
WAITING_FOR_TEXT = "waiting_for_text"
WAITING_FOR_PHOTO = "waiting_for_photo"

async def start_comment_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data[WAITING_FOR_TEXT] = True
    await update.message.reply_text('Отправьте текст в формате <сообщение> -c <цвет стикера>')

async def action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = "https://randomall.ru/api/gens/3441"
    headers = {
        "Content-Type": "application/json"
    }
    data = {}
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        await update.message.reply_text(result['msg'])
    else:
        print(f"Error: {response.status_code}, {response.text}")

async def facts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = "https://randomall.ru/api/gens/3674"
    headers = {
        "Content-Type": "application/json"
    }
    data = {}
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        await update.message.reply_text(result['msg'])
    else:
        print(f"Error: {response.status_code}, {response.text}")

async def comment_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get(WAITING_FOR_TEXT) and update.message.text[0] != '/':
        pattern = re.compile(r'^(.*?)\s*-c\s*(\S+)$')
        match = pattern.match(update.message.text)
        if match:
            text = match.group(1).strip()
            color = match.group(2).strip()
            if color not in sticker_colors: color = 'light_yellow'
        else:
            text =  update.message.text
            color = 'light_yellow'
        user = update.message.from_user
        comment_text = f"Комментарий от {user.first_name} {user.last_name}: {text}"
        ID1 = BOARDS[0]["id"]
        url = f"https://api.miro.com/v2/boards/{ID1}/sticky_notes"
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {MIRO_API_TOKEN}"
        }

        
        payload = {
            "data": {
                "content": comment_text
            },
            "style" : {
                "fillColor": color
            }, 
            "position": {
                "x": 2000+random.random()*1000,
                "y": 2000+random.random()*1000
            }
    }
        response = requests.post(url, headers=headers, json=payload)
        print(response)
        if response.status_code == 201:
            await update.message.reply_text('Стикер успешно создан в Miro.')
        else:
            await update.message.reply_text('Произошла ошибка при создании стикера')
    context.user_data[WAITING_FOR_TEXT] = False
        
async def color_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = "Доступные цвета:\n"
    for color in sticker_colors:
        message += f"- {color}\n"
    await update.message.reply_text(message)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = "Действие было отменено"
    context.user_data[WAITING_FOR_TEXT] = False
    context.user_data[WAITING_FOR_PHOTO] = False
    await update.message.reply_text(message)


async def start_photo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(board["name"], callback_data=board["id"])] for board in BOARDS]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Выберите доску для загрузки фото:', reply_markup=reply_markup)

async def select_board(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    board_id = query.data
    print(query)
    print(board_id)
    context.user_data["selected_board_id"] = board_id
    context.user_data[WAITING_FOR_PHOTO] = True
    await query.answer()
    await query.edit_message_text('Доска выбрана. Пожалуйста, отправьте фото.')


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get(WAITING_FOR_PHOTO):
        try:
            message = update.message
            if message.photo:
                photo = message.photo[-1]
                photo_file = await photo.get_file()
                file_url = photo_file.file_path
                selected_board_id = context.user_data.get("selected_board_id")

                if not selected_board_id:
                    await message.reply_text('Не выбрана доска. Пожалуйста, начните сначала.')
                    return

                miro_url = f"https://api.miro.com/v2/boards/{selected_board_id}/images"
                headers = {
                    "accept": "application/json",
                    "authorization": f"Bearer {MIRO_API_TOKEN}"
                }

                data = {
                    "data": {
                        "title": "Sample image title",
                        "url": file_url
                    },
                    "position": {
                        "x": 2000 + random.random() * 1000,
                        "y": 2000 + random.random() * 1000
                    }
                }
                
                response = requests.post(miro_url, headers=headers, json=data)
                if response.status_code == 201:
                    await message.reply_text('Фотография успешно добавлена на доску Miro.')
                else:
                    await message.reply_text(f'Произошла ошибка при добавлении фотографии: {response.text}')
                
                context.user_data[WAITING_FOR_PHOTO] = False
            else:
                await message.reply_text('Пожалуйста, отправьте фото.')

        except Exception as e:
            await message.reply_text(f'Произошла ошибка: {e}')

def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    cancel_handler = CommandHandler('cancel', cancel)
    action_handler = CommandHandler('action', action)
    facts_handler = CommandHandler('facts', facts)
    comment_handler = CommandHandler('comment', start_comment_command)
    application.add_handler(start_handler)
    application.add_handler(cancel_handler)
    application.add_handler( comment_handler)
    application.add_handler(action_handler)
    application.add_handler(facts_handler)



    photo_command_handler = CommandHandler("photo", start_photo_command)
    application.add_handler(photo_command_handler)
    application.add_handler(CallbackQueryHandler(select_board))
    photo_handler = MessageHandler(filters.PHOTO, handle_photo)
    handler_comment = MessageHandler(filters.TEXT, comment_command)
    
    color_hangler = CommandHandler("color", color_command)
    application.add_handler(color_hangler)

    application.add_handler(photo_handler)
    application.add_handler(handler_comment)
    application.run_polling()

if __name__ == '__main__':
    main()
   
