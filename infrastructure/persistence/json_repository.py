import json
import os
import threading
from typing import Any, Callable, Optional
from domain.exceptions.custom_exceptions import PersistenceError

class JsonRepository:
    def __init__(self, filepath: str, key_field: str):
        self.filepath = filepath
        self.key_field = key_field
        self._lock = threading.Lock()
        if not os.path.exists(filepath):
            self._write([])

    def _read(self) -> list[dict]:
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            raise PersistenceError('read', str(e))

    def _write(self, data: list[dict]) -> None:
        tmp = self.filepath + '.tmp'
        try:
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            os.replace(tmp, self.filepath)
        except OSError as e:
            raise PersistenceError('write', str(e))

    def find_all(self, predicate: Optional[Callable] = None) -> list[dict]:
        data = self._read()
        return [d for d in data if predicate(d)] if predicate else data

    def find_by_key(self, key_value: Any) -> Optional[dict]:
        for d in self._read():
            if d.get(self.key_field) == key_value:
                return d
        return None

    def insert(self, record: dict) -> None:
        with self._lock:
            data = self._read()
            data.append(record)
            self._write(data)

    def update(self, key_value: Any, new_record: dict) -> bool:
        with self._lock:
            data = self._read()
            for i, d in enumerate(data):
                if d.get(self.key_field) == key_value:
                    data[i] = new_record
                    self._write(data)
                    return True
            return False

    def delete(self, key_value: Any) -> bool:
        with self._lock:
            data = self._read()
            new_data = [d for d in data if d.get(self.key_field) != key_value]
            if len(new_data) == len(data):
                return False
            self._write(new_data)
            return True