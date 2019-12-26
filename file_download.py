# -*- coding: utf-8 -*-

import requests
import json
import datetime
import os, sys
import logging
import mosaic

FILE_TYPE = 'json'

def main ():

    logging.basicConfig(format='%(asctime)s - %(funcName)s - %(message)s', level=logging.DEBUG)

    config = mosaic.get_config(os.path.abspath(os.path.dirname(__file__)))
    logging.info(f'Path to the data file: {config["data_path"]}')
    logging.info(f'Name of the data file: {config["data_file"]}')

    temp_filename = data_download(config)

    data_activate (temp_filename, config)

def data_download(config: dict) -> str:

    try:

        data_filename = f'{config["data_path"]}/{config["data_file"]}_{datetime.date.today()}.{FILE_TYPE}'

        with open(data_filename, 'w') as data_file:

            logging.info(f'Data file {data_filename} successfull opened')

            logging.info(f'Request url: {config["mosaic_url"]}')
            web_response = requests.request('get', config["mosaic_url"])
            json_data = web_response.json()
            logging.info(f'Request successfull: {web_response}')

            json.dump(json_data, data_file)
            logging.info(f'File: {data_filename} successfull written')
            data_file.close()

            return(data_filename)

    except (requests.ConnectionError, requests.HTTPError, requests.Timeout) as err:
        logging.error(f'The HTTP requests has raised an error: {err}')
        sys.exit()
        
    except OSError as err:
        logging.error(f'An OS error occurred: {err}')
        sys.exit()

    except:
        logging.error('An error occurred')
        sys.exit()

def data_activate(today_filename: str, config: dict) -> bool():

    try:
        bck_filename = f'{config["data_path"]}/{config["data_file"]}.bak'
        tmp_filename = f'{config["data_path"]}/data.tmp'
        data_filename = f'{config["data_path"]}/{config["data_file"]}.{FILE_TYPE}'

        if os.path.exists(tmp_filename):
            os.remove(tmp_filename)
            logging.info(f'Existing temporary file successfull deleted')

        if os.path.exists(bck_filename):
            os.rename(bck_filename, tmp_filename)
            logging.info(f'Temporary copy of backup file created')

        os.rename(data_filename, bck_filename)
        logging.info('Data file backed up')

        os.rename(today_filename, data_filename)
        logging.info('New file moved to data file')

        if os.path.exists(tmp_filename):
            os.remove(tmp_filename)

        return(True)
    
    except OSError as err:
        
        logging.error(f'An error occurred: {err}')
        if not(os.path.exists(data_filename)):
            logging.info(f'Data file missing. Try to restore')
            if os.path.exists(bck_filename):
                os.rename(bck_filename, data_filename)
                logging.warning(f'The data file is restored')
                return(True)

            else:
                logging.error(f'Data file could not restored. Terminate programm')
                sys.exit()


if __name__ == '__main__':
    main()
