# -*- coding: utf-8 -*-

import requests
import json
import datetime
import os
import sys
import logging
from logging.handlers import RotatingFileHandler

import telegram
from telegram.error import TelegramError, Unauthorized, BadRequest, TimedOut, ChatMigrated, NetworkError
from telegram.ext import CommandHandler, MessageHandler
from telegram.ext import Dispatcher, Filters

FILE_TYPE = 'json'

LOG_FILE = "mosaic_bot.log"

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
        my_logger.info(f'Path to the data file: {config["data_path"]}')
        my_logger.info(f'Name of the data file: {config["data_file"]}')

        my_logger.info(f'Start the bot updater')
        updater = telegram.ext.Updater(
            get_bot_token(), use_context=True)
        my_logger.info(f'Bot {updater.bot.name} started')

        my_logger.info(f'Adding the dispatchers')
        updater.dispatcher.add_handler(CommandHandler('start', handler_start))
        updater.dispatcher.add_handler(
            telegram.ext.CallbackQueryHandler(handler_button))
        #updater.dispatcher.add_handler(CommandHandler('help', handler_help))
        updater.dispatcher.add_error_handler(handler_error)
        my_logger.info(f'Dispatcher successfull added')

        my_logger.info(f'Starting bot poller')
        updater.start_polling()
        updater.idle()

        # mosaic_blog_today =

    except Exception as err:
        my_logger.error(f'{error["common"]}: {err}')


def get_bot_token() -> str:

    try:
        my_logger.info('Reading configuration')
        config = get_config(os.path.abspath(os.path.dirname(__file__)))

        my_logger.info(f'Token file: {config["token_filename"]}')
        with open(f'{config["token_filename"]}') as token_file:
            token = token_file.readline()
            token_file.close()
            my_logger.info(f'Token read from file')

        return(str(token))

    except OSError as err:
        my_logger.error(f'{error["os_err"]}: {err}')
        sys.exit()

    except:
        my_logger.error(error['common'])
        sys.exit()


def data_read_blog_from_file(config: dict) -> dict:

    try:

        data_filename = f'{config["data_path"]}/{config["data_file"]}.{FILE_TYPE}'

        my_logger.info(f'Opening the data file: {data_filename}')
        with open(data_filename) as data_file:
            my_logger.info(f'File {data_filename} opened')

            my_logger.info(f'Read JSON data ')
            mosaic_data = json.load(data_file)
            data_file.close()
            my_logger.info('JSON data loaded')

            return(mosaic_data['blog'])

    except OSError as err:
        my_logger.error(f'{error["os_err"]}: {err}')
        sys.exit()

    except:
        my_logger.error(error['common'])
        sys.exit()


def handler_start(my_update: telegram.update, the_context: telegram.ext.CallbackContext):

    config = get_config(os.path.abspath(os.path.dirname(__file__)))

    user_language = get_language_code(my_update.effective_user)

    my_logger.info(f'Creating start mesages')
    message_title = get_message_text('start_message_title', user_language)
    message_text = get_message_text('start_message_text', user_language)

    my_logger.info(f'Sending start messages')
    my_update.effective_chat.bot.send_message(
        my_update.effective_chat.id, text=f'*{message_title}*', parse_mode='Markdown', disable_web_page_preview=True)

    my_update.effective_chat.bot.send_photo(
        my_update.effective_chat.id, photo=open(config['start_image'], 'rb'), parse_mode='Markdown')

    my_update.effective_chat.bot.send_message(
        my_update.effective_chat.id, text=f'{message_text}', parse_mode='Markdown',
        disable_web_page_preview=True)

    keyboard_send(my_update, KEYBOARD_LAYER['top'])


def handler_button(my_update: telegram.update, the_context: telegram.ext.CallbackContext):

    my_logger.info(f'Getting pressed button')
    pressed_button = my_update.callback_query.data
    my_logger.info(f'Pressed button: {pressed_button}')

    user_language = get_language_code(my_update.callback_query.from_user)

    my_logger.info(f'Choosing blog entry depending on button')
    if pressed_button == KEYBOARD_BUTTONS['last']:
        blog_entry = get_blog_entry_latest(int(KEYBOARD_BUTTONS['last']))

    elif pressed_button == KEYBOARD_BUTTONS['second']:
        blog_entry = get_blog_entry_latest(int(KEYBOARD_BUTTONS['second']))

    my_logger.info(f'Creating message')
    message = blog_entry_create(user_language, blog_entry)

    my_logger.info(f'Sending message')
    blog_entry_send(my_update, message)


