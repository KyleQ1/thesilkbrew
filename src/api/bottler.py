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

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """ """
    print("post_deliver_bottles")
    print(f"potions delievered: {potions_delivered} order_id: {order_id}", flush=True)
    with db.engine.begin() as connection:
        for potion in potions_delivered:
            print(potion.potion_type)
            # Shit fuck balls
            grab_potion_id = connection.execute(sqlalchemy.text("""
                SELECT id FROM grab_potions 
                WHERE r = :r AND g = :g AND b = :b AND d = :d
            """), {"r": potion.potion_type[0], "g": potion.potion_type[1],
                   "b": potion.potion_type[2], "d": potion.potion_type[3]}).scalar()

            if grab_potion_id is None:
                continue  # Skip if no matching potion recipe is found

            # check if potion type exists update else insert
            connection.execute(sqlalchemy.text(f"""INSERT INTO potion_ledger (quantity, grab_potion_id)
                                                VALUES (:quantity, :id)"""), 
                                                [{"quantity": potion.quantity, "id": grab_potion_id}])
            connection.execute(sqlalchemy.text(f"""INSERT INTO global_inventory (num_red_ml, num_green_ml, num_blue_ml, num_dark_ml) 
                                                VALUES (:r, :g, :b, :d)"""), 
                                                [{"r": -potion.potion_type[0] * potion.quantity, "g": -potion.potion_type[1] * potion.quantity, 
                                                    "b": -potion.potion_type[2] * potion.quantity, "d": -potion.potion_type[3] * potion.quantity}])

    return "OK"

def calculate_max_batches(red_ml, green_ml, blue_ml, dark_ml, r, g, b, d):
    ingredients_available = [red_ml, green_ml, blue_ml, dark_ml]
    recipe_requirements = [r, g, b, d]

    max_batches = float('inf')  

    for available, required in zip(ingredients_available, recipe_requirements):
        if required > 0: # Skip if no ingredient is required
            max_batches = min(max_batches, available // required)

    return max_batches


def efficient_bottle_plan(red_ml, green_ml, blue_ml, dark_ml, potion_capacity):
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("""SELECT r, g, b, d, sku FROM grab_potions""")).fetchall()
        random.shuffle(result)  # Shuffle to randomize initial selection

        selected_potions = []
        purchase_plan = []
        max_batches_allowed = potion_capacity // 4

        # Select and compute production for up to 6 potions that can be initially made
        for potion in result:
            if len(selected_potions) >= 6 or potion_capacity <= 0:
                break

            r, g, b, d, sku = potion
            # Calculate maximum batches for this potion
            max_batches = calculate_max_batches(red_ml, green_ml, blue_ml, dark_ml, r, g, b, d)
            if max_batches > 0:
                print("Creating potion", potion, flush=True)
                selected_potions.append(potion)
                # Create either the maximum number of batches or the potion cap or the max allowed
                batches_to_produce = min(max_batches, max_batches_allowed)
                # Deduct resources based on the number of batches
                red_ml -= r * batches_to_produce
                green_ml -= g * batches_to_produce
                blue_ml -= b * batches_to_produce
                dark_ml -= d * batches_to_produce
                potion_capacity -= batches_to_produce


                # Append to purchase plan
                purchase_plan.append({
                    "potion_type": [r, g, b, d],
                    "quantity": batches_to_produce
                })

        return purchase_plan


def get_ml():
    with db.engine.begin() as connection:
        return connection.execute(sqlalchemy.text("""
            SELECT 
                COALESCE(SUM(num_red_ml), 0) AS sum_red_ml,
                COALESCE(SUM(num_green_ml), 0) AS sum_green_ml,
                COALESCE(SUM(num_blue_ml), 0) AS sum_blue_ml,
                COALESCE(SUM(num_dark_ml), 0) AS sum_dark_ml
            FROM global_inventory
""")).first()

def total_potions_left():
    with db.engine.begin() as connection:
        cap = connection.execute(sqlalchemy.text("""SELECT potion_capacity FROM capacity""")).first()[0]
        total = connection.execute(sqlalchemy.text("""SELECT COALESCE(SUM(quantity), 0) as quant FROM potion_ledger""")).first()[0]
        return cap - total

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

    total_potion_inventory = total_potions_left()
    plan = efficient_bottle_plan(red, green, blue, dark, total_potion_inventory)
    print("Bottling Plan: ", plan, flush=True)
    return plan
