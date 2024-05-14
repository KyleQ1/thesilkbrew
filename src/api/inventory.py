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

def get_inv():
    with db.engine.begin() as connection:
        return connection.execute(sqlalchemy.text("""SELECT 
                                                  COALESCE(sum(num_green_ml),0) + COALESCE(sum(num_red_ml),0) 
                                                  + COALESCE(sum(num_blue_ml),0) + COALESCE(sum(num_dark_ml),0) as total_ml,
                                                    COALESCE(SUM(gold), 0) as total_gold
                                                    FROM inventory_ledger 
                                                    """)).first()

def get_pot():
    with db.engine.begin() as connection:
        return connection.execute(sqlalchemy.text("""SELECT COALESCE(sum(quantity), 0) as total_potions 
                                                    from potion_ledger
                                                    """)).first()[0]

@router.get("/audit")
def get_inventory():
    """ """
    print("get_inventory", flush=True)
    with db.engine.begin() as connection:
        num_ml, gold = get_inv()
        num_potions = get_pot()

    return {"number_of_potions": num_potions, "ml_in_barrels": num_ml, "gold": gold}

# supposed to return 1 and each costs 1000
# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    print("get_capacity_plan", flush=True)
    pot_cap_send = 0
    ml_cap_send = 0
    with db.engine.begin() as connection:
        pot_cap, ml_cap = connection.execute(sqlalchemy.text("""SELECT potion_capacity, ml_capacity 
                                                FROM capacity 
                                                WHERE id = 1""")).first()
        num_ml, gold = get_inv()
        num_potions = get_pot()
        
        # Update potion to be bigger than ml by 1 then scale evenly
        if num_potions >= pot_cap * 0.9 and gold > 1.5 * 1000 :
            pot_cap_send = 1
        if num_ml >= ml_cap * 0.9 and (gold - 1000) > 1.5 * 1000:
            ml_cap_send = 1
            
    return {
        "potion_capacity": pot_cap_send,
        "ml_capacity": ml_cap_send
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
    if capacity_purchase.potion_capacity > 0 or capacity_purchase.ml_capacity > 0:
        with db.engine.connect() as connection:
            ml_cap, pot_cap = connection.execute(sqlalchemy.text("""SELECT ml_capacity, potion_capacity 
                                                FROM capacity 
                                                WHERE id = 1
                                                FOR UPDATE""")).first()
            new_ml_cap = ml_cap + capacity_purchase.ml_capacity * 10000
            new_pot_cap = pot_cap + capacity_purchase.potion_capacity * 50
            new_gold = -1000 * (capacity_purchase.ml_capacity + capacity_purchase.potion_capacity)
            print(f"new_ml_cap: {new_ml_cap} new_pot_cap: {new_pot_cap} new_gold: {new_gold}", flush=True)
            connection.execute(sqlalchemy.text("""UPDATE capacity 
                                                    SET potion_capacity = :pot_cap, ml_capacity = :ml_cap 
                                                    WHERE id = 1"""), 
                                                    {"pot_cap": new_pot_cap, 
                                                    "ml_cap": new_ml_cap})
            connection.execute(sqlalchemy.text("""INSERT INTO inventory_ledger 
                                                    (gold)
                                                    VALUES (:gold)
                                                    """), 
                                                    {"gold": new_gold})

    return "OK"
