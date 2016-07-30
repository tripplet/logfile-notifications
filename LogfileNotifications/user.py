import pprint
import http.client
import urllib.parse
import threading
from datetime import datetime
import sys

import pynma
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

    def should_send_push(self, ignore_online=False):
        if not self.cfg['enabled'] \
                or (self.online and not ignore_online) \
                or (self.quiet_until is not None and self.quiet_until > datetime.now()):
            return False
        else:
            return True

    def push(self, title, message, ignore_online=False):
        if not self.should_send_push(ignore_online):
            return

        thr = threading.Thread(target=self.push_synchron, args=(title, message, ignore_online))
        thr.start()

    def inform_start(self):
        if 'start_msg' in self.cfg and self.cfg['start_msg'] is True:
            self.push_synchron('Info', 'Restart')

    def push_synchron(self, title, message, ignore_online=False):
        if not self.should_send_push(ignore_online):
            return

        print('-> %s' % self.cfg['name'])
        sys.stdout.flush()

        for method in self.cfg['notify_with']:
            if method == 'nma' and 'nma_key' in self.cfg:
                self.nma.push('MinecraftServer', title + ': ' + message)

            elif method == 'pushover' and 'pushover_token' in self.cfg:
                self.send_pushover(title, message)

            elif method == 'telegram' and 'telegram_chat_id' in self.cfg and User.telegram_bot is not None:
                User.telegram_bot.send_message(chat_id=self.cfg['telegram_chat_id'],
                                              text="{}: {}".format(title, message))

    def handle_event(self, event_nickname, server_name, event_name, check_field):
        if event_nickname in self.cfg['nicknames']:
            # Nickname belonged to this user
            self.last_seen = datetime.now()
            if event_name == 'Login':
                self.online = datetime.now()
            elif event_name == 'Logout':
                self.online = False
        else:
            if self.cfg[check_field]:
                if event_name == 'Login':
                    # Cancel offline event for nickname
                    # And don't send online event
                    if event_nickname in self.offline_events:
                        print('-> %s (canceled)' % (self.cfg['name']))
                        try:
                            self.push_scheduler.cancel(self.offline_events.pop(event_nickname))
                        except ValueError as err:
                            print('Error' + str(err))

                        return
                    title = 'Login ({})'.format(server_name)
                    self.push(title, event_nickname)
                else:
                    title = event_name

                    # Delay offline event
                    if self.should_send_push():
                        print('-> %s (delayed)' % (self.cfg['name']))
                        event = self.push_scheduler.enter(30, 1, self.push, (title, event_nickname))
                        self.offline_events[event_nickname] = event

    def send_pushover(self, title, message):
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
               'online: {}'.format(TelegramBot.format_date(self.last_seen),
                                   TelegramBot.format_date(self.quiet_until),
                                   bool(self.online))
        return ret
