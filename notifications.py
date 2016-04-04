#!/usr/bin/env python3

import sys
import yaml

import LogfileNotifications

#######################################################################################
#######################################################################################


def main():
    if len(sys.argv) < 2:
        print('No config file given')
        exit(1)

    with open(sys.argv[1]) as fp:
        config = yaml.load(fp)

    print('Logfile monitoring running')
    m = InformMinecraft.Monitor(config)
    m.loop()

if __name__ == '__main__':
    main()