# -*- coding: utf-8 -*-

import requests
import json
import datetime
import os, sys
import logging
import run_mosaic_bot as mosaic

FILE_TYPE = 'json'

def main ():

    config = mosaic.get_config(os.path.abspath(os.path.dirname(__file__)))
    my_logger.info(f'Path to the data file: {config["data_path"]}')
    my_logger.info(f'Name of the data file: {config["data_file"]}')

    temp_filename = data_download(config)

    data_activate (temp_filename, config)

def data_download(config: dict) -> str:

    try:

        data_filename = f'{config["data_path"]}/{config["data_file"]}_{datetime.date.today()}.{FILE_TYPE}'

        my_logger.info(f'Start data download ')
        with open(data_filename, 'w') as data_file:

            my_logger.debug(f'Data file {data_filename} successfull opened')

            my_logger.debug(f'Request url: {config["mosaic_url"]}')
            web_response = requests.request('get', config["mosaic_url"])
            json_data = web_response.json()
            my_logger.debug(f'Request successfull: {web_response}')

            json.dump(json_data, data_file)
            my_logger.debug(f'File: {data_filename} successfull written')
            data_file.close()

            my_logger.info(f'Data download successfull')
            return(data_filename)

    except (requests.ConnectionError, requests.HTTPError, requests.Timeout) as err:
        my_logger.error(f'The HTTP requests has raised an error: {err}')
        sys.exit()

    except OSError as err:
        my_logger.error(f'An OS error occurred: {err}')
        sys.exit()

    except:
        my_logger.error('An error occurred')
        sys.exit()

def data_activate(today_filename: str, config: dict) -> bool():

    my_logger.info(f'Start activating latest data')

    try:
        bck_filename = f'{config["data_path"]}/{config["data_file"]}.bak'
        my_logger.debug(f'Backup file: {bck_filename}')
        tmp_filename = f'{config["data_path"]}/data.tmp'
        my_logger.debug(f'Temporary file: {tmp_filename}')
        data_filename = f'{config["data_path"]}/{config["data_file"]}.{FILE_TYPE}'
        my_logger.debug(f'Data file: {data_filename}')

        if os.path.exists(tmp_filename):
            os.remove(tmp_filename)
            my_logger.debug(f'Existing temporary file successfull deleted')

        if os.path.exists(bck_filename):
            os.rename(bck_filename, tmp_filename)
            my_logger.debug(f'Temporary copy of backup file created')

        os.rename(data_filename, bck_filename)
        my_logger.info('Data file backed up')

        os.rename(today_filename, data_filename)
        my_logger.info('New file moved to data file')

        if os.path.exists(tmp_filename):
            os.remove(tmp_filename)
            my_logger.debug(f'Temporary file: {tmp_filename} successfull removed')

        my_logger.info(f'Activation of data successfull')
        return(True)

    except OSError as err:

        my_logger.error(f'An error occurred: {err}')
        if not(os.path.exists(data_filename)):
            my_logger.info(f'Data file missing. Try to restore')
            if os.path.exists(bck_filename):
                os.rename(bck_filename, data_filename)
                my_logger.warning(f'The data file is restored')
                return(True)

            else:
                my_logger.error(f'Data file could not restored. Terminate programm')
                sys.exit()

my_logger = logging.getLogger()
my_logger.level = logging.DEBUG

logfile_handler = logging.StreamHandler(sys.stdout)
logfile_handler.setFormatter(logging.Formatter('%(asctime)s - %(funcName)s - %(message)s'))
my_logger.addHandler(logfile_handler)

if __name__ == '__main__':
    main()
