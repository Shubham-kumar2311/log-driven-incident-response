"""Backward-compat alias — publisher.py owns the queue internally.
Uses lazy import to avoid import-ordering issues.
"""


def _get_queue():
    from publisher import get_local_queue
    return get_local_queue()


class _LazyQueue:
    """Proxy that defers the real queue lookup until first access."""
    _q = None

    def _resolve(self):
        if self._q is None:
            self._q = _get_queue()
        return self._q

    def qsize(self):
        return self._resolve().qsize()

    def put(self, item, **kw):
        return self._resolve().put(item, **kw)

    def put_nowait(self, item):
        return self._resolve().put_nowait(item)

    def get(self, **kw):
        return self._resolve().get(**kw)

    def get_nowait(self):
        return self._resolve().get_nowait()


processed_event_queue = _LazyQueue()
