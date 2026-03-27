import os
import base64
import json
from flask import Flask, render_template, request
from azure.communication.email import EmailClient
from azure.identity import DefaultAzureCredential

app = Flask(__name__)

ACS_ENDPOINT = os.getenv("ACS_ENDPOINT")
ACS_SENDER_ADDRESS = os.getenv("ACS_SENDER_ADDRESS")


def get_user_info(req):
    principal = req.headers.get("X-MS-CLIENT-PRINCIPAL")

    if not principal:
        return None, None

    decoded = base64.b64decode(principal)
    user_data = json.loads(decoded)

    name = None
    email = None

    for claim in user_data.get("claims", []):
        if claim["typ"] == "name":
            name = claim["val"]
        if claim["typ"] in ["preferred_username", "emails"]:
            email = claim["val"]

    return name, email


def send_email(to_email, subject, body):
    credential = DefaultAzureCredential()
    client = EmailClient(ACS_ENDPOINT, credential)

    message = {
        "senderAddress": ACS_SENDER_ADDRESS,
        "recipients": {
            "to": [{"address": to_email}]
        },
        "content": {
            "subject": subject,
            "plainText": body,
            "html": f"<p>{body}</p>"
        }
    }

    poller = client.begin_send(message)
    return poller.result()


@app.route("/", methods=["GET", "POST"])
def index():
    success = None
    tracking_id = None
    error = None

    user_name, user_email = get_user_info(request)

    if request.method == "POST":
        to_email = request.form.get("to_email", "").strip()
        subject = request.form.get("subject", "").strip()
        body = request.form.get("body", "").strip()

        if not to_email or not subject or not body:
            error = "Todos los campos son obligatorios."
        else:
            try:
                result = send_email(to_email, subject, body)
                success = "Correo enviado correctamente."
                tracking_id = result.get("id")
            except Exception as ex:
                error = str(ex)

    return render_template(
        "index.html",
        success=success,
        tracking_id=tracking_id,
        error=error,
        sender_address=ACS_SENDER_ADDRESS,
        user_name=user_name,
        user_email=user_email
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
