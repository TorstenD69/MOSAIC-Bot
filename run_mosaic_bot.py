# -*- coding: utf-8 -*-

import requests
import json
import datetime
import locale
import os
import sys
import logging
from logging.handlers import RotatingFileHandler

import telegram
import telegram.ext

from telegram.error import TelegramError, Unauthorized, BadRequest, TimedOut, ChatMigrated, NetworkError

FILE_TYPE = 'json'

LOG_FILE = "mosaic_bot.log"

# Constants for button functions
BUTTON_FUNCTION = {
    'command': 'c',
    'menu': 'm'
}

# Constants for Keyboard layer
KEYBOARD_LAYER = {
    'main': 'ma',
    'year': 'yr',
    'month': 'mo',
    'day': 'dy'
}

# Constants for inline keyboard
KEYBOARD_BUTTONS = {
    'last': '1',
    'second': '2',
    'calendar': '3',
    'top': '4',
    'back': '5'
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
        updater.dispatcher.add_handler(
            telegram.ext.CommandHandler('start', handler_start))
        updater.dispatcher.add_handler(
            telegram.ext.CallbackQueryHandler(handler_button))
        # updater.dispatcher.add_handler(CommandHandler('help', handler_help))
        updater.dispatcher.add_error_handler(handler_error)
        my_logger.info(f'Dispatcher successfull added')

        my_logger.info(f'Starting bot poller')
        updater.start_polling()
        updater.idle()

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

    send_top_level_keyboard(my_update)


def handler_button(my_update: telegram.update, the_context: telegram.ext.CallbackContext):

    my_logger.info(f'Getting pressed button')
    pressed_button = get_abstract_button_from_callback(
        my_update.callback_query.data)
    my_logger.info(f'Pressed button: {pressed_button}')

    my_logger.info(f'Choosing button processing depending on button type')

    if pressed_button['function'] == BUTTON_FUNCTION['command']:
        process_command_buttons(my_update, pressed_button)

    elif pressed_button['function'] == BUTTON_FUNCTION['menu']:
        process_menu_buttons(my_update, pressed_button)


def handler_error(my_update: telegram.update, the_context: telegram.ext.CallbackContext):

    my_logger.error('Update "%s" caused error "%s"',
                    my_update, the_context.error)


def process_command_buttons(my_update: telegram.update, button: dict):

    my_logger.info(f'Processing command button: {button}')

    if button['value'] == str(KEYBOARD_BUTTONS['last']) or button['value'] == str(KEYBOARD_BUTTONS['second']):
        send_latest_blog_entry(my_update, button['value'])

    elif button['value'] == 'top':
        send_top_level_keyboard(my_update)

    elif button['layer'] == KEYBOARD_LAYER['day']:
        send_blog_entry_by_date(my_update, button)


def process_menu_buttons(my_update: telegram.update, button: dict):

    my_logger.info(f'Processing menu button: {button}')

    if button['layer'] == KEYBOARD_LAYER['main'] and button['value'] == KEYBOARD_BUTTONS['calendar']:
        send_year_menu(my_update, button)

    elif button['layer'] == KEYBOARD_LAYER['year']:
        send_month_menu(my_update, button)

    elif button['layer'] == KEYBOARD_LAYER['month']:
        send_day_menu(my_update, button)


def send_latest_blog_entry(my_update: telegram.update, button: str):

    blog_entry = get_blog_entry_latest(button)

    user_language = get_language_code(my_update.callback_query.from_user)

    my_logger.info(f'Creating message')
    message = blog_entry_create(user_language, blog_entry)

    my_logger.info(f'Sending message')
    blog_entry_send(my_update, message)


def send_top_level_keyboard(my_update: telegram.update):

    user_language = get_language_code(my_update.effective_user)

    my_logger.info(f'Creating keyboard markup')
    bot_keyboard = telegram.InlineKeyboardMarkup(
        create_top_level_keyboard(user_language))

    my_logger.info(f'Sending the message including keyboard')
    my_update.effective_chat.bot.send_message(
        my_update.effective_chat.id, text=f'*{get_message_text("keyboard", user_language)}*', parse_mode='Markdown',
        reply_markup=bot_keyboard, disable_web_page_preview=True)


def send_blog_entry_by_date(my_update: telegram.update, button: dict):

    blog_entry = get_blog_entry_by_date(button['value'])

    user_language = get_language_code(my_update.callback_query.from_user)

    my_logger.info(f'Creating message')
    message = blog_entry_create(user_language, blog_entry)

    my_logger.info(f'Sending message')
    blog_entry_send(my_update, message)


def create_top_level_keyboard(language: str) -> list:

    my_logger.info(f'Creating top level menu')

    button = [
        create_abstract_button(BUTTON_FUNCTION['command'], KEYBOARD_LAYER['main'], KEYBOARD_BUTTONS['last'], get_button_caption(
            KEYBOARD_BUTTONS['last'], language)),
        create_abstract_button(BUTTON_FUNCTION['command'], KEYBOARD_LAYER['main'], KEYBOARD_BUTTONS['second'], get_button_caption(
            KEYBOARD_BUTTONS['second'], language)),
        create_abstract_button(BUTTON_FUNCTION['menu'], KEYBOARD_LAYER['main'], KEYBOARD_BUTTONS['calendar'], get_button_caption(
            KEYBOARD_BUTTONS['calendar'], language))
    ]

    keyboard = [[telegram.InlineKeyboardButton(button[0]['caption'], callback_data=create_callback_from_abstract(button[0])),
                 telegram.InlineKeyboardButton(button[1]['caption'], callback_data=create_callback_from_abstract(button[1]))],
                [telegram.InlineKeyboardButton(button[2]['caption'], callback_data=create_callback_from_abstract(button[2]))]]

    my_logger.info(f'Keyboard list created: {keyboard}')

    return(keyboard)


def create_abstract_button(function: str, layer: str, value: str, caption: str) -> dict:

    abstract_button = {
        'function': function,
        'layer': layer,
        'value': value,
        'caption': caption
    }

    return(abstract_button)


def get_abstract_button_from_callback(callback: str) -> dict:

    value_list = callback.split('_')

    abstract_button = {
        'function': value_list[0],
        'layer': value_list[1],
        'value': value_list[2],
        'caption': ''
    }

    return(abstract_button)


def create_callback_from_abstract(button: dict) -> str:

    return(f'{button["function"]}_{button["layer"]}_{button["value"]}')


def get_button_caption(button_type: str, language: str) -> telegram.InlineKeyboardButton:

    try:
        message_filename = f'{os.path.abspath(os.path.dirname(__file__))}/messages.json'
        my_logger.info(f'Message file: {message_filename}')

        with open(message_filename) as message_file:
            messages = json.load(message_file)
            message_file.close()

        buttons = messages['buttons']

        button_caption = buttons[button_type]['caption'][language]
        my_logger.info(f'Button caption: {button_caption}')

        return(button_caption)

    except OSError as err:
        my_logger.error(f'{error["os_err"]}: {err}')

    except:
        my_logger.error(error['common'])


def send_year_menu(my_update: telegram.update, button: dict):

    my_logger.info(f'Creating calendar menu')

    language = get_language_code(my_update.effective_user)

    menu = create_calender_menu(KEYBOARD_LAYER['year'], button['value'])

    menu.append([telegram.InlineKeyboardButton(get_button_caption(
        KEYBOARD_BUTTONS['top'], language), callback_data=f'c_{KEYBOARD_LAYER["year"]}_top')])

    inline_keyboard = telegram.InlineKeyboardMarkup(menu)

    my_logger.info(f'Sending the message including keyboard')

    my_update.effective_chat.bot.editMessageReplyMarkup(
        chat_id=my_update.effective_chat.id, message_id=my_update.effective_message.message_id,
        reply_markup=inline_keyboard, disable_web_page_preview=True)


def send_month_menu(my_update: telegram.update, button: dict):

    my_logger.info(f'Creating calendar menu')

    language = get_language_code(my_update.effective_user)

    menu = create_calender_menu(KEYBOARD_LAYER['month'], button['value'])

    menu.append([telegram.InlineKeyboardButton(get_button_caption(
        KEYBOARD_BUTTONS['top'], language), callback_data=f'c_{KEYBOARD_LAYER["month"]}_top')])

    inline_keyboard = telegram.InlineKeyboardMarkup(menu)

    my_logger.info(f'Sending the message including keyboard')
    my_update.effective_chat.bot.editMessageReplyMarkup(
        chat_id=my_update.effective_chat.id, message_id=my_update.effective_message.message_id,
        text=f'*{get_message_text("month_keyboard", language)}*', parse_mode='Markdown',
        reply_markup=inline_keyboard, disable_web_page_preview=True)


def send_day_menu(my_update: telegram.update, button: dict):

    my_logger.info(f'Creating calendar menu')

    language = get_language_code(my_update.effective_user)

    menu = create_calender_menu(KEYBOARD_LAYER['day'], button['value'])

    menu.append([telegram.InlineKeyboardButton(get_button_caption(
        KEYBOARD_BUTTONS['top'], language), callback_data=f'c_{KEYBOARD_LAYER["day"]}_top')])

    inline_keyboard = telegram.InlineKeyboardMarkup(menu)

    my_logger.info(f'Sending the message including keyboard')
    my_update.effective_chat.bot.editMessageReplyMarkup(
        chat_id=my_update.effective_chat.id, message_id=my_update.effective_message.message_id,
        text=f'*{get_message_text("day_keyboard", language)}*', parse_mode='Markdown',
        reply_markup=inline_keyboard, disable_web_page_preview=True)


def create_calender_menu(layer: int, choice: str) -> list:

    my_logger.info(f'Start creating the mosaic calendar menu')

    n_rows = 6

    buttons = get_cal_buttons_from_blog(layer, choice)

    menu = [buttons[i:i + n_rows] for i in range(0, len(buttons), n_rows)]

    my_logger.info(f'Creating the dynamic menu finished')

    return(menu)


def get_cal_buttons_from_blog(layer: int, choice: str) -> list:

    buttons = []

    kind = 'mosaic'
    calendar = get_calendar_from_blog(kind)

    if layer == KEYBOARD_LAYER['year']:
        range = calendar.keys()
        value_prefix = ''
        function = BUTTON_FUNCTION['menu']

    elif layer == KEYBOARD_LAYER['month']:
        year = get_date_part(choice, KEYBOARD_LAYER['year'])
        range = calendar[year].keys()
        value_prefix = f'{year}-'
        function = BUTTON_FUNCTION['menu']

    elif layer == KEYBOARD_LAYER['day']:
        year = get_date_part(choice, KEYBOARD_LAYER['year'])
        month = get_date_part(choice, KEYBOARD_LAYER['month'])
        range = calendar[year][month]
        value_prefix = f'{year}-{month}-'
        function = BUTTON_FUNCTION['command']

    for item in range:
        button = {
            'function': function,
            'layer': layer,
            'value': f'{value_prefix}{item}'
        }

        buttons.append(telegram.InlineKeyboardButton(
            item, callback_data=create_callback_from_abstract(button)))

    return(buttons)


def get_calendar_from_blog(kind: str) -> dict:

    try:
        config = get_config(os.path.abspath(os.path.dirname(__file__)))

        mosaic_blog = data_read_blog_from_file(config)

        calendar = {}
        for entry in mosaic_blog:
            if entry['kind'] == kind:
                year = get_date_part(entry['date'], KEYBOARD_LAYER['year'])
                month = get_date_part(entry['date'], KEYBOARD_LAYER['month'])
                day = get_date_part(entry['date'], KEYBOARD_LAYER['day'])

                if year not in calendar.keys():
                    calendar[year] = {}
                    calendar[year][month] = [day]

                else:
                    if month not in calendar[year].keys():
                        calendar[year][month] = [day]

                    else:
                        calendar[year][month].append(day)

        sorted_calendar = sort_calendar(calendar)

        return(sorted_calendar)

    except OSError as err:
        my_logger.error(f'{error["os_err"]}: {err}')

    except:
        my_logger.error(error['common'])


def get_date_part(date: str, part: int) -> str:

    if part == KEYBOARD_LAYER['year']:
        return(date[0:4])
    elif part == KEYBOARD_LAYER['month']:
        return(date[5:7])
    elif part == KEYBOARD_LAYER['day']:
        return(date[8:10])


def blog_entry_create(language: str, blog_entry: dict) -> dict:

    my_logger.info(f'Create blog entry')
    message = {'date': blog_entry['date'],
               'title': blog_entry[f'title_{language}'],
               'text': blog_entry[f'text_{language}'],
               'permalink': blog_entry['permalink'],
               'kind': blog_entry['kind']
               }

    if blog_entry['kind'] == 'mosaic':
        message['media_type'] = blog_entry['media_type']

        if blog_entry['media_type'].lower() == 'image' and blog_entry['image'] != 'false':
            my_logger.info(
                f'Blog entry contains image: {blog_entry["image"]["url"]}')
            message.update({'image_url': blog_entry['image']['url']})
            message.update({'image_caption': blog_entry['image']['caption']})

        elif blog_entry['media_type'].lower() == 'video':
            my_logger.info(f'Message contains video')
            message.update(
                {'video_url': blog_entry[f'video_{language}']['url']})
            message.update(
                {'video_title': blog_entry[f'video_{language}']['title']})

        elif blog_entry['media_type'].lower() == 'youtube':
            my_logger.info(f'Message contains youtube video')
            message.update(
                {'video_url': f'https://www.youtube.com/watch?v={blog_entry["youtube_de"]}'})

        else:
            my_logger.info(f'Message contains no image and no video')
            message.update({'image_url': ''})
            message.update({'image_caption': ''})

    else:
        blog_entry['media_type'] = ''

    my_logger.info(f'Blog entry: {message}')
    return(message)


def blog_entry_send(my_update: telegram.update, message: dict):

    my_logger.info(f'Send blog entry')
    current_chat = my_update.effective_chat

    if message['media_type'].lower() == 'image':
        url = message['image_url']

        if 'image_caption' in message and len(message['image_caption']) > 0:
            caption = message['image_caption']
        else:
            caption = message['image_url']

    elif (message['media_type'].lower() == 'video') or (message['media_type'].lower() == 'youtube'):
        url = message['video_url']

        if 'video_title' in message and len(message['video_title']) > 0:
            caption = message['video_title']
        else:
            caption = message['video_url']

    else:
        url = ''
        caption = ''

    my_logger.info(f'Create message')
    message_text = f'*{get_localized_date(message["date"], my_update)}*\n*{message["title"]}*\n{message["text"]}\n\n[{caption}]({url})'

    my_logger.info(f'Send message')
    current_chat.bot.send_message(current_chat.id, text=message_text,
                                  parse_mode=telegram.ParseMode.MARKDOWN, disable_web_page_preview=False)

    send_top_level_keyboard(my_update)


def get_localized_date(date: str, my_update: telegram.update) -> str:

    language = get_language_code(my_update.effective_user)

    if language == 'de':
        locale_code = 'de_DE.utf8'

    else:
        locale_code = 'en_US.utf8'

    locale.setlocale(locale.LC_ALL, locale_code)

    local_date = datetime.datetime.strptime(
        date, "%Y-%m-%d").date().strftime("%d %B %Y")

    return(local_date)


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


def get_blog_entry_latest(mode: str) -> dict:

    try:
        config = get_config(os.path.abspath(os.path.dirname(__file__)))

        my_logger.info(f'Read blog from file')
        mosaic_blog = data_read_blog_from_file(config)

        my_logger.info(f'Blog entry to show: {mode}')
        if mode == KEYBOARD_BUTTONS['last']:
            requested_date = datetime.date.today()

        elif mode == KEYBOARD_BUTTONS['second']:
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

            my_logger.info(
                f'Message found: {messages["messages"][message_type][language]}')
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


def sort_calendar(calendar: dict) -> dict:

    my_logger.info(f'Start sorting the calendar from the blog')

    sorted_calendar = {}

    for year in sorted(calendar.keys()):
        sorted_calendar[year] = {}

        for month in sorted(calendar[year].keys()):
            sorted_calendar[year][month] = sorted(calendar[year][month])

    my_logger.info(f'Sorting the calendar finished')

    return(sorted_calendar)


my_logger = logging.getLogger()
my_logger.level = logging.WARNING

logfile_handler = RotatingFileHandler(
    f'{os.path.abspath(os.path.dirname(__file__))}/log/{LOG_FILE}', maxBytes=1024000, backupCount=7)
logfile_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(funcName)s - %(message)s'))
my_logger.addHandler(logfile_handler)

if __name__ == '__main__':
    main()
