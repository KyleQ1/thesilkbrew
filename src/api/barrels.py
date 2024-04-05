from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    green_potions_needed = False
    with db.engine.begin() as connection:
        result1 = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory"))
        for row in result1:
            # Check if less than 10 green potions in inventory.
            green_potions = row[0]
            if green_potions < 10:  
                green_potions_needed = True
                break
        results2 = connection.exectue(sqlalchemy.text("SELECT gold from global_inventory"))
        for row in results2:
            gold = row[0]
    
    purchase_plan = []
    if green_potions_needed:
        # Find a small green potion barrel in the wholesale catalog and add it to the purchase plan.
        for barrel in wholesale_catalog:
            if barrel.potion_type == [0, 100, 0, 0] and gold >= barrel.price:
                purchase_plan.append({"sku": barrel.sku, "quantity": 1})
                break

    return purchase_plan

