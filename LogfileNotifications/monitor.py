import sched
import time
import threading
from datetime import datetime
import sys
import re

from .user import User
from .bot import NotificationBot


class Monitor:
    def __init__(self, config):
        self.users = []
        self.server_logs = {}
        self.tgbot = None
        self.push_scheduler = sched.scheduler()

        # parse user from config
        for user in config['users']:
            self.users.append(User(user, self.push_scheduler))

        # create telegram bot
        if 'telegram_bot_token' in config:
            self.tgbot = NotificationBot(config, self.users)

            if self.tgbot.ready:
                self.tgbot.start()
                User.telegram_bot = self.tgbot

        # start scheduler loop
        t = threading.Thread(target=self.scheduler_loop)
        t.start()

        # create inotify listener
        if 'logfiles' in config:
            from .logfile import FileWatcher
            for log_file in config['logfiles']:
                watcher = FileWatcher(log_file, config['regex'], self)
                self.server_logs[watcher.watch_path] = watcher
            print('Finished processing status of log files')

        # inform users about restart
        for user in self.users:
            user.inform_start()

    def loop(self):
        if len(self.server_logs) == 0:
            self.read_stdin()
        else:
            from .logfile import FileWatcher
            FileWatcher.loop()  # start file notification loop

    def read_stdin(self):
        """Read from stdin for debugging"""
        while True:
            line = input('$ ')
            self.handle_newline_event(line, 'stdin')

    def scheduler_loop(self):
        """Infinite loop for executing scheduled push events."""
        while True:
            self.push_scheduler.run()
            time.sleep(1)

    def handle_newline_event(self, line, event):
        if line == '':
            return

        result_login = event.login.search(line)
        result_logout = event.logout.search(line)

        if result_login is not None:
            print('%s -- Login (%s) %s' % (str(datetime.now()), event.name, result_login.group(1)))

        if result_logout is not None:
            print('%s -- Logout %s' % (str(datetime.now()), result_logout.group(1)))

        sys.stdout.flush()

        for cur_user in self.users:
            if result_login is not None:
                cur_user.handle_event(result_login.group(1), event.name, 'Login', 'login_msg')

            if result_logout is not None:
                cur_user.handle_event(result_logout.group(1), event.name, 'Logout', 'logout_msg')
