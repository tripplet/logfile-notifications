#!/usr/bin/env python3

from datetime import datetime, timedelta
from collections import OrderedDict

import telegram # pip install python-telegram-bot
from telegram.ext import Updater

import logging
logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class MinecraftBot:

    _handle_response = None # Function responsible for handling a response from the user
    _messages = 0 # Number of messages processed

    _quiet_times = OrderedDict({
        '4 Stunden':         lambda: datetime.now() + timedelta(hours=4),
        'Bis Morgen':        lambda: (datetime.now() + timedelta(days=1))
                                      .replace(hour=6, minute=0, second=0, microsecond=0),
        'Bis Heute Abend':   lambda: datetime.now().replace(hour=20, minute=0, second=0, microsecond=0),
        'RuheModus beenden': lambda: None
    })

    _reply_quiet = telegram.ReplyKeyboardMarkup([[list(_quiet_times.keys())[0], list(_quiet_times.keys())[1]],
                                                 [list(_quiet_times.keys())[2], list(_quiet_times.keys())[3]]],
                                                resize_keyboard=True,
                                                one_time_keyboard=True)

    def __init__(self, config, users):
        try:
            self.cfg = config
            self.users = users

            self.started = datetime.now()

            self.bot = telegram.Bot(token=self.cfg['telegram_bot_token'])
            self.updater = Updater(bot=self.bot)

            # Get the dispatcher to register handlers
            self.dispatcher = self.updater.dispatcher

            self.dispatcher.addErrorHandler(self.bot_error)

            # add commands
            self.dispatcher.addTelegramMessageHandler(self.rx_message)
            self.dispatcher.addTelegramCommandHandler("info", self.cmd_info)
            self.dispatcher.addTelegramCommandHandler("cancel", self.cmd_cancel)
            self.dispatcher.addTelegramCommandHandler("status", self.cmd_status)
            self.dispatcher.addTelegramCommandHandler("settings", self.cmd_settings)
            self.dispatcher.addTelegramCommandHandler("quiet", self.cmd_quiet)
            self.dispatcher.addTelegramCommandHandler("broadcast", self.cmd_broadcast)
            self.dispatcher.addTelegramCommandHandler("help", self.help)

            self.dispatcher.addUnknownTelegramCommandHandler(self.help)

            # Start the Bot
            self.updater.start_polling(clean=True, timeout=30)

        except Exception as exp:
            print('Error creating telegram bot')


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


    def cmd_info(self, bot, update):
        if not self.is_authorized(bot, update): return

        self.sendMessage(update.message.chat_id,
                         text='Am Leben seit: {}\nNachrichten verarbeitet: {}'.format(self.started, self._messages))


    def cmd_settings(self, bot, update):
        if not self.is_authorized(bot, update): return
        self.sendMessage(update.message.chat_id, text='Not implemented yet...')


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
                response += '{}: {}\n'.format(user.cfg['name'], 'Online' if user.online else 'Offline (Zuletzt online ' + str(user.last_seen) + ')')

        self.sendMessage(update.message.chat_id, text = response)


    def cmd_quiet(self, bot, update):
        if not self.is_authorized(bot, update): return

        self.sendMessage(update.message.chat_id, text='Wie lange?\nNutze /cancel zum Abbrechen', reply_markup=self._reply_quiet)

        # Function handling the response
        def quiet_response(self, update):
            if update.message.text in self._quiet_times:
                # find user with the current chat id
                found_user = [user for user in self.users if "telegram_chat_id" in user.cfg and
                                                              user.cfg["telegram_chat_id"] == update.message.chat_id]

                # set quiet time of user
                found_user[0].quiet_until = self._quiet_times[update.message.text]()

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
        if self._handle_response is None:
            self.help(bot, update)
        else:
            self._handle_response(self, update)


    def help(self, bot, update):
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