def handler_error(my_update: telegram.update, the_context: telegram.ext.CallbackContext):

    my_logger.error('Update "%s" caused error "%s"',
                  my_update, the_context.error)


def keyboard_send(my_update: telegram.update, layer: int):

    user_language = get_language_code(my_update.effective_user)

    my_logger.info(f'Creating keyboard markup')
    bot_keyboard = telegram.InlineKeyboardMarkup(
        create_inline_keyboard(user_language, layer))

    my_logger.info(f'Sending the message including keyboard')
    my_update.effective_chat.bot.send_message(
        my_update.effective_chat.id, text=f'*{get_message_text("keyboard", user_language)}*', parse_mode='Markdown',
        reply_markup=bot_keyboard, disable_web_page_preview=True)


def create_inline_keyboard(language: str, layer: int) -> list:

    my_logger.info(f'Creating the list for the inline keyboard')
    if layer == KEYBOARD_LAYER['top']:
        keyboard = [[get_keyboard_button(KEYBOARD_BUTTONS['last'], language),
                     get_keyboard_button(KEYBOARD_BUTTONS['second'], language)]]
    my_logger.info(f'Keyboard list created: {keyboard_send}')

    return(keyboard)


def get_keyboard_button(button_type: str, language: str) -> telegram.InlineKeyboardButton:

    try:
        message_filename = f'{os.path.abspath(os.path.dirname(__file__))}/messages.json'
        my_logger.info(f'Message file: {message_filename}')

        with open(message_filename) as message_file:
            messages = json.load(message_file)
            message_file.close()

        buttons = messages['buttons']

        button_caption = buttons[button_type][language]
        my_logger.info(f'Button caption: {button_caption}')

        return(telegram.InlineKeyboardButton(button_caption, callback_data=button_type))

    except OSError as err:
        my_logger.error(f'{error["os_err"]}: {err}')

    except:
        my_logger.error(error['common'])


def blog_entry_create(language: str, blog_entry: dict) -> dict:

    my_logger.info(f'Create blog entry')
    message = {'date': blog_entry['date'],
               'title': blog_entry[f'title_{language}'],
               'text': blog_entry[f'text_{language}'],
               'media_type': blog_entry['media_type']
               }

    if blog_entry['media_type'].lower() == 'image':
        my_logger.info(f'Blog entry contains image: {blog_entry["image"]["url"]}')
        message.update({'image_url': blog_entry['image']['url']})
        message.update({'image_caption': blog_entry['image']['caption']})

    elif blog_entry['media_type'].lower() == 'video':
        my_logger.info(f'Message contains video')
        message.update({'video_url': blog_entry[f'video_{language}']['url']})
        message.update(
            {'video_title': blog_entry[f'video_{language}']['title']})

    elif blog_entry['media_type'].lower() == 'youtube':
        my_logger.info(f'Message contains youtube video')
        message.update({'video_url': f'https://www.youtube.com/watch?v={blog_entry["youtube_de"]}'})

    my_logger.info(f'Blog entry: {message}')
    return(message)


def blog_entry_send(my_update: telegram.update, message: dict):

    my_logger.info(f'Send blog entry')
    current_chat = my_update.effective_chat

    my_logger.info(f'Send title')
    current_chat.bot.send_message(current_chat.id, text=f'*{message["date"]} {message["title"]}*',
                                  parse_mode='Markdown', disable_web_page_preview=True)

    if message['media_type'].lower() == 'image':
        my_logger.info(f'Blog entry contains image. Send image')
        current_chat.bot.send_photo(
            current_chat.id, message['image_url'], caption=message['image_caption']
        )

    elif message['media_type'].lower() == 'video':
        my_logger.info(f'Blog entry contains video. Send video')
        current_chat.bot.send_video(
            current_chat.id, message['video_url'], caption=message['video_title']
        )

    my_logger.info(f'Send message')
    current_chat.bot.send_message(current_chat.id, text=message['text'],
                                  parse_mode='Markdown', disable_web_page_preview=True)

    keyboard_send(my_update, KEYBOARD_LAYER['top'])


