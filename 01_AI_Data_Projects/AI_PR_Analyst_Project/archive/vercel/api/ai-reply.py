import json
from http.server import BaseHTTPRequestHandler
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
    handler.end_headers()
    handler.wfile.write(body)


def _read_json(handler: BaseHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("Content-Length", "0") or "0")
    if length <= 0:
        return {}
    raw = handler.rfile.read(length).decode("utf-8")
    return json.loads(raw or "{}")


def _request_json(url: str, payload: dict, headers: dict, timeout: int = 60) -> dict:
    request = Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Provider HTTP {exc.code}: {body}") from exc


def _provider_text(payload: dict) -> str:
    provider = (payload.get("provider") or "").lower().strip()
    model = (payload.get("model") or "").strip()
    api_key = (payload.get("api_key") or payload.get("apiKey") or "").strip()
    endpoint = (payload.get("endpoint") or "").strip()
    prompt = (payload.get("prompt") or "").strip()
    temperature = float(payload.get("temperature") or 0.65)

    if provider not in {"openai", "gemini", "huggingface"}:
        raise ValueError("This proxy supports OpenAI, Gemini, and Hugging Face only.")
    if not model:
        raise ValueError("Missing model.")
    if not api_key:
        raise ValueError("Missing API key.")
    if not prompt:
        raise ValueError("Missing prompt.")

    if provider == "openai":
        data = _request_json(
            "https://api.openai.com/v1/chat/completions",
            {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
            },
            {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
        )
        return (data.get("choices", [{}])[0].get("message", {}).get("content") or "").strip()

    if provider == "gemini":
        data = _request_json(
            f"https://generativelanguage.googleapis.com/v1beta/models/{quote(model, safe='')}:generateContent?key={quote(api_key, safe='')}",
            {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": temperature},
            },
            {"Content-Type": "application/json"},
        )
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        return "".join(part.get("text", "") for part in parts).strip()

    data = _request_json(
        endpoint or "https://router.huggingface.co/v1/chat/completions",
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        },
        {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    return (data.get("choices", [{}])[0].get("message", {}).get("content") or "").strip()


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        _json_response(self, 200, {"ok": True})

    def do_POST(self):
        try:
            payload = _read_json(self)
            text = _provider_text(payload)
            if not text:
                raise RuntimeError("Provider returned an empty response.")
            _json_response(self, 200, {"reply": text, "provider": payload.get("provider"), "model": payload.get("model")})
        except Exception as exc:
            _json_response(self, 400, {"error": str(exc)})
