import os, sys, unittest, asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
os.environ["DISABLE_MODEL_LOADING"] = "1"
from fastapi.testclient import TestClient
from server import app, Clip, decode
from runtime import BodyLimitMiddleware


class ApiTests(unittest.TestCase):
    def test_validation_and_health(self):
        with TestClient(app) as client:
            self.assertEqual(client.get("/health").status_code, 200)
            self.assertEqual(client.get("/ready").status_code, 503)
            self.assertEqual(client.post("/infer", json={}).status_code, 422)
            r = client.options(
                "/infer",
                headers={
                    "Origin": "https://untrusted.example",
                    "Access-Control-Request-Method": "POST",
                },
            )
            self.assertNotIn("access-control-allow-origin", r.headers)

    def test_timestamp_rejected(self):
        with self.assertRaises(ValueError):
            decode(Clip(model="hybrid", frames=["x", "x"], timestamps=[1, 1]))

    def test_chunked_limit(self):
        messages = iter(
            [
                {"type": "http.request", "body": b"123", "more_body": True},
                {"type": "http.request", "body": b"456", "more_body": False},
            ]
        )
        sent = []

        async def receive():
            return next(messages)

        async def send(message):
            sent.append(message)

        async def never(*args):
            raise AssertionError("Oversize reached app")

        asyncio.run(
            BodyLimitMiddleware(never, 5)(
                {"type": "http", "method": "POST", "path": "/"}, receive, send
            )
        )
        self.assertEqual(sent[0]["status"], 413)


if __name__ == "__main__":
    unittest.main()
