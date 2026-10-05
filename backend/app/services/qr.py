"""
Minimal QR code helper.

Payload is a small JSON object containing only the verification
token. No PII, no JWT, no password, no credentials.
"""

import base64
import io
import json

import qrcode


def make_qr_base64(payload_dict, box_size=6, border=2):
    """
    Return a base64-encoded PNG of a QR code containing the given
    payload dict as compact JSON.
    """

    payload = json.dumps(payload_dict, separators=(",", ":"))

    img = qrcode.make(
        payload,
        box_size=box_size,
        border=border
    )

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    encoded = base64.b64encode(buffer.read()).decode("ascii")

    return encoded