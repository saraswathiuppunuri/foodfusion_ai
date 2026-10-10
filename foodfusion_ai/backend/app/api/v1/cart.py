from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.permissions import get_current_user
from app.models.entities import User, CartItem
from app.schemas.schemas import CartOut, CartItemAdd
from app.services.order_service import add_to_cart, get_cart_view, get_or_create_cart

router = APIRouter(prefix="/cart", tags=["Cart Management"])

@router.get("", response_model=CartOut)
def view_cart(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retrieves current customer's cart with server-calculated totals."""
    return get_cart_view(current_user, db)

@router.post("/items", response_model=CartOut)
def add_item(
    item_in: CartItemAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Adds a dish to the persistent cart, validating availability and restaurant consistency."""
    return add_to_cart(
        user=current_user,
        dish_id=item_in.dish_id,
        quantity=item_in.quantity,
        notes=item_in.customization_notes or "",
        db=db
    )

@router.delete("/items/{item_id}", response_model=CartOut)
def remove_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Removes a dish item from the cart."""
    cart = get_or_create_cart(current_user, db)
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart.id).first()
    if item:
        db.delete(item)
        db.commit()
    return get_cart_view(current_user, db)

@router.delete("", response_model=CartOut)
def clear_cart(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Clears all items in the customer's cart."""
    cart = get_or_create_cart(current_user, db)
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    cart.restaurant_id = None
    db.commit()
    return get_cart_view(current_user, db)
