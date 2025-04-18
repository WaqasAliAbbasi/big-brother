from big_brother.services.mail import monitor_emails, move_to_trash
from big_brother.parsers.parse import parse_email
from big_brother.services.ynab_service import submit_transaction


def main():
    for mail_client, email in monitor_emails():
        try:
            transaction = parse_email(email)
            if transaction:
                submit_transaction(transaction)
                move_to_trash(mail_client, email.uid)
                print("Transaction submitted to YNAB")
        except Exception as e:
            print(f"Failed to parse email {email.date} {email.subject}")
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
