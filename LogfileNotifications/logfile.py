import os
import pyinotify


class EventHandler(pyinotify.ProcessEvent):
    monitor = None

    def __init__(self, *args, **kwargs):
        super(EventHandler, self).__init__(*args, **kwargs)

    def process_IN_MODIFY(self, event):
        if event.pathname not in EventHandler.monitor.server_logs:
            return

        log_file = EventHandler.monitor.server_logs[event.pathname]

        new_lines = log_file.update_position()
        lines = new_lines.split('\n')

        for line in lines:
            EventHandler.monitor.handle_newline_event(line, log_file.name)


class ServerLogFile:
    watch_manager = pyinotify.WatchManager()
    notifier = pyinotify.Notifier(watch_manager, EventHandler())

    def __init__(self, log_file, monitor):
        self.file = log_file['file']
        self.name = log_file['name']
        self.position = 0
        self.update_position()

        EventHandler.monitor = monitor
        ServerLogFile.watch_manager.add_watch(os.path.dirname(self.file), pyinotify.IN_MODIFY, rec=False)

    def update_position(self):
        with open(self.file) as f:
            if self.position > os.stat(self.file).st_size:
                self.position = 0

            f.seek(self.position)
            new_lines = f.read()

            last_n = new_lines.rfind('\n')
            if last_n >= 0:
                self.position += last_n + 1

            f.seek(self.position)
            return new_lines

    @staticmethod
    def loop():
        ServerLogFile.notifier.loop()



