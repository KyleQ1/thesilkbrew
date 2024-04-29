from fastapi import HTTPException, APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
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
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    print("search_orders")
    print(f"customer_name: {customer_name} potion_sku: {potion_sku} search_page: {search_page} sort_col: {sort_col} sort_order: {sort_order}", flush=True)
    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
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
