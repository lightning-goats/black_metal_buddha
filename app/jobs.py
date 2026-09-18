from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from .fulfillment.printful import PrintfulClient
from .models import Job, Order
from .notifications.email import EmailSender
from .settings import Settings, settings


def _retry_or_fail(session: Session, job: Job, exc: Exception) -> None:
    job.attempt_count += 1
    job.state = "PENDING" if job.attempt_count < 8 else "FAILED"
    delay = min(60, 2 ** min(job.attempt_count, 6))
    job.next_attempt_at = datetime.now(timezone.utc) + timedelta(minutes=delay)
    job.last_error = str(exc)[:2000]
    session.commit()


def process_submit_printful_job(
    session: Session,
    job: Job,
    *,
    config: Settings = settings,
    client: PrintfulClient | None = None,
) -> None:
    order = session.get(Order, job.order_id)
    if order is None:
        job.state = "FAILED"
        job.last_error = "Order not found"
        session.commit()
        return

    if order.payment_state != "COMPLETED":
        job.state = "FAILED"
        job.last_error = "Order is not paid"
        session.commit()
        return

    if config.printful_mode == "disabled":
        job.state = "PENDING"
        job.last_error = "Printful disabled by configuration"
        job.next_attempt_at = datetime.now(timezone.utc) + timedelta(hours=1)
        session.commit()
        return

    pf = client or PrintfulClient(config)
    try:
        existing = pf.get_order_by_external_id(order.order_number)
        data = existing or pf.create_draft_order(order)
        order.printful_order_id = str(data.get("id") or "")
        order.fulfillment_state = "DRAFT"
        order.order_state = "FULFILLMENT_SUBMITTED"
        order.submitted_to_printful_at = datetime.now(timezone.utc)
        job.state = "COMPLETED"
        job.last_error = None
        session.commit()
    except Exception as exc:
        _retry_or_fail(session, job, exc)


def process_email_job(
    session: Session,
    job: Job,
    *,
    config: Settings = settings,
    sender: EmailSender | None = None,
) -> None:
    order = session.get(Order, job.order_id)
    if order is None:
        job.state = "FAILED"
        job.last_error = "Order not found"
        session.commit()
        return

    if config.email_mode == "disabled":
        job.state = "PENDING"
        job.last_error = "Transactional email disabled by configuration"
        job.next_attempt_at = datetime.now(timezone.utc) + timedelta(hours=1)
        session.commit()
        return

    mailer = sender or EmailSender(config)
    try:
        if job.job_type == "SEND_ORDER_CONFIRMATION":
            mailer.send_order_confirmation(order)
        elif job.job_type == "SEND_SHIPPING_NOTIFICATION":
            mailer.send_shipping_notification(order)
        elif job.job_type.startswith("SEND_REFUND_CONFIRMATION"):
            mailer.send_refund_confirmation(order)
        else:
            raise RuntimeError(f"Unknown email job type: {job.job_type}")

        job.state = "COMPLETED"
        job.last_error = None
        session.commit()
    except Exception as exc:
        _retry_or_fail(session, job, exc)


def process_pending_jobs(
    session: Session,
    *,
    limit: int = 20,
    config: Settings = settings,
) -> int:
    now = datetime.now(timezone.utc)
    jobs = session.scalars(
        select(Job)
        .where(Job.state == "PENDING", Job.next_attempt_at <= now)
        .order_by(Job.created_at)
        .limit(limit)
    ).all()

    for job in jobs:
        if job.job_type == "SUBMIT_PRINTFUL_ORDER":
            process_submit_printful_job(session, job, config=config)
        elif job.job_type.startswith("SEND_"):
            process_email_job(session, job, config=config)
    return len(jobs)
