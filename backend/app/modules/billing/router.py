from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.audit import service as audit
from app.modules.auth.models import User
from app.modules.auth.router import current_user, require_role
from app.modules.billing import service
from app.modules.billing.models import Payment
from app.modules.billing.schemas import PaymentOut, PriceIn, PriceOut
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
        qr_payload=f"SPMS|{payment.id}|{payment.amount}",
    )


@router.get("/payments/{payment_id}", dependencies=[staff])
def get_payment(payment_id: int, db: Annotated[Session, Depends(get_db)]) -> PaymentOut:
    payment = db.get(Payment, payment_id)
    if payment is None:
        raise HTTPException(404, "Payment not found")
    return payment_out(db, payment)
