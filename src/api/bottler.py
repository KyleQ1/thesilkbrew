from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

def get_potion_color(potion_type: list[int]):
    if potion_type == [1, 0, 0, 0]:
        return "red"
    elif potion_type == [0, 1, 0, 0]:
        return "green"
    elif potion_type == [0, 0, 1, 0]:
        return "blue"
    elif potion_type == [0, 0, 0, 1]:
        return "dark"
    else:
        print("Invalid potion type when bottling", flush=True)
        return None

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """ """
    print("post_deliver_bottles")
    print(f"potions delievered: {potions_delivered} order_id: {order_id}", flush=True)
    with db.engine.begin() as connection:
        for potion in potions_delivered:
            color = get_potion_color(potion.potion_type)
            if color != None:
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_{color}_potions = num_{color}_potions + {potion.quantity}"))
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_{color}_ml = num_{color}_ml - {potion.quantity * 100}"))

    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.
    print("get_bottle_plan", flush=True)
    green_ml_available = False
    green_ml = 0
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory"))
        for row in result:
            green_ml = row[0]
            if green_ml >= 100:  
                green_ml_available = True
                break

    # Create 5 green potions if green ml is available.
    if green_ml_available:
        return [
            {
                "potion_type": [0, 1, 0, 0],
                "quantity": (green_ml // 100),
            }
        ]
    # Otherwise, create 0 potions.
    else:
        return []
        

if __name__ == "__main__":
    print(get_bottle_plan())