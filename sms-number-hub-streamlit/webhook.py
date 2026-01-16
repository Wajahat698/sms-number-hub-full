from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import Response
from twilio.request_validator import RequestValidator

from lib.db import init_db, log_event, upsert_sms_message


load_dotenv()

app = FastAPI(title="SMS Number Hub Webhook", version="1.0.0")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_validator() -> RequestValidator | None:
    token = (os.getenv("TWILIO_AUTH_TOKEN") or "").strip()
    if not token:
        return None
    return RequestValidator(token)


def _validate_twilio_signature(request: Request, form: dict[str, Any]) -> bool:
    validator = _get_validator()
    if validator is None:
        return False

    signature = request.headers.get("X-Twilio-Signature", "")
    url = str(request.url)
    return bool(validator.validate(url, form, signature))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/twilio/sms")
async def twilio_inbound_sms(request: Request) -> Response:
    init_db()

    try:
        form = dict(await request.form())
    except Exception as e:
        log_event(
            level="error",
            event_type="twilio_parse_form",
            message="Failed to parse inbound request form.",
            context={"error": str(e)},
        )
        return Response(content="", media_type="text/xml", status_code=400)

    enforce_sig = (os.getenv("ENFORCE_TWILIO_SIGNATURE") or "true").strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
    }

    if enforce_sig:
        if not _validate_twilio_signature(request, form):
            log_event(
                level="warning",
                event_type="twilio_signature_invalid",
                message="Inbound Twilio webhook signature validation failed.",
                context={"url": str(request.url)},
            )
            return Response(content="", media_type="text/xml", status_code=403)

    try:
        msg_sid = form.get("MessageSid")
        to_number = (form.get("To") or "").strip()
        from_number = (form.get("From") or "").strip() or None
        body = form.get("Body")
        received_at = _now_iso()

        message_id = upsert_sms_message(
            provider="twilio",
            provider_message_sid=str(msg_sid) if msg_sid else None,
            to_number=to_number,
            from_number=from_number,
            body=str(body) if body is not None else None,
            received_at=received_at,
            raw_payload={k: (str(v) if v is not None else None) for k, v in form.items()},
        )

        log_event(
            level="info",
            event_type="twilio_inbound_sms",
            message="Inbound SMS stored.",
            context={"message_id": message_id, "to": to_number, "from": from_number, "sid": msg_sid},
        )

        return Response(content="<?xml version=\"1.0\" encoding=\"UTF-8\"?><Response></Response>", media_type="text/xml")
    except Exception as e:
        log_event(
            level="error",
            event_type="twilio_ingest_error",
            message="Failed to store inbound SMS.",
            context={"error": str(e), "payload": json.dumps(form, ensure_ascii=False)},
        )
        return Response(content="<?xml version=\"1.0\" encoding=\"UTF-8\"?><Response></Response>", media_type="text/xml", status_code=200)
