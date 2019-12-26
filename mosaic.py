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
LAST = "last"
YESTERDAY = 2

# Constants for Keyboard layer
TOP = 1


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
        logging.error(f'An error occurred: {err}')


def get_bot_token() -> str:

    try:
        token_filename = f'{os.path.abspath(os.path.dirname(__file__))}/bot_token'
        with open(token_filename) as token_file:
            token = token_file.readline()
            token_file.close()

        return(str(token))
    
    except OSError as err:
        logging.error(f'An OS error occurred: {err}')
        sys.exit()

    except:
        logging.error('An error occurred')
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
        logging.error(f'An OS error occurred: {err}')
        sys.exit()

    except:
        logging.error('An error occurred')
        sys.exit()


def handler_start(my_update: telegram.update, the_context: telegram.ext.CallbackContext):

    user_language = my_update.effective_user.language_code

    bot_keyboard = telegram.InlineKeyboardMarkup(
        create_inline_keyboard(user_language, TOP))

    message_title = get_message_text('start_message_title', user_language)
    message_text = get_message_text('start_message_text', user_language)

    my_update.effective_chat.bot.send_message(
        my_update.effective_chat.id, text=f'*{message_title}*', parse_mode='Markdown', disable_web_page_preview=True)

    my_update.effective_chat.bot.send_photo(
        my_update.effective_chat.id, 'blob:https://web.telegram.org/c801a070-d67f-4c1c-964a-19a082ae7414', parse_mode='Markdown')

    my_update.effective_chat.bot.send_message(
        my_update.effective_chat.id, text=f'*{message_text}*', parse_mode='Markdown',
        reply_markup=bot_keyboard, disable_web_page_preview=True)


def create_inline_keyboard(language: str, layer: int) -> list:

    if layer == TOP:
        keyboard = [[get_keyboard_button(LAST, language)]]

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
        logging.error(f'An OS error occurred: {err}')
        sys.exit()

    except:
        logging.error('An error occurred')
        sys.exit()


def handler_button(my_update: telegram.update, the_context: telegram.ext.CallbackContext):

    pressed_button = my_update.callback_query.data

    user_language = get_language_code(my_update.callback_query.from_user)

    if pressed_button == str(LAST):
        blog_entry = get_blog_entry_by_date(str(datetime.date.today()))

        message = message_create(user_language, blog_entry)

        message_send(my_update, message)


def handler_error(my_update: telegram.update, the_context: telegram.ext.CallbackContext):

    logging.error('Update "%s" caused error "%s"',
                  my_update, the_context.error)


def message_create(language: str, blog_entry: dict) -> dict:

    message = {'date': blog_entry['date'],
               'title': blog_entry[f'title_{language}'],
               'text': blog_entry[f'text_{language}'],
               'image_url': blog_entry['image']['url'],
               'image_caption': blog_entry['image']['caption']}

    return(message)


def message_send(my_update: telegram.update, message: dict):

    user_language = get_language_code(my_update.effective_user)

    bot_keyboard = telegram.InlineKeyboardMarkup(
        create_inline_keyboard(user_language, TOP))

    query = my_update.callback_query

    query.bot.send_message(query.message.chat_id, text=f'*{message["date"]} {message["title"]}*',
                           parse_mode='Markdown', disable_web_page_preview=True)

    if len(message['image_url']) > 0:
        query.bot.send_photo(
            query.message.chat_id, message['image_url'], caption=message['image_caption'])

    query.bot.send_message(query.message.chat_id, text=message['text'], reply_markup=bot_keyboard,
                           parse_mode='Markdown', disable_web_page_preview=True)


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
        logging.error(f'An OS error occurred: {err}')

    except:
        logging.error('An error occurred')


def get_blog_latest(today: str) -> dict:

    try:
        config = get_config(os.path.abspath(os.path.dirname(__file__)))

        mosaic_blog = data_read_blog_from_file(config)

    except OSError as err:
        logging.error(f'An OS error occurred: {err}')

    except:
        logging.error('An error occurred')


def get_language_from_user(my_update: telegram.update) -> str:

    language = 'DE'
    return(language)


def get_message_text(message_type: str, language: str) -> str:

    try:
        message_filename = f'{os.path.abspath(os.path.dirname(__file__))}/messages.json'
        with open(message_filename) as message_file:
            messages = json.load(message_file)
            message_file.close()

            return(messages['messages'][message_type][language])

    except OSError as err:
        logging.error(f'An OS error occurred: {err}')
        sys.exit()

    except:
        logging.error('An error occurred')
        sys.exit()


def get_config(script_path: str) -> dict:

    try:
        config_file_name = f'{script_path}/config.json'

        with open(config_file_name) as config_file:
            config_data = json.load(config_file)
            config_file.close()

            return(config_data)

    except Exception as err:
        logging.error(f'An error occurred: {err}')
        sys.exit()


logging.basicConfig(
    format='%(asctime)s - %(funcName)s - %(message)s', level=logging.DEBUG)

if __name__ == '__main__':
    main()
