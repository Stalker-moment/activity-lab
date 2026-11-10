"""ASGI payload bounds include chunked requests; no image data in logs."""

import threading
from starlette.responses import JSONResponse


class AdmissionGate:
    def __init__(self, limit=2):
        if limit < 1:
            raise ValueError("MAX_INFLIGHT must be positive")
        self.slots = threading.BoundedSemaphore(limit)

    def acquire(self):
        return self.slots.acquire(blocking=False)

    def release(self):
        self.slots.release()


class BodyLimitMiddleware:
    def __init__(self, app, max_bytes):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        chunks = []
        size = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            size += len(message.get("body", b""))
            if size > self.max_bytes:
                return await JSONResponse(
                    {"detail": "Ukuran permintaan melebihi batas 6 MB."},
                    status_code=413,
                )(scope, receive, send)
            chunks.append(message)
            if not message.get("more_body", False):
                break

        async def replay():
            if chunks:
                return chunks.pop(0)
            return await receive()

        await self.app(scope, replay, send)
