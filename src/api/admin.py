from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    print("reset")
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("TRUNCATE global_inventory, carts, capacity, cart_items, potions"))
        connection.execute(sqlalchemy.text("""INSERT INTO capacity (potion_capacity, ml_capacity)
                                            VALUES (50, 10000)"""))
        connection.execute(sqlalchemy.text("""INSERT INTO global_inventory (gold)
                                            VALUES (100)"""))
    return "OK"

