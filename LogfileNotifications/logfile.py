# -*- coding: utf-8 -*-

import os
import re
import logging

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class FileWatcher(FileSystemEventHandler):
    log = logging.getLogger(__name__)
    watch_manager = Observer()

    def __init__(self, entry, regex, handle_newline_event):
        self.path = entry['path']
        self.name = entry['name']
        self.login = re.compile(regex[entry['regex']['login']])
        self.logout = re.compile(regex[entry['regex']['logout']])
        self.handle_newline_event = handle_newline_event

        # Complete update
        self.positions = {}
        self.update_position(self.path)

        if os.path.isdir(self.path):
            self.watch_path = self.path
        else:
            self.watch_path = os.path.dirname(self.path)

        FileWatcher.watch_manager.schedule(self, self.watch_path, recursive=False)

    def on_created(self, event):
        self.on_modified(event)

    def on_modified(self, event):
        new_lines = self.update_position(event.src_path)
        lines = new_lines.split('\n')

        for line in lines:
            self.handle_newline_event(line, self)

    def update_position(self, path):
        if os.path.isdir(path):
            for dir_entry in os.scandir(path):
                if dir_entry.is_file():
                    self._update_file_position(dir_entry.path)
            return ''
        else:
            return self._update_file_position(path)

    def _update_file_position(self, file_path):
        if file_path not in self.positions:
            self.positions[file_path] = 0

        with open(file_path) as f:
            if self.positions[file_path] > os.stat(file_path).st_size:
                self.positions[file_path] = 0

            f.seek(self.positions[file_path])
            try:
                new_lines = f.read()
            except UnicodeDecodeError as ex:
                FileWatcher.log.info("Ignoring UnicodeDecodeError in '{}': ".format(file_path, str(ex)))
                self.positions[file_path] = os.stat(file_path).st_size
                return ''
            except Exception as ex:
                FileWatcher.log.error("Error while reading file '{}': {}".format(file_path, str(ex)))
                self.positions[file_path] = os.stat(file_path).st_size
                return ''

            last_n = new_lines.rfind('\n')
            if last_n >= 0:
                self.positions[file_path] += last_n + 1

            return new_lines
