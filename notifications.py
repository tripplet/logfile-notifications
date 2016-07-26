#!/usr/bin/env python3

import sys
import yaml

import LogfileNotifications
from bothelper import TelegramBot

#######################################################################################
#######################################################################################


def main():
    if len(sys.argv) < 2:
        print('No config file given')
        exit(1)

    with open(sys.argv[1]) as fp:
        config = yaml.load(fp)

    print('Logfile monitoring running (v' + TelegramBot.get_version(use_caller_version=True, nb_levels_above=1) + ')')
    m = LogfileNotifications.Monitor(config)
    m.loop()

if __name__ == '__main__':
    main()
