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
        num_ml, gold = connection.execute(sqlalchemy.text("""SELECT COALESCE(sum(num_green_ml + num_red_ml + num_blue_ml), 0) as total_ml,
                                                    COALESCE(sum(gold), 0) as total_gold 
                                                    FROM global_inventory 
                                                    """)).first()
        num_potions = connection.execute(sqlalchemy.text("""SELECT COALESCE(sum(quantity), 0)
                                                         as total_potions 
                                                         from potions""")).first()[0]

    return {"number_of_potions": num_potions, "ml_in_barrels": num_ml, "gold": gold}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    print("get_capacity_plan", flush=True)
    with db.engine.begin() as connection:
        pot_cap, ml_cap = connection.execute(sqlalchemy.text("""SELECT potion_capacity, ml_capacity 
                                                FROM capacity 
                                                WHERE id = 1""")).first()
        num_ml, gold = connection.execute(sqlalchemy.text("""SELECT sum(num_green_ml + num_red_ml + num_blue_ml) 
                                                as total_ml,
                                                sum(gold) as total_gold 
                                                FROM global_inventory""")).first()[0]
        num_potions = connection.execute(sqlalchemy.text("""SELECT sum(quantity) 
                                                         as total_potions 
                                                         from potions""")).first()[0]
        
        if num_potions > pot_cap or num_ml > ml_cap and gold > 1.5 * 1000:
            pot_cap += 50
            ml_cap += 10000
            gold -= 1000
            
    return {
        "potion_capacity": pot_cap,
        "ml_capacity": ml_cap
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
    with db.engine.connect() as connection:
        connection.execute(sqlalchemy.text("""UPDATE capacity 
                                                SET potion_capacity = :pot_cap, ml_capacity = :ml_cap 
                                                WHERE id = 1"""), 
                                                {"pot_cap": capacity_purchase.potion_capacity, 
                                                 "ml_cap": capacity_purchase.ml_capacity})
        connection.execute(sqlalchemy.text("""INSERT INTO global_inventory 
                                                (gold)
                                                VALUES (:gold)
                                                """), 
                                                {"gold": -1000})

    return "OK"
