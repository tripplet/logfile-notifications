import os
import re
import logging

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class EventHandler(FileSystemEventHandler):
    monitor = None

    def on_created(self, event):
        self.on_modified(event)

    def on_modified(self, event):
        if os.path.dirname(event.src_path) not in EventHandler.monitor.server_logs:
            return

        log_file = EventHandler.monitor.server_logs[os.path.dirname(event.src_path)]

        new_lines = log_file.update_position(event.src_path)
        lines = new_lines.split('\n')

        for line in lines:
            EventHandler.monitor.handle_newline_event(line, log_file)


class FileWatcher:
    watch_manager = Observer()

    def __init__(self, entry, regex, monitor):
        self.path = entry['path']
        self.name = entry['name']
        self.login = re.compile(regex[entry['regex']['login']])
        self.logout = re.compile(regex[entry['regex']['logout']])

        # Complete update
        self.positions = {} 
        self.update_position(self.path)

        EventHandler.monitor = monitor

        if os.path.isdir(self.path):
            self.watch_path = self.path
        else:
            self.watch_path = os.path.dirname(self.path)

        FileWatcher.watch_manager.schedule(EventHandler(), self.watch_path, recursive=False)

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
            try:
                new_lines = f.read()
            except UnicodeDecodeError as ex:
                logging.info("Ignoring UnicodeDecodeError in '{}': ".format(file_path, str(ex)))
                self.positions[file_path] = os.stat(file_path).st_size
                return ''
            except Exception as ex:
                logging.error("Error while reading file '{}': {}".format(file_path, str(ex)))
                self.positions[file_path] = os.stat(file_path).st_size
                return ''

            last_n = new_lines.rfind('\n')
            if last_n >= 0:
                self.positions[file_path] += last_n + 1

            return new_lines
