import asyncio
from big_brother.services.mail import monitor_emails, move_to_trash
from big_brother.parsers.parse import parse_email
from big_brother.services.ynab_service import create_transactions
from big_brother.services.amex import monitor_amex


async def start_email_monitor():
    async for mail_client, email in monitor_emails():
        try:
            transaction = parse_email(email)
            if transaction:
                create_transactions([transaction])
                move_to_trash(mail_client, email.uid)
                print("Transaction submitted to YNAB")
        except Exception as e:
            print(f"Failed to parse email {email.date} {email.subject}")
            print(f"Error: {e}")


def main():
    async def run():
        await asyncio.gather(
            start_email_monitor(),
            monitor_amex(),
        )

    asyncio.run(run())


if __name__ == "__main__":
    main()
