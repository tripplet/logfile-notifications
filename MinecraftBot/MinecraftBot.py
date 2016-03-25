#!/usr/bin/env python3

from datetime import datetime

import yaml
import telegram # pip install python-telegram-bot
from telegram.ext import Updater


class MinecraftBot(object):
    def __init__(self, config, users):
        try:
            self.cfg = config
            self.users = users

            self.started = datetime.now()
            self.messages = 0

            self.bot = telegram.Bot(token=self.cfg['telegram_bot_token'])
            self.updater = Updater(bot=self.bot)

            # Get the dispatcher to register handlers
            self.dispatcher = self.updater.dispatcher

            self.dispatcher.addErrorHandler(self.bot_error)

            # add commands
            self.dispatcher.addTelegramMessageHandler(help)
            self.dispatcher.addTelegramCommandHandler("info", self.cmd_info)
            self.dispatcher.addTelegramCommandHandler("status", self.cmd_status)
            self.dispatcher.addTelegramCommandHandler("settings", self.cmd_settings)
            self.dispatcher.addTelegramCommandHandler("quiet", self.cmd_quiet)
            self.dispatcher.addTelegramCommandHandler("broadcast", self.cmd_broadcast)

            self.dispatcher.addUnknownTelegramCommandHandler(help)

            # Start the Bot
            self.updater.start_polling(clean=True, timeout=30)

        except Exception as exp:
            print('Error creating telegram bot')


    def is_authorized(self, bot, update):
        authorized_user = [user["telegram_chat_id"] for user in self.cfg["users"] if "telegram_chat_id" in user]

        if not update.message.chat_id in authorized_user:
            bot.sendMessage(update.message.chat_id, text='Not authorized: %d' % update.message.chat_id)
            return False

        self.messages += 1
        return True


    def cmd_info(self, bot, update):
        if not self.is_authorized(bot, update): return

        bot.sendMessage(update.message.chat_id,
                        text='Started: {}\nMessages received: {}'.format(self.started, self.messages))


    def cmd_settings(self, bot, update):
        if not self.is_authorized(bot, update): return


    def cmd_broadcast(self, bot, update):
        if not self.is_authorized(bot, update): return


    def cmd_status(self, bot, update):
        if not self.is_authorized(bot, update): return

        response = ''
        for user in self.users:
            response += '{}: {}\n'.format(user.cfg['name'], user.online)

        bot.sendMessage(update.message.chat_id,text = response)


    def cmd_quiet(self, bot, update):
        if not self.is_authorized(bot, update): return


    def help(self, bot, update):
        if not self.is_authorized(bot, update): return

        print('help')
        bot.sendMessage(update.message.chat_id, text='Hi, meine Kommands:\n'
                                                     '/info - Bot Info & Statistik\n'
                                                     '/status - Status\n'
                                                     '/quiet - Ich will meine Ruhe\n'
                                                     '/settings - Einstellungen\n'
                                                     '/broadcast - Nachricht an alle')


    def bot_error(self, bot, update, error):
        print('Update "%s" caused error "%s"' % (update, error))
