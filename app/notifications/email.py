from __future__ import annotations

import smtplib
from email.message import EmailMessage

from ..models import Order, Shipment
from ..settings import Settings, settings


class EmailConfigurationError(RuntimeError):
    pass


class EmailSender:
    def __init__(self, config: Settings = settings):
        self.config = config

    def _send(self, *, to: str, subject: str, body: str) -> None:
        if self.config.email_mode == "disabled":
            raise EmailConfigurationError("Transactional email is disabled")

        if self.config.email_mode == "console":
            # Development-only transport. Do not log shipping addresses or payment data.
            print(f"[email] to={to} subject={subject}\n{body}")
            return

        if not self.config.smtp_host or not self.config.email_from:
            raise EmailConfigurationError("SMTP is not configured")

        message = EmailMessage()
        message["From"] = self.config.email_from
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)

        with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port, timeout=20) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            if self.config.smtp_username:
                smtp.login(self.config.smtp_username, self.config.smtp_password or "")
            smtp.send_message(message)

    def send_order_confirmation(self, order: Order) -> None:
        body = (
            f"Thank you for your Black Metal Buddha order {order.order_number}.\n\n"
            f"Payment received: {order.currency} {order.total_cents / 100:.2f}\n"
            "Your order will move to fulfillment after payment confirmation.\n\n"
            f"Order status: {self.config.public_base_url}/orders/{order.order_number}\n\n"
            "All things pass."
        )
        self._send(
            to=order.email,
            subject=f"Black Metal Buddha order {order.order_number}",
            body=body,
        )

    def send_shipping_notification(self, order: Order, shipment: Shipment) -> None:
        tracking = ""
        if shipment.tracking_number:
            tracking += f"Tracking number: {shipment.tracking_number}\n"
        if shipment.tracking_url:
            tracking += f"Tracking: {shipment.tracking_url}\n"

        body = (
            f"A shipment for Black Metal Buddha order {order.order_number} is on the way.\n\n"
            f"{tracking}"
            f"Order status: {self.config.public_base_url}/orders/{order.order_number}\n"
        )
        self._send(
            to=order.email,
            subject=f"Black Metal Buddha order {order.order_number} shipped",
            body=body,
        )

    def send_refund_confirmation(self, order: Order) -> None:
        body = (
            f"A refund for Black Metal Buddha order {order.order_number} has completed.\n\n"
            f"Refunded total recorded: {order.currency} {order.refunded_cents / 100:.2f}\n"
            "Your financial institution may take additional time to display the credit."
        )
        self._send(
            to=order.email,
            subject=f"Refund completed for {order.order_number}",
            body=body,
        )
