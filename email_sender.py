import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders


def send_email_with_attachment(
    smtp_server,
    smtp_port,
    sender_email,
    sender_password,
    recipient_email,
    subject,
    body,
    attachment_bytes,
    attachment_filename
):
    """
    Mengirim email dengan lampiran (mis. PDF) lewat SMTP (STARTTLS).

    PENTING:
    - sender_email JUGA dipakai sebagai username login SMTP, jadi
      harus alamat yang sama dengan pemilik sender_password.
    - sender_password adalah App Password / password SMTP, diambil
      dari st.secrets di app.py -- JANGAN PERNAH ditulis langsung
      di dalam kode atau di-commit ke GitHub.
    """

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = subject

    msg.attach(
        MIMEText(body, "plain")
    )

    part = MIMEBase("application", "octet-stream")
    part.set_payload(attachment_bytes)
    encoders.encode_base64(part)

    part.add_header(
        "Content-Disposition",
        f"attachment; filename={attachment_filename}"
    )

    msg.attach(part)

    with smtplib.SMTP(smtp_server, smtp_port) as server:

        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(
            sender_email,
            recipient_email,
            msg.as_string()
        )
