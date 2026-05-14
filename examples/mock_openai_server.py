#!/usr/bin/env python3
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict


class MockOpenAIHandler(BaseHTTPRequestHandler):
    server_version = "MockOpenAI/0.1"

    def do_GET(self) -> None:
        if self.path == "/v1/models":
            self._send_json({"object": "list", "data": [{"id": "mock-llm", "object": "model"}]})
            return
        self.send_error(404, "not found")

    def do_POST(self) -> None:
        if self.path not in {"/v1/chat/completions", "/v1/completions"}:
            self.send_error(404, "not found")
            return

        payload = self._read_json()
        prompt_tokens = self._estimate_prompt_tokens(payload)
        completion_tokens = int(payload.get("max_tokens") or 32)
        total_tokens = prompt_tokens + completion_tokens

        if self.path == "/v1/chat/completions":
            response = {
                "id": "chatcmpl-mock",
                "object": "chat.completion",
                "model": payload.get("model", "mock-llm"),
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "This is a mock OpenAI-compatible response.",
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                },
            }
        else:
            response = {
                "id": "cmpl-mock",
                "object": "text_completion",
                "model": payload.get("model", "mock-llm"),
                "choices": [{"index": 0, "text": "This is a mock completion.", "finish_reason": "stop"}],
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                },
            }

        self._send_json(response)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _read_json(self) -> Dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length) if content_length else b"{}"
        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            payload = {}
        return payload if isinstance(payload, dict) else {}

    def _estimate_prompt_tokens(self, payload: Dict[str, Any]) -> int:
        if "messages" in payload and isinstance(payload["messages"], list):
            text = " ".join(str(message.get("content", "")) for message in payload["messages"])
        else:
            text = str(payload.get("prompt", ""))
        return max(1, len(text.split()))

    def _send_json(self, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8000), MockOpenAIHandler)
    print("Mock OpenAI-compatible server listening on http://127.0.0.1:8000")
    print("Try: POST /v1/chat/completions")
    server.serve_forever()


if __name__ == "__main__":
    main()
