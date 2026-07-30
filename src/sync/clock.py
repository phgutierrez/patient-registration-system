"""Relógio lógico híbrido com ordenação determinística."""
from __future__ import annotations

import threading
import time
import uuid


class HybridLogicalClock:
    def __init__(self, device_uuid: str):
        self.device_uuid = device_uuid
        self._lock = threading.Lock()
        self._last_ms = 0
        self._counter = 0

    def next(self) -> tuple[str, str]:
        with self._lock:
            now_ms = int(time.time() * 1000)
            if now_ms > self._last_ms:
                self._last_ms = now_ms
                self._counter = 0
            else:
                self._counter += 1
            event_uuid = str(uuid.uuid4())
            order = (
                f'{self._last_ms:013d}:{self._counter:08d}:'
                f'{self.device_uuid}:{event_uuid}'
            )
            return order, event_uuid

    def observe(self, order: str) -> None:
        try:
            timestamp, counter, *_ = order.split(':', 2)
            remote_ms = int(timestamp)
            remote_counter = int(counter)
        except (AttributeError, TypeError, ValueError):
            return
        with self._lock:
            if remote_ms > self._last_ms:
                self._last_ms = remote_ms
                self._counter = remote_counter
            elif remote_ms == self._last_ms:
                self._counter = max(self._counter, remote_counter)