def get_language_code(user: telegram.User) -> str:

    my_logger.info(f'Try to get language of the user')
    my_logger.info(f'User language: {user.language_code.lower()}')
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
        my_logger.error(f'{error["os_err"]}: {err}')

    except:
        my_logger.error(error['common'])


def get_blog_entry_latest(mode: int) -> dict:

    try:
        config = get_config(os.path.abspath(os.path.dirname(__file__)))

        my_logger.info(f'Read blog from file')
        mosaic_blog = data_read_blog_from_file(config)

        my_logger.info(f'Blog entry to show: {mode}')
        if mode == int(KEYBOARD_BUTTONS['last']):
            requested_date = datetime.date.today()

        elif mode == int(KEYBOARD_BUTTONS['second']):
            requested_date = datetime.date.today() - datetime.timedelta(days=1)

        my_logger.info(f'Date to show: {requested_date}')
        latest_entry = None

        for blog_entry in mosaic_blog:
            blog_entry_date = datetime.datetime.strptime(
                blog_entry['date'], '%Y-%m-%d').date()
            my_logger.info(f'Date of the blog entry: {blog_entry_date}')
            if blog_entry_date == requested_date:
                my_logger.info(f'Blog entry for date {requested_date} found')
                latest_entry = blog_entry
                break

            else:

                if blog_entry_date < requested_date and latest_entry == None:
                    my_logger.info(f'Blog entry is the first one found')
                    latest_entry = blog_entry

                elif blog_entry_date < requested_date and blog_entry_date > datetime.datetime.strptime(latest_entry['date'], '%Y-%m-%d').date():
                    my_logger.info(f'Blog entry is newer that the current one')
                    latest_entry = blog_entry

        my_logger.info(f'Entry in mode {mode} found: {latest_entry}')
        return(latest_entry)

    except OSError as err:
        my_logger.error(f'{error["os_err"]}: {err}')

    except:
        my_logger.error(error['common'])


def get_message_text(message_type: str, language: str) -> str:

    my_logger.info(f'Read message from messages file')

    try:
        message_filename = f'{os.path.abspath(os.path.dirname(__file__))}/messages.json'
        my_logger.info(f'Message file: {message_filename}')
        with open(message_filename) as message_file:
            my_logger.info(f'Read message data')
            messages = json.load(message_file)
            message_file.close()

            my_logger.info(f'Message found: {messages["messages"][message_type][language]}')
            return(messages['messages'][message_type][language])

    except OSError as err:
        my_logger.error(f'{error["os_err"]}: {err}')
        sys.exit()

    except:
        my_logger.error(error['common'])
        sys.exit()


def get_config(script_path: str) -> dict:

    try:
        config_file_name = f'{script_path}/config.json'

        my_logger.info(f'Open configuration file: {config_file_name}')
        with open(config_file_name) as config_file:
            config_data = json.load(config_file)
            config_file.close()
            my_logger.info(f'Read configuration successfull: {config_data}')

            return(config_data)

    except Exception as err:
        my_logger.error(f'{error["common"]}: {err}')
        sys.exit()


#logging.basicConfig(filename=f'{os.path.abspath(os.path.dirname(__file__))}/log/mosaic_bot.log',
#                    format='%(asctime)s - %(funcName)s - %(message)s', level=logging.DEBUG)

my_logger = logging.getLogger()
my_logger.level = logging.WARNING

logfile_handler = RotatingFileHandler(f'{os.path.abspath(os.path.dirname(__file__))}/log/{LOG_FILE}', maxBytes=1024000, backupCount=7)
logfile_handler.setFormatter(logging.Formatter('%(asctime)s - %(funcName)s - %(message)s'))
my_logger.addHandler(logfile_handler)

if __name__ == '__main__':
    main()
