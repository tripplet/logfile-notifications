import os
import pyinotify


class EventHandler(pyinotify.ProcessEvent):
    monitor = None

    def __init__(self, *args, **kwargs):
        super(EventHandler, self).__init__(*args, **kwargs)

    # noinspection PyPep8Naming
    @staticmethod
    def process_IN_MODIFY(event):
        if os.path.dirname(event.pathname) not in EventHandler.monitor.server_logs:
            return

        log_file = EventHandler.monitor.server_logs[os.path.dirname(event.pathname)]

        new_lines = log_file.update_position(event.pathname)
        lines = new_lines.split('\n')

        for line in lines:
            EventHandler.monitor.handle_newline_event(line, log_file.name)


class LogFile:
    watch_manager = pyinotify.WatchManager()
    notifier = pyinotify.Notifier(watch_manager, EventHandler())

    def __init__(self, log_entry, monitor):
        self.path = log_entry['path']
        self.name = log_entry['name']

        # Complete update
        self.positions = {} 
        self.update_position(self.path)

        EventHandler.monitor = monitor

        if os.path.isdir(self.path):
            self.watch_path = self.path
        else:
            self.watch_path = os.path.dirname(self.path)

        LogFile.watch_manager.add_watch(self.watch_path, pyinotify.IN_MODIFY, rec=False)

    def update_position(self, path):
        if os.path.isdir(path):
            for dir_entry in os.scandir(path):
                if dir_entry.is_file():
                    self.update_file_position(dir_entry.path)
            return ''
        else:
            return self.update_file_position(path)

    def update_file_position(self, file_path):
        if file_path not in self.positions:
            self.positions[file_path] = 0

        with open(file_path) as f:
            if self.positions[file_path] > os.stat(file_path).st_size:
                self.positions[file_path] = 0

            f.seek(self.positions[file_path])
            new_lines = f.read()

            last_n = new_lines.rfind('\n')
            if last_n >= 0:
                self.positions[file_path] += last_n + 1

            return new_lines

    @staticmethod
    def loop():
        LogFile.notifier.loop()
