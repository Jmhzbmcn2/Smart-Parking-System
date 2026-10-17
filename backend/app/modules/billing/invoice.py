import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

from app.core import clock
from app.core.config import BACKEND_DIR
from app.modules.billing.models import Payment
from app.modules.billing.service import billable_hours, minutes
from app.modules.sessions.models import ParkingSession


def _vnd(amount: int) -> str:
    return f"{amount:,}".replace(",", ".") + " VND"


def _fmt(at: datetime) -> str:
    return at.astimezone(clock.TZ).strftime("%H:%M:%S %d/%m/%Y")


def build(payment: Payment, session: ParkingSession, email: str) -> EmailMessage:
    assert session.exit_at is not None and payment.paid_at is not None
    hours = billable_hours(minutes(session.entry_at, session.exit_at))
    message = EmailMessage()
    message["Subject"] = f"Hóa đơn SPMS #{payment.id}"
    message["From"] = os.getenv("SPMS_MAIL_FROM", "spms@localhost")
    message["To"] = email
    message.set_content(
        f"Hóa đơn gửi xe SPMS\n"
        f"Mã thanh toán: {payment.id}\n"
        f"Biển số: {session.plate}\n"
        f"Giờ vào: {_fmt(session.entry_at)}\n"
        f"Giờ ra: {_fmt(session.exit_at)}\n"
        f"Số giờ tính phí: {hours}\n"
        f"Số tiền: {_vnd(payment.amount)}\n"
        f"Phương thức: {payment.method}\n"
        f"Thanh toán lúc: {_fmt(payment.paid_at)}\n",
        cte="8bit",
    )
    return message


def send(payment: Payment, session: ParkingSession, email: str) -> tuple[datetime, Path | None]:
    """SP-3.3: SMTP when SPMS_SMTP_HOST is set, otherwise a file in the outbox directory."""
    message = build(payment, session, email)
    host = os.getenv("SPMS_SMTP_HOST")
    if host:
        user = os.getenv("SPMS_SMTP_USER")
        with smtplib.SMTP(host, int(os.getenv("SPMS_SMTP_PORT", "587"))) as smtp:
            if user:
                smtp.starttls()
                smtp.login(user, os.getenv("SPMS_SMTP_PASSWORD", ""))
            smtp.send_message(message)
        return clock.now(), None
    outbox = Path(os.getenv("SPMS_OUTBOX_DIR", BACKEND_DIR / "outbox"))
    outbox.mkdir(parents=True, exist_ok=True)
    path = outbox / f"{payment.id}.eml"
    path.write_bytes(bytes(message))
    return clock.now(), path
