"""Resend HTTPS transport for Django's EmailMessage interface."""

import base64
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail.backends.base import BaseEmailBackend


class ResendEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        sent = 0

        for message in email_messages or []:
            if not message.recipients():
                continue

            try:
                self._send(message)
            except Exception:
                if not self.fail_silently:
                    raise
            else:
                sent += 1

        return sent

    def _send(self, message):
        if not settings.RESEND_API_KEY:
            raise ImproperlyConfigured(
                "RESEND_API_KEY is required for Resend delivery."
            )

        # Keep Django's header-injection validation.
        message.message()

        payload = {
            "from": message.from_email,
            "subject": message.subject,
            "html" if message.content_subtype == "html" else "text": message.body,
        }

        for key in ("to", "cc", "bcc", "reply_to"):
            if value := getattr(message, key):
                payload[key] = value

        for alternative in getattr(message, "alternatives", []):
            if alternative.mimetype == "text/html":
                payload["html"] = alternative.content

        attachments = []

        for attachment in message.attachments:
            if not isinstance(attachment, tuple) or len(attachment) != 3:
                raise ValueError(
                    "Expected filename/content/mimetype attachment."
                )

            filename, content, mimetype = attachment

            if isinstance(content, str):
                content = content.encode("utf-8")

            attachments.append({
                "filename": filename,
                "content": base64.b64encode(content).decode("ascii"),
                "content_type": mimetype,
            })

        if attachments:
            payload["attachments"] = attachments

        request = Request(
            "https://api.resend.com/emails",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json",
                "User-Agent": "Brewnook/1.0",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=settings.EMAIL_TIMEOUT) as response:
                data = json.load(response)
        except HTTPError as exc:
            raise RuntimeError(
                f"Resend rejected the email (HTTP {exc.code})."
            ) from None
        except URLError:
            raise RuntimeError("Resend could not be reached.") from None

        if not isinstance(data, dict) or not data.get("id"):
            raise RuntimeError("Resend did not return a message ID.")