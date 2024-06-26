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
        connection.execute(sqlalchemy.text("TRUNCATE inventory_ledger, carts, capacity, cart_items, potion_ledger"))
        connection.execute(sqlalchemy.text("""INSERT INTO capacity (id, potion_capacity, ml_capacity)
                                            VALUES (1, 50, 10000)"""))
        connection.execute(sqlalchemy.text("""INSERT INTO inventory_ledger (gold)
                                            VALUES (100)"""))
    return "OK"

