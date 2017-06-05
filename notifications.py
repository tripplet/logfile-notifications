#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import yaml
import locale
import logging

import LogfileNotifications
from bothelper import TelegramBot

# German time formatting
try:
    locale.setlocale(locale.LC_TIME, 'de_DE')
except locale.Error as exp:
    try:
        locale.setlocale(locale.LC_TIME, 'de_DE.utf8')
    except locale.Error as exp:
        pass

#######################################################################################
#######################################################################################


def main():
    if len(sys.argv) < 2:
        print('No config file given')
        exit(1)

    with open(sys.argv[1]) as fp:
        config = yaml.load(fp)

    log_format = '%(asctime)s - [%(name)s] %(levelname)-5.5s - %(message)s'
    log_formatter = logging.Formatter(log_format)

    logging.basicConfig(level=config['logging']['level'],
                        format=log_format,
                        datefmt='%Y-%m-%d %H:%M:%S')

    if 'file' in config['logging']:
        file_handler = logging.FileHandler(config['logging']['file'])
        file_handler.setFormatter(log_formatter)
        logging.getLogger().addHandler(file_handler)

    logging.info('Logfile monitoring running - version: ' + TelegramBot.get_version())
    m = LogfileNotifications.Monitor(config)

    # Set separate logging level for telegram bot (really excessive on DEBUG)
    if 'telegram_bot_token' in config:
        logging.getLogger("telegram.bot").setLevel(config['logging']['telegram_level'])

    m.loop()

if __name__ == '__main__':
    main()
