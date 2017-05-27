# -*- coding: utf-8 -*-

import http.client
import urllib.parse
import logging

import pynma

"""Notification base class"""


class Notify(object):
    __methods = None
    log = logging.getLogger(__name__)

    @staticmethod
    def methods():
        if Notify.__methods is None:
            Notify.__methods = {
                'debug': NotifyDebug,
                'nma': NotifyNma,
                'telegram': NotifyTelegram,
                'pushover': NotifyPushover
            }
        return Notify.__methods

    def __init__(self, user):
        self.user = user

    @staticmethod
    def notify(method, user, title, message):
        if method not in Notify.methods().keys():
            Notify.log.error('Unknown notification method: ' + method)
            return
        Notify.methods()[method](user).send(title, message)

    def send(self, title, message):
        raise Exception('Not implemented in base class')


class NotifyDebug(Notify):
    def send(self, title, message):
        Notify.log.critical('DEBUG-NOTIFY {} => Title: {}, Msg: {}'.format(self.user.cfg['name'], title, message))


class NotifyPushover(Notify):
    def send(self, title, message):
        conn = http.client.HTTPSConnection('api.pushover.net:443')
        conn.request('POST', '/1/messages.json', urllib.parse.urlencode({
            'token': self.user.cfg['pushover_token'],
            'user': self.user.cfg['pushover_key'],
            'message': message,
            'title': title,
            'sound': 'none'}),
            {'Content-type': 'application/x-www-form-urlencoded'})


class NotifyNma(Notify):
    def send(self, title, message):
        if self.user.nma is None and 'nma_key' in self.user.cfg:
            self.user.nma = pynma.PyNMA([self.user.cfg['nma_key']])

        self.user.nma.push('Notification', title + ': ' + message)


class NotifyTelegram(Notify):
    def send(self, title, message):
        if 'telegram_chat_id' in self.user.cfg and self.user.telegram_bot is not None:
            self.user.telegram_bot.send_message(chat_id=self.user.cfg['telegram_chat_id'],
                                                text="{}: {}".format(title, message))