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
    # TODO: test
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory"))
        green_potions = result.fetchone()[0]
    if green_potions == 0:
        return []

    return [
            {
                "sku": "GREEN_POTION_0",
                "name": "green potion",
                "quantity": green_potions,
                "price": 49,
                "potion_type": [0, 100, 0, 0],
            }
        ]
