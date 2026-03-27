import os
from flask import Flask, render_template, request
from azure.communication.email import EmailClient
from azure.identity import DefaultAzureCredential

app = Flask(__name__)

ACS_ENDPOINT = os.getenv("ACS_ENDPOINT")
ACS_SENDER_ADDRESS = os.getenv("ACS_SENDER_ADDRESS")


def send_email(to_email, subject, body):
    credential = DefaultAzureCredential()
    client = EmailClient(ACS_ENDPOINT, credential)

    message = {
        "senderAddress": ACS_SENDER_ADDRESS,
        "recipients": {
            "to": [
                {"address": to_email}
            ]
        },
        "content": {
            "subject": subject,
            "plainText": body,
            "html": f"""
            <html>
              <body>
                <p>{body}</p>
              </body>
            </html>
            """
        }
    }

    poller = client.begin_send(message)
    result = poller.result()
    return result


@app.route("/", methods=["GET", "POST"])
def index():
    status = None
    error = None

    if request.method == "POST":
        to_email = request.form.get("to_email", "").strip()
        subject = request.form.get("subject", "").strip()
        body = request.form.get("body", "").strip()

        if not to_email or not subject or not body:
            error = "Todos los campos son obligatorios."
        else:
            try:
                result = send_email(to_email, subject, body)
                status = f"Correo enviado correctamente. Resultado: {result}"
            except Exception as ex:
                error = f"Ocurrió un error: {str(ex)}"

    return render_template("index.html", status=status, error=error)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
