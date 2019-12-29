# -*- coding: utf-8 -*-

import requests
import json
import datetime
import os
import sys
import logging

import telegram
from telegram.error import TelegramError, Unauthorized, BadRequest, TimedOut, ChatMigrated, NetworkError
from telegram.ext import CommandHandler, MessageHandler
from telegram.ext import Dispatcher, Filters

FILE_TYPE = 'json'

# Constants for inline keyboard
KEYBOARD_BUTTONS = {
    'last': '1',
    'second': '2',
    'calendar': '3'
}

# Constants for Keyboard layer
KEYBOARD_LAYER = {
    'top': 1
}

# Error constants
error = {
    'common': 'An error occurred',
    'os_err': 'An OS error occurred'
}


def main():

    try:

        config = get_config(os.path.abspath(os.path.dirname(__file__)))
        logging.info(f'Path to the data file: {config["data_path"]}')
        logging.info(f'Name of the data file: {config["data_file"]}')

        updater = telegram.ext.Updater(
            get_bot_token(), use_context=True)

        updater.dispatcher.add_handler(CommandHandler('start', handler_start))
        updater.dispatcher.add_handler(
            telegram.ext.CallbackQueryHandler(handler_button))
        #updater.dispatcher.add_handler(CommandHandler('help', handler_help))
        updater.dispatcher.add_error_handler(handler_error)

        updater.start_polling()
        updater.idle()

        # mosaic_blog_today =

    except Exception as err:
        logging.error(f'{error["common"]}: {err}')


def get_bot_token() -> str:

    try:
        token_filename = f'{os.path.abspath(os.path.dirname(__file__))}/bot_token'
        with open(token_filename) as token_file:
            token = token_file.readline()
            token_file.close()

        return(str(token))

    except OSError as err:
        logging.error(f'{error["os_err"]}: {err}')
        sys.exit()

    except:
        logging.error(error['common'])
        sys.exit()


def data_read_blog_from_file(config: dict) -> dict:

    try:

        data_filename = f'{config["data_path"]}/{config["data_file"]}.{FILE_TYPE}'

        with open(data_filename) as data_file:
            logging.info(f'File {data_filename} opened')

            mosaic_data = json.load(data_file)
            data_file.close()
            logging.info('JSON data loaded')

            return(mosaic_data['blog'])

    except OSError as err:
        logging.error(f'{error["os_err"]}: {err}')
        sys.exit()

    except:
        logging.error(error['common'])
        sys.exit()


def handler_start(my_update: telegram.update, the_context: telegram.ext.CallbackContext):

    config = get_config(os.path.abspath(os.path.dirname(__file__)))

    user_language = get_language_code(my_update.effective_user)

    message_title = get_message_text('start_message_title', user_language)
    message_text = get_message_text('start_message_text', user_language)

    my_update.effective_chat.bot.send_message(
        my_update.effective_chat.id, text=f'*{message_title}*', parse_mode='Markdown', disable_web_page_preview=True)

    my_update.effective_chat.bot.send_photo(
        my_update.effective_chat.id, photo=open(config['start_image'], 'rb'), parse_mode='Markdown')

    my_update.effective_chat.bot.send_message(
        my_update.effective_chat.id, text=f'{message_text}', parse_mode='Markdown',
        disable_web_page_preview=True)

    keyboard_send(my_update, KEYBOARD_LAYER['top'])


def handler_button(my_update: telegram.update, the_context: telegram.ext.CallbackContext):

    pressed_button = my_update.callback_query.data

    user_language = get_language_code(my_update.callback_query.from_user)

    if pressed_button == KEYBOARD_BUTTONS['last']:
        blog_entry = get_blog_entry_latest(int(KEYBOARD_BUTTONS['last']))

    elif pressed_button == KEYBOARD_BUTTONS['second']:
        blog_entry = get_blog_entry_latest(int(KEYBOARD_BUTTONS['second']))

    message = blog_entry_create(user_language, blog_entry)

    blog_entry_send(my_update, message)


def handler_error(my_update: telegram.update, the_context: telegram.ext.CallbackContext):

    logging.error('Update "%s" caused error "%s"',
                  my_update, the_context.error)


def keyboard_send(my_update: telegram.update, layer: int):

    user_language = get_language_code(my_update.effective_user)

    bot_keyboard = telegram.InlineKeyboardMarkup(
        create_inline_keyboard(user_language, layer))
        
    my_update.effective_chat.bot.send_message(
        my_update.effective_chat.id, text=f'*{get_message_text("keyboard", user_language)}*', parse_mode='Markdown',
        reply_markup=bot_keyboard, disable_web_page_preview=True)


