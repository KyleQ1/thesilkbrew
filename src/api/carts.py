from fastapi import APIRouter, Depends, Request
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
    print(f"visit_id: {visit_id} customers: {customers}", flush=True)

    return "OK"


@router.post("/")
def create_cart(new_cart: Customer):
    """ """
    print("create_cart")
    print(f"new_cart: {new_cart}", flush=True)
    return {"cart_id": 1}


class CartItem(BaseModel):
    quantity: int

carttable = []
@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """
    /carts/3/items/FUNKY_POT 
    """
    print("set_item_quantity")
    print(f"cart_id: {cart_id} item_sku: {item_sku} cart_item: {cart_item}", flush=True)
    carttable.append({"cart_id": cart_id, "item_sku": item_sku, "quantity": cart_item.quantity})
    return "OK"


class CartCheckout(BaseModel):
    payment: str

def get_color(item_sku):
    if "GREEN" in item_sku:
        return "green"
    elif "RED" in item_sku:
        return "red"
    elif "BLUE" in item_sku:
        return "blue"
    elif "DARK" in item_sku:
        return "dark"
    else:
        return None
    
@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """
    /carts/3/checkout 
    """
    print("checkout")
    print(f"cart_id: {cart_id} cart_checkout: {cart_checkout}", flush=True)
    for item in carttable:
        if item["cart_id"] == cart_id:
            quantity = item["quantity"]
            item_sku = item["item_sku"]
    color = get_color(item_sku)
        
    # Link this gold to catalog gold

    gold_paid = 50 * quantity
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(f"""UPDATE global_inventory SET gold = gold + {gold_paid}"""))
        if color:
            connection.execute(sqlalchemy.text(f"""UPDATE global_inventory SET num_{color}_potions = num_{color}_potions - {quantity}"""))
        else:
            print("Fuck up color", item_sku=["item_sku"], flush=True)
    return {"total_potions_bought": quantity, "total_gold_paid": gold_paid}
