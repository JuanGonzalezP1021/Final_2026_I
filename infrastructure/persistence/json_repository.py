import json
import os
from threading import Lock


class JsonRepository:
    _lock = Lock()

    def __init__(self, file_path, key_field):
        self.file_path = file_path
        self.key_field = key_field

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        if not os.path.exists(file_path):
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def find_all(self):
        with self._lock:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)

    def _save_all(self, data):
        with self._lock:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

    def find_by_key(self, key):
        for item in self.find_all():
            if item[self.key_field] == key:
                return item
        return None

    def insert(self, record):
        data = self.find_all()
        data.append(record)
        self._save_all(data)

    def update(self, key, updated_record):
        data = self.find_all()

        for i, item in enumerate(data):
            if item[self.key_field] == key:
                data[i] = updated_record
                self._save_all(data)
                return

    def delete(self, key):
        data = [
            item
            for item in self.find_all()
            if item[self.key_field] != key
        ]
        self._save_all(data)