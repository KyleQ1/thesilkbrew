from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
import random

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

def get_potion_color(potion_type: list[int]):
    if potion_type == [100, 0, 0, 0]:
        return "red"
    elif potion_type == [0, 100, 0, 0]:
        return "green"
    elif potion_type == [0, 0, 100, 0]:
        return "blue"
    elif potion_type == [0, 0, 0, 100]:
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
            print(potion.potion_type)
            if color != None:
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_{color}_potions = num_{color}_potions + {potion.quantity}"))
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_{color}_ml = num_{color}_ml - {potion.quantity * 100}"))

    return "OK"

def easy_bottle_plan(red_ml, green_ml, blue_ml):
    """
    Bottles all barrels into red potions.
    """
    purchase_plan = []
    if red_ml > 100:
        purchase_plan.append({
            "potion_type": [100, 0, 0, 0],
            "quantity": (red_ml // 100),
        })
    if green_ml > 100:
        purchase_plan.append({
            "potion_type": [0, 100, 0, 0],
            "quantity": (green_ml // 100),
        })
    if blue_ml > 100:
        purchase_plan.append({
            "potion_type": [0, 0, 100, 0],
            "quantity": (blue_ml // 100),
        })
    
    print("Bottling Plan: ", purchase_plan, flush=True)

    return purchase_plan

def get_ml():
    with db.engine.begin() as connection:
        return connection.execute(sqlalchemy.text("""SELECT num_red_ml, num_green_ml, num_blue_ml, num_dark_ml FROM global_inventory""")).first()


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
    red, green, blue, dark = get_ml()
    return easy_bottle_plan(red, green, blue)
    

"""
def random_bottle_order(red_ml, green_ml, blue_ml):
    colors = ['red', 'blue', 'green']
    color1 = random.sample(colors)
    color2 = random.sample(colors)
    while color2 == color1:
        color2 = random.sample(colors)
    total = 100
    first = random.randint(1, 100)
    second = random.randint(1, 100 - first)
    third = total - first - second
    return {
        color1: first,
        color2: second,
        colors[3 - colors.index(color1) - colors.index(color2)]: third
    }
"""  

if __name__ == "__main__":
    print(get_bottle_plan())