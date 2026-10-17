from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.audit import service as audit
from app.modules.auth.models import User
from app.modules.auth.router import current_user, require_device, require_role
from app.modules.billing import invoice, service
from app.modules.billing.models import Payment
from app.modules.billing.schemas import (
    InvoiceRequest,
    InvoiceResult,
    MockResult,
    PaymentOut,
    PriceIn,
    PriceOut,
)
from app.modules.billing.service import AlreadyPaid
from app.modules.sessions import service as sessions
from app.modules.sessions.models import ParkingSession

router = APIRouter(tags=["billing"])

admin_role = require_role("admin")
staff = Depends(require_role("attendant", "admin"))


@router.get("/prices/current", dependencies=[Depends(current_user)])
def price_current(db: Annotated[Session, Depends(get_db)]) -> PriceOut:
    return PriceOut.model_validate(service.current_price(db))


@router.get("/prices", dependencies=[Depends(admin_role)])
def prices(db: Annotated[Session, Depends(get_db)]) -> list[PriceOut]:
    return [PriceOut.model_validate(p) for p in service.list_prices(db)]


@router.post("/prices", status_code=201)
def set_price(
    body: PriceIn,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(admin_role)],
) -> PriceOut:
    old = service.current_price(db)
    price = service.add_price(db, body.first_hours, body.first_price, body.per_hour, user.username)
    reason = (
        f"Giá cũ {old.first_hours}h/{old.first_price}/{old.per_hour}"
        f" -> giá mới {price.first_hours}h/{price.first_price}/{price.per_hour} (VND)"
    )
    audit.record(db, user, "price_change", "-", reason)
    db.commit()
    return PriceOut.model_validate(price)


def payment_out(db: Session, payment: Payment) -> PaymentOut:
    session = db.get(ParkingSession, payment.session_id)
    assert session is not None
    return PaymentOut(
        id=payment.id,
        session_id=payment.session_id,
        plate=session.plate,
        gate_id=payment.gate_id,
        amount=payment.amount,
        status=payment.status,
        method=payment.method,
        paid_at=payment.paid_at,
        qr_payload=f"SPMS|{payment.id}|{payment.amount}",
    )


@router.get("/payments/{payment_id}", dependencies=[staff])
def get_payment(payment_id: int, db: Annotated[Session, Depends(get_db)]) -> PaymentOut:
    return payment_out(db, find_payment(db, payment_id))


def find_payment(db: Session, payment_id: int) -> Payment:
    payment = db.get(Payment, payment_id)
    if payment is None:
        raise HTTPException(404, "Payment not found")
    return payment


@router.post("/payments/{payment_id}/mock", dependencies=[Depends(require_device)])
def mock_gateway(
    payment_id: int, body: MockResult, db: Annotated[Session, Depends(get_db)]
) -> PaymentOut:
    """Stands in for the payment gateway callback, so it has no authentication."""
    payment = find_payment(db, payment_id)
    try:
        if body.success:
            sessions.complete_exit(db, payment, "qr")
        else:
            sessions.fail_payment(db, payment)
    except AlreadyPaid as exc:
        raise HTTPException(409, "Payment already paid") from exc
    db.commit()
    return payment_out(db, payment)


@router.post("/payments/{payment_id}/cash")
def pay_cash(
    payment_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role("attendant", "admin"))],
) -> PaymentOut:
    """HZ-03: the attendant settles the payment in cash; the audit row commits with it."""
    payment = find_payment(db, payment_id)
    try:
        event = sessions.complete_exit(db, payment, "cash")
    except AlreadyPaid as exc:
        raise HTTPException(409, "Payment already paid") from exc
    audit.record(db, user, "cash_payment", payment.gate_id, "Thu tiền mặt", event.plate)
    db.commit()
    return payment_out(db, payment)


@router.post("/payments/{payment_id}/invoice", status_code=202)
def send_invoice(
    payment_id: int, body: InvoiceRequest, db: Annotated[Session, Depends(get_db)]
) -> InvoiceResult:
    """Open: the driver asks for it at the exit kiosk after paying."""
    payment = find_payment(db, payment_id)
    if payment.status != "paid":
        raise HTTPException(409, "Payment is not paid yet")
    session = db.get(ParkingSession, payment.session_id)
    assert session is not None
    sent_at, path = invoice.send(payment, session, body.email)
    return InvoiceResult(sent_at=sent_at, path=path.name if path else None)
