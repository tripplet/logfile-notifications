#!/usr/bin/env python3

from datetime import datetime, timedelta

import telegram  # pip install python-telegram-bot
from telegram.ext import CommandHandler

from bothelper import TelegramBot

import logging
logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# German time formating
import locale
try:
    locale.setlocale(locale.LC_TIME, 'de_DE')
except Exception as exp:
    try:
        locale.setlocale(locale.LC_TIME, 'de_DE.utf8')
    except Exception as exp:
        pass


class NotificationBot(TelegramBot):
    _quiet_times = {
        '4 Stunden':         lambda: datetime.now() + timedelta(hours=4),
        'Bis Morgen':        lambda: (datetime.now() + timedelta(days=1))
                                      .replace(hour=6, minute=0, second=0, microsecond=0),
        'Bis Heute Abend':   lambda: datetime.now().replace(hour=20, minute=0, second=0, microsecond=0),
        'RuheModus beenden': lambda: None
    }

    _reply_quiet = telegram.ReplyKeyboardMarkup([['4 Stunden', 'Bis Morgen'],
                                                 ['Bis Heute Abend', 'RuheModus beenden']],
                                                resize_keyboard=True,
                                                one_time_keyboard=True)

    def __init__(self, config, users):
        super().__init__(config)
        self.users = users

        self.dispatcher.addTelegramCommandHandler(CommandHandler("status", self.cmd_status))
        self.dispatcher.addTelegramCommandHandler(CommandHandler("settings", self.cmd_settings))
        self.dispatcher.addTelegramCommandHandler(CommandHandler("quiet", self.cmd_quiet))
        self.dispatcher.addTelegramCommandHandler(CommandHandler("broadcast", self.cmd_broadcast))

    def _reload_config_file(self):
        self.cfg = self.config_file

    def is_authorized(self, bot, update):
        authorized_user = [user.cfg["telegram_chat_id"] for user in self.users if "telegram_chat_id" in user.cfg]

        if update.message.chat_id not in authorized_user:
            self.sendMessage(update.message.chat_id, text='Unauthorized: %d' % update.message.chat_id)
            return False

        # Received a valid message from an authorized user
        self.messages += 1
        return True

    def _find_user_by_id(self, user_id):
        # find user with the current chat id
        found_user = [user for user in self.users if "telegram_chat_id" in user.cfg and
                      user.cfg["telegram_chat_id"] == user_id]

        # set quiet time of user
        return found_user[0]

    def cmd_settings(self, bot, update):
        if not self.is_authorized(bot, update): return
        self.sendMessage(update.message.chat_id, text=str(self._find_user_by_id(update.message.chat_id)))

    def cmd_broadcast(self, bot, update):
        if not self.is_authorized(bot, update): return

        # Text after /broadcast
        msg = update.message.text[10:]

        self.sendMessage(update.message.chat_id, text='Was möchtest du allen schreiben?\nNutze /cancel zum Abbrechen',
                         reply_markup=telegram.ForceReply())

        # Function handling the response
        def broadcast_response(self, update):
            for user in self.users:
                user.push_synchron('Broadcast', update.message.text, ignore_online=True)

            self.sendMessage(update.message.chat_id, text='Erledigt', reply_markup=telegram.ReplyKeyboardHide())
            self.set_handle_response(update.message.chat_id, None)

        self.set_handle_response(update.message.chat_id, broadcast_response)

    def cmd_status(self, bot, update):
        if not self.is_authorized(bot, update): return

        response = ''
        for user in self.users:
            if user.cfg['enabled']:
                response += '{}: {}\n'.format(user.cfg['name'],
                                              'Online' if user.online else
                                              'Offline (Zuletzt online ' + TelegramBot.formatDate(user.last_seen) + ')')

        self.sendMessage(update.message.chat_id, text=response)

    def cmd_quiet(self, bot, update):
        if not self.is_authorized(bot, update): return

        self.sendMessage(update.message.chat_id,
                         text='Wie lange?\nNutze /cancel zum Abbrechen',
                         reply_markup=self._reply_quiet)

        # Function handling the response
        def quiet_response(self, update):
            if update.message.text in self._quiet_times:
                # find user with the current chat id
                self._find_user_by_id(update.message.chat_id).quiet_until = self._quiet_times[update.message.text]()

                self.sendMessage(update.message.chat_id, text='Erledigt', reply_markup=telegram.ReplyKeyboardHide())
                self.set_handle_response(update.message.chat_id, None)

            else:
                self.sendMessage(update.message.chat_id, text='Bitte wähle eine der folgenden Möglichkeiten',
                                 reply_markup=self.reply_quiet)

        self.set_handle_response(update.message.chat_id, quiet_response)

    def cmd_help(self, bot, update):
        if not self.is_authorized(bot, update): return

        self.sendMessage(update.message.chat_id, text='Hi, meine Kommands:\n'
                                                      '/info - Bot Info & Statistik\n'
                                                      '/status - Status\n'
                                                      '/quiet - Ich will meine Ruhe\n'
                                                      '/settings - Einstellungen\n'
                                                      '/broadcast - Nachricht an alle\n'
                                                      '/help - Zeigt die Hilfe\n'
                                                      '/cancel - Aktuelle Aktion abbrechen',
                         reply_markup=telegram.ReplyKeyboardHide())
