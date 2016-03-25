#!/usr/bin/env python3

import re
import sys
import os
import json

from datetime import datetime
import http.client
import urllib.parse
import threading

import pyinotify # pip install pyinotify
import pynma
import yaml  # pip install pyyaml
from pushbullet import Pushbullet # pip install pushbullet.py

# config file
config_path = sys.argv[1]

#######################################################################################
#######################################################################################

users = []
server_logs = dict()
tgbot = None

with open(sys.argv[1]) as fp:
    config = yaml.load(fp)

user_login_string  = re.compile('\[[\d:]+\]\s\[[\w\s\/]+\]:\s([\w]+) joined the game')
user_logout_string = re.compile('\[[\d:]+\]\s\[[\w\s\/]+\]:\s([\w]+) left the game')


if 'telegram_bot_token' in config:
    from MinecraftBot import MinecraftBot


def main():
    global users
    global server_logs
    global tgbot

    # parse user from config
    for user in config['users']:
        users.append(User(user))

    if 'telegram_bot_token' in config:
        tgbot = MinecraftBot(config, users)

    # create inotify listener
    wm = pyinotify.WatchManager()
    notifier = pyinotify.Notifier(wm, EventHandler())

    for sv in config['server_logs']:
        slf = ServerLogFile(sv)
        server_logs[slf.file] = slf
        server_logs[slf.file].add_watch(wm)

    # start infinite loop
    print('Logfile monitoring running')
    notifier.loop()


class User:
    def __init__(self, user_config):
        self.cfg = user_config
        self.online = False
        self.last_seen = None

        if 'nma_key' in self.cfg:
            self.nma = pynma.PyNMA([self.cfg['nma_key']])


    def push(self, title, message):
        if not self.cfg['enabled'] or self.online:
            return

        print('-> %s' % self.cfg['name'])
        sys.stdout.flush()

        for method in self.cfg['notify_with']:
            if method == 'nma' and 'nma_key' in self.cfg:
                self.nma.push('MinecraftServer', title + ': ' + message)

            elif method == 'pushbullet' and 'pushbullet_token' in self.cfg:
                self.sendPushbullet(title, message)

            elif method == 'pushover' and 'pushover_token' in self.cfg:
                self.sendPushover(title, message)

            elif method == 'telegram' and 'telegram_chat_id' in self.cfg and tgbot is not None:
                tgbot.bot.sendMessage(chat_id=self.cfg['telegram_chat_id'], text="{}: {}".format(title, message))


    def handleEvent(self, new_user, server_name, event_name, check_field):
        if not self.cfg['search'] in new_user:
            if self.cfg[check_field]:

                if event_name == 'Login':
                    title = 'Login ({})'.format(server_name)
                else:
                    title = event_name

                thr = threading.Thread(target=self.push, args=(title, new_user), kwargs={})
                thr.start()
        else:
            self.last_seen = datetime.now()
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


class ServerLogFile:
    def __init__(self, log_file):
        self.file = log_file['file']
        self.name = log_file['name']
        self.position = 0
        self.update_position()

    def update_position(self):
        with open(self.file) as f:
            if self.position > os.stat(self.file).st_size:
                self.position = 0

            f.seek(self.position)
            new_lines = f.read()

            last_n = new_lines.rfind('\n')
            if last_n >= 0:
                self.position += last_n + 1

            f.seek(self.position)
            return new_lines

    def add_watch(self, watchManager):
        watchManager.add_watch(os.path.dirname(self.file), pyinotify.IN_MODIFY, rec=False)


class EventHandler(pyinotify.ProcessEvent):
    def __init__(self, *args, **kwargs):
        super(EventHandler, self).__init__(*args, **kwargs)

    def process_IN_MODIFY(self, event):
        if event.pathname not in server_logs:
            return

        log_file = server_logs[event.pathname]

        new_lines = log_file.update_position()
        lines = new_lines.split('\n')

        for line in lines:
            if line == '':
                continue

            result_login  = user_login_string.search(line)
            result_logout = user_logout_string.search(line)

            if result_login is not None:
                print('%s -- Login (%s) %s' % (str(datetime.now()), log_file.name, result_login.group(1)))

            if result_logout is not None:
                print('%s -- Logout %s' % (str(datetime.now()), result_logout.group(1)))

            sys.stdout.flush()

            for cur_user in users:
                if result_login is not None:
                    cur_user.handleEvent(result_login.group(1), log_file.name, 'Login', 'login_msg')

                if result_logout is not None:
                    cur_user.handleEvent(result_logout.group(1), log_file.name, 'Logout', 'logout_msg')

if __name__ == '__main__':
    main()