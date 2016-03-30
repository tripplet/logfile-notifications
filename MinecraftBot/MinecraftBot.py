#!/usr/bin/env python3

from datetime import datetime, timedelta

import telegram # pip install python-telegram-bot
from telegram.ext import Updater

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


class MinecraftBot:

    _handle_response = None # Function responsible for handling a response from the user
    _messages = 0 # Number of messages processed

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
        try:
            self.cfg = config
            self.users = users

            self.started = datetime.now()
            self.version = MinecraftBot.getVersion()

            self.bot = telegram.Bot(token=self.cfg['telegram_bot_token'])
            self.updater = Updater(bot=self.bot)

            # Get the dispatcher to register handlers
            self.dispatcher = self.updater.dispatcher

            self.dispatcher.addErrorHandler(self.bot_error)

            # add commands
            self.dispatcher.addTelegramMessageHandler(self.rx_message)
            self.dispatcher.addTelegramCommandHandler("start", self.cmd_start)
            self.dispatcher.addTelegramCommandHandler("info", self.cmd_info)
            self.dispatcher.addTelegramCommandHandler("cancel", self.cmd_cancel)
            self.dispatcher.addTelegramCommandHandler("status", self.cmd_status)
            self.dispatcher.addTelegramCommandHandler("settings", self.cmd_settings)
            self.dispatcher.addTelegramCommandHandler("quiet", self.cmd_quiet)
            self.dispatcher.addTelegramCommandHandler("broadcast", self.cmd_broadcast)
            self.dispatcher.addTelegramCommandHandler("help", self.cmd_help)

            self.dispatcher.addUnknownTelegramCommandHandler(self.cmd_help)

            # Start the Bot
            self.updater.start_polling(clean=True, timeout=30)

        except Exception as exp:
            print('Error creating telegram bot')


    @staticmethod
    def formatDate(date):
        if date is None:
            return 'Unbekannt'
        else:
            return date.strftime('%a %-d. %b - %H:%M')


    @staticmethod
    def getVersion():
        try:
            import subprocess
            import os
            import inspect
            
            # Determine directory this file is located in
            cwd = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
            
            # try .version file
            version_file = os.path.join(cwd, '.version'))
            if os.path.exists(version_file):
                with open(version_file) as f:
                    version = f.read()
                    return version
            else
                # try with git
                return subprocess.check_output(['git', 'describe', '--long', '--always'], cwd=cwd).decode('utf8').strip()
        except Exception:
            return '?'


    def sendMessage(self, chat_id, text, **args):
        self.bot.sendMessage(chat_id=chat_id, text=text, **args)
        self._messages += 1


    def is_authorized(self, bot, update):
        authorized_user = [user.cfg["telegram_chat_id"] for user in self.users if "telegram_chat_id" in user.cfg]

        if not update.message.chat_id in authorized_user:
            self.sendMessage(update.message.chat_id, text='Unauthorized: %d' % update.message.chat_id)
            return False

        # Received a valid message from an authorized user
        self._messages += 1
        return True


    def _findUserById(self, id):
        # find user with the current chat id
        found_user = [user for user in self.users if "telegram_chat_id" in user.cfg and
                      user.cfg["telegram_chat_id"] == id]

        # set quiet time of user
        return found_user[0]


    def cmd_start(self, bot, update):
        if not self.is_authorized(bot, update): return
        self.cmd_help(bot, update)


    def cmd_info(self, bot, update):
        if not self.is_authorized(bot, update): return
        self.sendMessage(update.message.chat_id,
                         text='Version: {}\n'
                              'Am Leben seit: {}\n'
                              'Nachrichten verarbeitet: {}'
                         .format(self.version, MinecraftBot.formatDate(self.started), self._messages))


    def cmd_settings(self, bot, update):
        if not self.is_authorized(bot, update): return
        self.sendMessage(update.message.chat_id, text=str(self._findUserById(update.message.chat_id)))


    def cmd_broadcast(self, bot, update):
        if not self.is_authorized(bot, update): return

        # Text after /broadcast
        msg = update.message.text[10:]

        self.sendMessage(update.message.chat_id, text='Was möchtest du allen schreiben?\nNutze /cancel zum Abbrechen',
                         reply_markup=telegram.ForceReply())

        # Function handling the response
        def broadcast_response(self, update):
            for user in self.users:
                user.push('Broadcast', update.message.text, ignore_online=True)

            self.sendMessage(update.message.chat_id, text='Erledigt', reply_markup=telegram.ReplyKeyboardHide())
            self._handle_response = None

        self._handle_response = broadcast_response


    def cmd_status(self, bot, update):
        if not self.is_authorized(bot, update): return

        response = ''
        for user in self.users:
            if user.cfg['enabled']:
                response += '{}: {}\n'.format(user.cfg['name'],
                                            'Online' if user.online else
                                            'Offline (Zuletzt online ' + MinecraftBot.formatDate(user.last_seen) + ')')

        self.sendMessage(update.message.chat_id, text = response)


    def cmd_quiet(self, bot, update):
        if not self.is_authorized(bot, update): return

        self.sendMessage(update.message.chat_id, text='Wie lange?\nNutze /cancel zum Abbrechen', reply_markup=self._reply_quiet)

        # Function handling the response
        def quiet_response(self, update):
            if update.message.text in self._quiet_times:
                # find user with the current chat id
                self._findUserById(update.message.chat_id).quiet_until = self._quiet_times[update.message.text]()

                self.sendMessage(update.message.chat_id, text='Erledigt', reply_markup=telegram.ReplyKeyboardHide())
                self._handle_response = None

            else:
                self.sendMessage(update.message.chat_id, text='Bitte wähle eine der folgenden Möglichkeiten',
                                 reply_markup=self.reply_quiet)

        self._handle_response = quiet_response


    def cmd_cancel(self, bot, update):
        if not self.is_authorized(bot, update): return

        self.sendMessage(update.message.chat_id, text='Abgebrochen', reply_markup=telegram.ReplyKeyboardHide())
        self._handle_response = None


    def rx_message(self, bot, update):
        if not self.is_authorized(bot, update): return

        # Not expecting a response
        if not self._handle_response is None:
            self._handle_response(self, update)


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


    def bot_error(self, bot, update, error):
        print('Update "%s" caused error "%s"' % (update, error))