def create_inline_keyboard(language: str, layer: int) -> list:

    if layer == KEYBOARD_LAYER['top']:
        keyboard = [[get_keyboard_button(KEYBOARD_BUTTONS['last'], language),
            get_keyboard_button(KEYBOARD_BUTTONS['second'], language)]]

    return(keyboard)


def get_keyboard_button(button_type: str, language: str) -> telegram.InlineKeyboardButton:

    try:
        message_filename = f'{os.path.abspath(os.path.dirname(__file__))}/messages.json'
        with open(message_filename) as message_file:
            messages = json.load(message_file)
            message_file.close()

        buttons = messages['buttons']

        return(telegram.InlineKeyboardButton(buttons[button_type][language], callback_data=button_type))

    except OSError as err:
        logging.error(f'{error["os_err"]}: {err}')

    except:
        logging.error(error['common'])


def blog_entry_create(language: str, blog_entry: dict) -> dict:

    message = {'date': blog_entry['date'],
               'title': blog_entry[f'title_{language}'],
               'text': blog_entry[f'text_{language}'],
               'media_type': blog_entry['media_type']
               }

    if blog_entry['media_type'].lower() == 'image':
        message.update({'image_url': blog_entry['image']['url']})
        message.update({'image_caption': blog_entry['image']['caption']})

    elif blog_entry['media_type'].lower() == 'video':
        message.update({'video_url': blog_entry[f'video_{language}']['url']})
        message.update(
            {'video_title': blog_entry[f'video_{language}']['title']})

    return(message)


def blog_entry_send(my_update: telegram.update, message: dict):

    current_chat = my_update.effective_chat

    current_chat.bot.send_message(current_chat.id, text=f'*{message["date"]} {message["title"]}*',
                                  parse_mode='Markdown', disable_web_page_preview=True)

    if message['media_type'].lower() == 'image':
        current_chat.bot.send_photo(
            current_chat.id, message['image_url'], caption=message['image_caption']
        )

    elif message['media_type'].lower() == 'video':
        current_chat.bot.send_video(
            current_chat.id, message['video_url'], caption=message['video_title']
        )

    current_chat.bot.send_message(current_chat.id, text=message['text'],
                                  parse_mode='Markdown', disable_web_page_preview=True)

    keyboard_send(my_update, KEYBOARD_LAYER['top'])


def get_language_code(user: telegram.User) -> str:

    if user.language_code.lower() == 'de':
        return('de')

    else:
        return('en')


def get_blog_entry_by_date(date: str) -> dict:

    try:
        config = get_config(os.path.abspath(os.path.dirname(__file__)))

        mosaic_blog = data_read_blog_from_file(config)

        for entry in mosaic_blog:
            if entry['date'] == date:
                return(entry)

            return('')

    except OSError as err:
        logging.error(f'{error["os_err"]}: {err}')

    except:
        logging.error(error['common'])


def get_blog_entry_latest(mode: int) -> dict:

    try:
        config = get_config(os.path.abspath(os.path.dirname(__file__)))

        mosaic_blog = data_read_blog_from_file(config)
        
        if mode == int(KEYBOARD_BUTTONS['last']):
            requested_date = datetime.date.today()

        elif mode == int(KEYBOARD_BUTTONS['second']):
            requested_date = datetime.date.today() - datetime.timedelta(days=1)

        latest_entry = None

        for blog_entry in mosaic_blog:
            blog_entry_date = datetime.datetime.strptime(
                blog_entry['date'], '%Y-%m-%d').date()
            if blog_entry_date == requested_date:
                latest_entry = blog_entry
                break

            else:

                if blog_entry_date < requested_date and latest_entry == None:
                    latest_entry = blog_entry

                elif blog_entry_date < requested_date and blog_entry_date > datetime.datetime.strptime(latest_entry['date'], '%Y-%m-%d').date():
                    latest_entry = blog_entry

        return(latest_entry)

    except OSError as err:
        logging.error(f'{error["os_err"]}: {err}')

    except:
        logging.error(error['common'])


def get_message_text(message_type: str, language: str) -> str:

    try:
        message_filename = f'{os.path.abspath(os.path.dirname(__file__))}/messages.json'
        with open(message_filename) as message_file:
            messages = json.load(message_file)
            message_file.close()

            return(messages['messages'][message_type][language])

    except OSError as err:
        logging.error(f'{error["os_err"]}: {err}')
        sys.exit()

    except:
        logging.error(error['common'])
        sys.exit()


def get_config(script_path: str) -> dict:

    try:
        config_file_name = f'{script_path}/config.json'

        with open(config_file_name) as config_file:
            config_data = json.load(config_file)
            config_file.close()

            return(config_data)

    except Exception as err:
        logging.error(f'{error["common"]}: {err}')
        sys.exit()


logging.basicConfig(
    format='%(asctime)s - %(funcName)s - %(message)s', level=logging.DEBUG)

if __name__ == '__main__':
    main()
