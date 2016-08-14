import sched
import time
import threading
import sys
import re
import logging

from .user import User
from .bot import NotificationBot
from .logfile import FileWatcher


class Monitor:
    log = logging.getLogger(__name__)

    def __init__(self, config):
        self.users = []
        self.server_logs = []
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

        # create file event watchers
        if 'logfiles' in config:
            for log_file in config['logfiles']:
                self.server_logs.append(FileWatcher(log_file, config['regex'], self.handle_newline_event))
            # Start watching for changes
            FileWatcher.watch_manager.start()
            Monitor.log.info('Finished processing status of log files')

        # inform users about restart
        for user in self.users:
            user.inform_start()

    def loop(self):
        if len(self.server_logs) == 0:
            self.read_stdin()
        else:
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                FileWatcher.watch_manager.stop()
            FileWatcher.watch_manager.join()

    def read_stdin(self):
        """Read from stdin for debugging"""

        stdin_events = object()
        stdin_events.name = 'stdin'
        stdin_events.login = re.compile('1\s(.+)')
        stdin_events.logout = re.compile('2\s(.+)')

        while True:
            line = input('$ ')
            # noinspection PyTypeChecker
            self.handle_newline_event(line, stdin_events)

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
            Monitor.log.info("Login: '{}' on '{}'".format(result_login.group(1), event.name))

        if result_logout is not None:
            Monitor.log.info("Logout: '{}' on '{}'".format(result_logout.group(1), event.name))

        sys.stdout.flush()

        for cur_user in self.users:
            if result_login is not None:
                cur_user.handle_event(result_login.group(1), event.name, 'Login', 'login_msg')

            if result_logout is not None:
                cur_user.handle_event(result_logout.group(1), event.name, 'Logout', 'logout_msg')
