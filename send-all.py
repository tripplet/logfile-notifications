#!/usr/bin/env python3

import sys
import os
import json

from datetime import datetime
import http.client
import urllib.parse

import pynma
import yaml  # pip install pyyaml
from pushbullet import Pushbullet # pip install pushbullet.py

#######################################################################################
#######################################################################################

def main():
    users = []

    if len(sys.argv) != 4:
        print("usage: ./send-all.py CONFIG-PATH TITLE MESSAGE")
        exit(-1)
    
    with open(sys.argv[1]) as fp:
        config = yaml.load(fp)

    # preapare config dict
    for user in config['users']:
        User(user).push(sys.argv[2], sys.argv[3])


class User:
    def __init__(self, user_config):
        self.cfg = user_config
        self.online = False

        if 'nma_key' in self.cfg:
            self.nma = pynma.PyNMA([self.cfg['nma_key']])


    def push(self, title, message):
        if not self.cfg['enabled'] or self.online:
            return

        print('-> %s' % self.cfg['name'])
        sys.stdout.flush()

        if 'nma_key' in self.cfg:
            self.nma.push('MinecraftServer', title + ': ' + message)

        elif 'pushbullet_token' in self.cfg:
            self.sendPushbullet(title, message)

        elif 'pushover_token':
            self.sendPushover(title, message)


    def handleEvent(self, new_user, event_name, check_field):
        if not self.cfg['search'] in new_user:
            if self.cfg[check_field]:
                thr = threading.Thread(target=self.push, args=(event_name, new_user), kwargs={})
                thr.start()
        else:
            if event_name == 'Login':
                self.online = True
            elif event_name == 'Logout':
                self.online = False


    def sendPushbullet(self, title, message):
        pb = Pushbullet(self.cfg['pushbullet_token'])

        selected_device = None # All devices

        if ('pushbullet_device' in self.cfg):
            selected_device = next(dev for dev in pb.devices if dev.nickname == self.cfg['pushbullet_device'])

        pb.push_note(title, message, device=selected_device)


    def sendPushover(self, title, message):
        conn = http.client.HTTPSConnection('api.pushover.net:443')
        conn.request('POST', '/1/messages.json', urllib.parse.urlencode({
            'token': self.cfg['pushover_token'],
            'user': self.cfg['pushover_key'],
            'message': message,
            'title': title,
            'sound': 'none'}),
            {'Content-type': 'application/x-www-form-urlencoded'})


if __name__ == '__main__':
    main()
