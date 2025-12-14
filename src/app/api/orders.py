from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from ..db.models import Order
from app.db.base import get_session
from app.security.dependencies import get_current_user
from app.db.models import User, BookOrderItem, Book

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

class ItemIn(BaseModel):
    book_id: str
    quantity: int

class ItemOut(BaseModel):
    id: str
    order_id: str
    book_id: str
    quantity: int

    model_config = {"extra": "ignore", "from_attributes": True}

@router.post("/", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def create_order(o: OrderIn, current_user: User = Depends(get_current_user)):
    async with get_session() as session:
        if current_user.type != 1:
            if o.user_id != current_user.id:
                raise HTTPException(status_code=403, detail="Forbidden")
            if o.paid:
                raise HTTPException(status_code=400, detail="Cannot create paid order")
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

@router.post("/{order_id}/items", response_model=ItemOut, status_code=201)
async def set_order_item(order_id: str, item: ItemIn, current_user: User = Depends(get_current_user)):
    async with get_session() as session:
        order = await session.get(Order, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        if order.paid:
            raise HTTPException(status_code=400, detail="Order already paid")
        if order.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Forbidden")
        # ensure book exists
        b = await session.get(Book, item.book_id)
        if not b:
            raise HTTPException(status_code=404, detail="Book not found")
        # find existing item
        from sqlalchemy import select
        stmt = select(BookOrderItem).where(BookOrderItem.order_id == order_id).where(BookOrderItem.book_id == item.book_id)
        res = await session.execute(stmt)
        existing = res.scalars().first()
        if item.quantity <= 0:
            if existing:
                await session.delete(existing)
                await session.commit()
                return ItemOut(id=existing.id, order_id=order_id, book_id=item.book_id, quantity=0)
            raise HTTPException(status_code=400, detail="Quantity invalid")
        if existing:
            existing.quantity = item.quantity
            session.add(existing)
            await session.commit()
            await session.refresh(existing)
            return ItemOut.model_validate(existing)
        # create new
        import uuid
        new_id = str(uuid.uuid4())
        new = BookOrderItem(id=new_id, order_id=order_id, book_id=item.book_id, quantity=item.quantity)
        session.add(new)
        await session.commit()
        await session.refresh(new)
        return ItemOut.model_validate(new)

@router.post("/{order_id}/pay", response_model=OrderOut)
async def pay_order(order_id: str, current_user: User = Depends(get_current_user)):
    async with get_session() as session:
        order = await session.get(Order, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        if order.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Forbidden")
        if order.paid:
            raise HTTPException(status_code=400, detail="Order already paid")
        # simple validation: must have at least one item
        from sqlalchemy import select
        stmt = select(BookOrderItem).where(BookOrderItem.order_id == order_id)
        res = await session.execute(stmt)
        items = res.scalars().all()
        if not items:
            raise HTTPException(status_code=400, detail="Order is empty")
        # mark as paid
        order.paid = True
        session.add(order)
        await session.commit()
        await session.refresh(order)
        return OrderOut.model_validate(order)
