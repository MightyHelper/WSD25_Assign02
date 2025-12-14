from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from ..db.models import Order
from app.storage.base import get_session
from app.security.dependencies import get_current_user
from app.db.models import User

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])

class OrderIn(BaseModel):
    id: str
    user_id: str
    paid: bool = False

    model_config = {"extra": "ignore", "from_attributes": True}

class OrderOut(BaseModel):
    id: str
    user_id: str
    paid: bool

    model_config = {"extra": "ignore", "from_attributes": True}

@router.post("/", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def create_order(o: OrderIn, current_user: User = Depends(get_current_user)):
    async with get_session() as session:
        order = Order(id=o.id, user_id=o.user_id, paid=o.paid)
        session.add(order)
        await session.commit()
        await session.refresh(order)
        return OrderOut.model_validate(order)

@router.get("/{order_id}", response_model=OrderOut)
async def get_order(order_id: str):
    async with get_session() as session:
        order = await session.get(Order, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return OrderOut.model_validate(order)
