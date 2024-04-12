from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/audit")
def get_inventory():
    """ """
    print("get_inventory", flush=True)
    with db.engine.begin() as connection:
        num_ml, num_potions, gold = connection.execute(sqlalchemy.text("""SELECT (num_green_ml + num_red_ml + num_blue_ml) as total_ml, 
                                                    (num_green_potions + num_red_potions + num_blue_potions) as total_potions, 
                                                    (gold) as total_gold 
                                                    FROM global_inventory 
                                                    """)).first()

    return {"number_of_potions": num_potions, "ml_in_barrels": num_ml, "gold": gold}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    print("get_capacity_plan", flush=True)
    return {
        "potion_capacity": 0,
        "ml_capacity": 0
        }

class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

# Gets called once a day
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase : CapacityPurchase, order_id: int):
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    print("deliver_capacity_plan")
    print(f"capacity_purchase: {capacity_purchase} order_id: {order_id}", flush=True)

    return "OK"
