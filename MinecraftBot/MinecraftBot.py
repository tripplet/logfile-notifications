#!/usr/bin/env python3

from datetime import datetime

import yaml
import telegram # pip install python-telegram-bot
from telegram.ext import Updater

import logging
logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class MinecraftBot(object):
    messages = 0

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
            self.dispatcher.addTelegramMessageHandler(self.help)
            self.dispatcher.addTelegramCommandHandler("info", self.cmd_info)
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
        self.messages += 1


    def is_authorized(self, bot, update):
        authorized_user = [user["telegram_chat_id"] for user in self.cfg["users"] if "telegram_chat_id" in user]

        if not update.message.chat_id in authorized_user:
            self.sendMessage(update.message.chat_id, text='Not authorized: %d' % update.message.chat_id)
            return False

        # Received a valid message from an authorized user
        self.messages += 1
        return True


    def cmd_info(self, bot, update):
        if not self.is_authorized(bot, update): return

        self.sendMessage(update.message.chat_id,
                        text='Gestarted: {}\nNachrichten verarbeitet: {}'.format(self.started, self.messages))


    def cmd_settings(self, bot, update):
        if not self.is_authorized(bot, update): return
        self.sendMessage(update.message.chat_id, text='Not implemented yet...')


    def cmd_broadcast(self, bot, update):
        if not self.is_authorized(bot, update): return
        self.sendMessage(update.message.chat_id, text='Not implemented yet...')


    def cmd_status(self, bot, update):
        if not self.is_authorized(bot, update): return

        response = ''
        for user in self.users:
            response += '{}: {}\n'.format(user.cfg['name'], user.online)

        self.sendMessage(update.message.chat_id,text = response)


    def cmd_quiet(self, bot, update):
        if not self.is_authorized(bot, update): return

        self.sendMessage(update.message.chat_id, text='Not implemented yet...')


    def help(self, bot, update):
        if not self.is_authorized(bot, update): return

        self.sendMessage(update.message.chat_id, text='Hi, meine Kommands:\n'
                                                      '/info - Bot Info & Statistik\n'
                                                      '/status - Status\n'
                                                      '/quiet - Ich will meine Ruhe\n'
                                                      '/settings - Einstellungen\n'
                                                      '/broadcast - Nachricht an alle\n'
                                                      '/help - Zeige diese Hilfe\n'
                                                      '/cancel - Aktuelle Aktion abbrechen',
                         reply_markup=telegram.ReplyKeyboardHide())


    def bot_error(self, bot, update, error):
        print('Update "%s" caused error "%s"' % (update, error))
