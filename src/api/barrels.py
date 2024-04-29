from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
import random

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

# Sort potions needed by total ml stored
# TODO: Sort using total potions too
def get_barrel_buying_order():
    barrel_buying_order = {}
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("""
            SELECT 
                COALESCE(SUM(num_green_ml), 0) AS sum_green_ml,
                COALESCE(SUM(num_red_ml), 0) AS sum_red_ml,
                COALESCE(SUM(num_blue_ml), 0) AS sum_blue_ml,
                COALESCE(SUM(num_dark_ml), 0) AS sum_dark_ml
            FROM inventory_ledger
                                                    """)).first()
        barrel_buying_order["green"] = result[0]
        barrel_buying_order["red"] = result[1]
        barrel_buying_order["blue"] = result[2]
        barrel_buying_order["dark"] = result[3]
    # check if they are all zero and randomize otherwise sort dict
    #if all(value == 0 for value in barrel_buying_order.values()):
    #    random.shuffle(barrel_buying_order)
    #else:
    barrel_buying_order = dict(sorted(barrel_buying_order.items(), key=lambda item: item[1]))
    
    return barrel_buying_order

def get_gold():
    with db.engine.begin() as connection:
        return connection.execute(sqlalchemy.text("SELECT sum(gold) from inventory_ledger")).first()[0]
    
# Determines which barrels should be bought
# Prioritizes buying larger barrels as they have higher ROI
# ml ber barrel is 2500, 500, 200
# Prices are 250, 100, 60
def get_size(gold, type_potion, catalog):
    type_potion = type_potion.upper()
    if f"LARGE_{type_potion}_BARREL" in catalog and gold >= catalog[f"LARGE_{type_potion}_BARREL"].price:
        return f"LARGE_{type_potion}_BARREL"
    elif f"MEDIUM_{type_potion}_BARREL" in catalog and gold >= catalog[f"MEDIUM_{type_potion}_BARREL"].price:
        return f"MEDIUM_{type_potion}_BARREL"
    elif f"SMALL_{type_potion}_BARREL" in catalog and gold >= catalog[f"SMALL_{type_potion}_BARREL"].price:
        return f"SMALL_{type_potion}_BARREL"
    elif f"MINI_{type_potion}_BARREL" in catalog and gold >= catalog[f"MINI_{type_potion}_BARREL"].price:
        return f"MINI_{type_potion}_BARREL"
    return None    

def get_quantity(catalog, gold, sku, remaining_cap, pot_ml):
    # Takes in catalog sees total barrels left
    max_gold = gold // catalog[sku].price
    max_capacity = remaining_cap // catalog[sku].ml_per_barrel
    if gold < 10000:
        return min(1, max_capacity)
    return min(max_gold, max_capacity)

def get_capacity():
    with db.engine.begin() as connection:
        total_ml = connection.execute(sqlalchemy.text("""
            SELECT COALESCE(SUM(num_red_ml), 0) + COALESCE(SUM(num_green_ml), 0) + 
            COALESCE(SUM(num_blue_ml), 0) + COALESCE(SUM(num_dark_ml), 0) as total_ml from inventory_ledger""")).first()[0]
        cap = connection.execute(sqlalchemy.text("SELECT ml_capacity from capacity")).first()[0]
        return cap - total_ml


@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")
    with db.engine.begin() as connection:
        for barrel in barrels_delivered:
            color = get_potion_color(barrel.potion_type)
            total_ml = barrel.ml_per_barrel * barrel.quantity
            if color != None:
                connection.execute(sqlalchemy.text(f"""INSERT INTO inventory_ledger 
                                                   (gold, num_{color}_ml) 
                                                   VALUES (:gold, :num_{color}_ml)"""),
                                                   [{"gold": -barrel.price, f"num_{color}_ml": barrel.ml_per_barrel}])
                
                print(f"Added potion ML: {color}  total_ml_stored: {total_ml}")
            else:
                print("Barrel color not found", flush=True)

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print("get_wholesale_purchase_plan", flush=True)
    catalog = {}
    for barrel in wholesale_catalog:
        catalog[barrel.sku] = barrel
    print(f"catalog: {catalog}")
    
    gold = get_gold()
    order = get_barrel_buying_order()
    purhcase_plan = []
    ml_purchase = 0

    for type_potion, ml in order.items():
        # change to total potions perhaps
        total_ml_left_storage = get_capacity() - ml_purchase
        print(type_potion, ml, gold, flush=True)
        size = get_size(gold, type_potion, catalog)
        if size:
            # get ml in order
        
            quantity = get_quantity(catalog, gold, size, total_ml_left_storage, ml)
            if quantity > 0:
                print(f"purchasing: {size} {catalog[size].price} {quantity}")
                purhcase_plan.append({"sku": size, "quantity": 1})
                gold -= catalog[size].price * quantity
                ml_purchase += catalog[size].ml_per_barrel * quantity
    return purhcase_plan
    

