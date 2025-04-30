import os
import imaplib
import time
import socket
import email
from email.header import decode_header
from typing import Generator
from dataclasses import dataclass
from datetime import datetime
from dateutil.parser import parse


@dataclass
class EmailMessage:
    uid: str
    subject: str
    from_address: str
    date: datetime
    body: str
    body_lines: list[str]


def connect_to_mailbox() -> imaplib.IMAP4_SSL:
    email_address = os.environ.get("EMAIL_USER")
    password = os.environ.get("EMAIL_PASSWORD")
    if not email_address or not password:
        raise ValueError(
            "Please set the EMAIL_USER and EMAIL_PASSWORD environment variables."
        )

    mail = imaplib.IMAP4_SSL("imap.mail.me.com")
    mail.login(email_address, password)
    return mail


def _get_email_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            if "attachment" in content_disposition:
                continue

            if content_type == "text/plain":
                body = part.get_payload(decode=True)
                return body.decode("utf-8", errors="ignore") if body else ""
            elif content_type == "text/html":
                body = part.get_payload(decode=True)
                return body.decode("utf-8", errors="ignore") if body else ""
    else:
        body = msg.get_payload(decode=True)
        return body.decode("utf-8", errors="ignore") if body else ""
    return ""


def monitor_emails(
    mail: imaplib.IMAP4_SSL = connect_to_mailbox(),
) -> Generator[tuple[imaplib.IMAP4_SSL, EmailMessage], None, None]:
    last_seen_uid = 0
    while True:
        try:
            mail.select("INBOX")
            status, uids = mail.uid("SEARCH", None, "ALL")
            if status != "OK":
                print("Error searching for messages.")
                time.sleep(60)
                continue

            new_uids = [
                int(uid) for uid in (uids[0] or "").split() if int(uid) > last_seen_uid
            ]
            if new_uids:
                print(f"Found {len(new_uids)} new emails.")
                for uid in new_uids:
                    # Fetch by UID
                    status, msg_data = mail.uid("FETCH", str(uid), "(BODY[])")
                    if status != "OK":
                        print(f"Error fetching message UID {uid}.")
                        continue

                    # Parse the email
                    email_message = email.message_from_bytes(msg_data[0][1])

                    # Decode the email subject
                    subject, encoding = decode_header(email_message["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding or "utf-8")

                    # Get sender, date, and body
                    from_address = email.utils.parseaddr(email_message["From"])[1]
                    date = email_message.get("Date")
                    parsed_date = parse(date)
                    body = _get_email_body(email_message)

                    yield (
                        mail,
                        EmailMessage(
                            uid=str(uid),
                            subject=subject,
                            from_address=from_address,
                            date=parsed_date,
                            body=body,
                            body_lines=body.splitlines(),
                        ),
                    )

                    last_seen_uid = max(last_seen_uid, uid)

            refresh_interval = 30
            print(f"Checking again in {refresh_interval} seconds.")
            time.sleep(refresh_interval)

        except (mail.abort, mail.error, socket.error) as e:
            print(f"Connection error: {e}. Attempting to reconnect in 60 seconds...")
            time.sleep(60)
            mail = connect_to_mailbox()
            if mail is None:
                print("Reconnection failed. Exiting.")
                break


def move_to_trash(mail: imaplib.IMAP4_SSL, uid: str) -> None:
    mail.uid("MOVE", uid, '"Deleted Messages"')
