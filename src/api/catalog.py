from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    print("get_catalog", flush=True)
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory"))
        green_potions = result.fetchone()['num_green_potions']

    return [
            {
                "sku": "GREEN_POTION_0",
                "name": "green potion",
                "quantity": green_potions,
                "price": 49,
                "potion_type": [0, 0, 100, 0],
            }
        ]
