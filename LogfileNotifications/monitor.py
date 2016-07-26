import sched
import time
import threading
from datetime import datetime
import sys
import re

from .user import User
from .bot import NotificationBot


class Monitor:
    user_login_regex = re.compile('\[[\d:]+\]\s\[[\w\s/]+\]:\s([\w]+) joined the game')
    user_logout_regex = re.compile('\[[\d:]+\]\s\[[\w\s/]+\]:\s([\w]+) left the game')

    def __init__(self, config):
        self.users = []
        self.server_logs = dict()
        self.tgbot = None
        self.push_scheduler = sched.scheduler()

        # parse user from config
        for user in config['users']:
            self.users.append(User(user, self.push_scheduler))

        # create telegram bot
        if 'telegram_bot_token' in config:
            self.tgbot = NotificationBot(config, self.users)
            User.telegram_bot = self.tgbot

        # override default regex
        if 'user_login_regex' in config:
            Monitor.user_login_regex = re.compile(config['user_login_regex'])
        if 'user_logout_regex' in config:
            Monitor.user_logout_regex = re.compile(config['user_logout_regex'])

        # start scheduler loop
        t = threading.Thread(target=self.scheduler_loop)
        t.start()

        # create inotify listener
        if 'server_logs' in config:
            from .logfile import FileWatcher
            for sv in config['server_logs']:
                    fw = FileWatcher(sv, self)
                    self.server_logs[fw.watch_path] = fw

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

    def handle_newline_event(self, line, event_provider):
        if line == '':
            return

        result_login = Monitor.user_login_regex.search(line)
        result_logout = Monitor.user_logout_regex.search(line)

        if result_login is not None:
            print('%s -- Login (%s) %s' % (str(datetime.now()), event_provider, result_login.group(1)))

        if result_logout is not None:
            print('%s -- Logout %s' % (str(datetime.now()), result_logout.group(1)))

        sys.stdout.flush()

        for cur_user in self.users:
            if result_login is not None:
                cur_user.handle_event(result_login.group(1), event_provider, 'Login', 'login_msg')

            if result_logout is not None:
                cur_user.handle_event(result_logout.group(1), event_provider, 'Logout', 'logout_msg')
