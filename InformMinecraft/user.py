import pprint
import http.client
import urllib.parse
import threading
from datetime import datetime
import sys

import pynma
from pushbullet import Pushbullet

from .bot import TelegramBot

class User:
    telegram_bot = None

    def __init__(self, user_config, push_scheduler):
        self.online = False
        self.last_seen = None
        self.quiet_until = None
        self.offline_events = dict()

        self.cfg = user_config
        self.push_scheduler = push_scheduler

        if 'nma_key' in self.cfg:
            self.nma = pynma.PyNMA([self.cfg['nma_key']])


    def push_as_thread(self, title, message, ignore_online=False):
        thr = threading.Thread(target=self.push, args=(title, message, ignore_online))
        thr.start()


    def push(self, title, message, ignore_online=False):
        if not self.cfg['enabled'] or (self.online and not ignore_online):
            return

        if self.quiet_until is not None and self.quiet_until > datetime.now():
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

            elif method == 'telegram' and 'telegram_chat_id' in self.cfg and User.telegram_bot is not None:
                User.telegram_bot.sendMessage(chat_id=self.cfg['telegram_chat_id'], text="{}: {}".format(title, message))


    def handleEvent(self, new_user, server_name, event_name, check_field):
        if not self.cfg['search'] in new_user:
            if self.cfg[check_field]:

                if event_name == 'Login':
                    # Cancel offline event for new_user
                    # And don't send online event
                    if new_user in self.offline_events:
                        print('-> %s (canceled)' % (self.cfg['name']))
                        try:
                            self.push_scheduler.cancel(self.offline_events.pop(new_user))
                        except ValueError as err:
                            print('Error' + err)

                        return
                    title = 'Login ({})'.format(server_name)
                    self.push_as_thread(title, new_user)
                else:
                    title = event_name

                    # Delay offline event
                    print('-> %s (delayed)' % (self.cfg['name']))
                    event = self.push_scheduler.enter(30, 1, self.push_as_thread, (title, new_user))
                    self.offline_events[new_user] = event

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

    def __str__(self):
        ret = pprint.pformat(self.cfg, indent=4)
        ret += '\n' \
               'last_seen: {}\n' \
               'quiet_until: {}\n' \
               'online: {}'.format(TelegramBot.formatDate(self.last_seen),
                                   TelegramBot.formatDate(self.quiet_until),
                                   self.online)
        return ret