from fastapi import HTTPException, APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from sqlalchemy.orm import Session
from src import database as db

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: str = "timestamp",
    sort_order: str = "desc"
):

    query = (
        sqlalchemy.select(
            db.cart_items.c.id,
            db.potions.c.sku,
            db.carts.c.customer_name,
            (db.potions.c.price * db.cart_items.c.quantity).label("line_item_total"),
            db.cart_items.c.created_at
        ).select_from(
            db.cart_items.join(db.potions, db.cart_items.c.grab_potion_id == db.potions.c.id)
                    .join(db.carts, db.cart_items.c.cart_id == db.carts.c.id))
    )
   
    # Applying filters
    if customer_name:
        query = query.where(db.carts.c.customer_name.ilike(f"%{customer_name}%"))
    if potion_sku:
        query = query.where(db.potions.c.sku.ilike(f"%{potion_sku}%"))

    # Sorting
    order_function = sqlalchemy.desc if sort_order == 'desc' else sqlalchemy.asc
    if sort_col == "timestamp":
        query.order_by(order_function(db.cart_items.c.created_at))
    elif sort_col == "line_item_total":
        query.order_by(order_function(sqlalchemy.literal_column("line_item_total")))
    elif sort_col == "item_sku":
        query.order_by(order_function(db.potions.c.sku))
    elif sort_col == "customer_name":
        query.order_by(order_function(db.carts.c.customer_name))

    # Pagination logic
    page_size = 5
    page_number = int(search_page) if search_page.isdigit() else 0
    query = query.limit(page_size).offset(page_number * page_size)

    # Executing query
    with db.engine.connect() as connection:
        results = connection.execute(query).fetchall()

    # Format results
    formatted_results = [{
        "line_item_id": result.id,
        "item_sku": result.sku,
        "customer_name": result.customer_name,
        "line_item_total": int(result.line_item_total),  # Ensure conversion to int if needed
        "timestamp": result.created_at.isoformat(),
    } for result in results]

    # Pagination response (simplified, not checking for previous/next existence)
    return {
        "previous": str(max(0, page_number - 1)),
        "next": str(page_number + 1) if len(results) == page_size else "",
        "results": formatted_results
    }


class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """
    print("post_visits")
    with db.engine.begin() as connection:
        for customer in customers:
            connection.execute(sqlalchemy.text(f"""INSERT INTO customers (name, class, level) 
                                                VALUES (:name, :class, :level)"""),
                                                {"name": customer.customer_name, 
                                                "class": customer.character_class, "level": customer.level})
    return "OK"

carttable = []
updateid = 0
@router.post("/")
def create_cart(new_cart: Customer):
    """ """
    global updateid
    print("create_cart")
    print(f"new_cart: {new_cart}", flush=True)
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(f"""INSERT INTO carts (customer_name, character_class, level) 
                                               VALUES (:customer_name, :character_class, :level)
                                                RETURNING id"""), 
                                               {"customer_name": new_cart.customer_name, 
                                                "character_class": new_cart.character_class, 
                                                "level": new_cart.level})
        return {"cart_id": result.scalar()}


class CartItem(BaseModel):
    quantity: int

@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """
    /carts/3/items/FUNKY_POT 
    """
    print("set_item_quantity")
    print(f"cart_id: {cart_id} item_sku: {item_sku} cart_item: {cart_item}", flush=True)
    # TODO: Check if we have enough potions in stock. Shouldn't be a problem for this project.

    with db.engine.begin() as connection:
        id = connection.execute(sqlalchemy.text("""SELECT id
                                                FROM potions
                                                WHERE sku = :sku"""), {"sku": item_sku}).scalar()
        if id is None:
            print("error with catalog or potion table idk")
            raise HTTPException(status_code=404, detail="Potion not found")
        connection.execute(sqlalchemy.text(f"""INSERT INTO cart_items (cart_id, grab_potion_id, quantity) 
                                            VALUES (:cart_id, :potion_id, :quantity)"""), 
                                            {"cart_id": cart_id, "potion_id": id, "quantity": cart_item.quantity})
    return "OK"

class CartCheckout(BaseModel):
    payment: str
    
@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """
    Process a checkout for a given cart_id and apply changes to inventory and global financial records.
    """
    print("checkout")
    with db.engine.begin() as connection:
        # Fetch all items in the cart and their corresponding potion details from potions
        result = connection.execute(
            sqlalchemy.text("""
                SELECT ci.quantity, p.price, p.id
                FROM cart_items ci
                JOIN potions p ON p.id = ci.grab_potion_id
                WHERE ci.cart_id = :cart_id
            """),
            {"cart_id": cart_id}
        ).first()

        if result == None:
            raise HTTPException(status_code=404, detail="No items found in the cart or invalid cart ID")

        order_quantity, gold, gp_id = result
        total_gold = order_quantity * gold
        print(f"order_quantity: {order_quantity} total_gold: {total_gold} gp_id: {gp_id}", flush=True)
        connection.execute(
            sqlalchemy.text("""INSERT INTO potion_ledger (quantity, grab_potion_id)
                                VALUES (:new_quantity, :id)"""),
            {"new_quantity": -order_quantity, "id": gp_id}
        )
        connection.execute(
            sqlalchemy.text("INSERT INTO inventory_ledger (gold) VALUES (:gold)"),
            {"gold": total_gold}
        )

        return {"total_potions_bought": order_quantity, "total_gold_paid": total_gold}
