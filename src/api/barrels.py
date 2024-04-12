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
def get_potion_buying_order():
    potion_buying_order = {}
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_ml, num_red_ml, num_blue_ml, num_dark_ml FROM global_inventory"))
        result = result.fetchone()
        potion_buying_order["green"] = result[0]
        potion_buying_order["red"] = result[1]
        potion_buying_order["blue"] = result[2]
        potion_buying_order["dark"] = result[3]
    potion_buying_order = dict(sorted(potion_buying_order.items(), key=lambda item: item[1]))
    return potion_buying_order

def get_gold():
    with db.engine.begin() as connection:
        return connection.execute(sqlalchemy.text("SELECT gold from global_inventory")).first()[0]
    
# Determines which barrels should be bought
# Prioritizes buying larger barrels as they have higher ROI
# ml ber barrel is 2500, 500, 200
# Prices are 250, 100, 60
def get_size(gold, type_potion, catalog):
    print(catalog[f"SMALL_RED_BARREL"].price, flush=True)
    if f"LARGE_{type_potion}_BARREL" in catalog and gold >= catalog[f"LARGE_{type_potion}_BARREL"].price:
        return f"LARGE_{type_potion}_BARREL"
    elif f"MEDIUM_{type_potion}_BARREL" in catalog and gold >= catalog[f"MEDIUM_{type_potion}_BARREL"].price:
        return f"MEDIUM_{type_potion}_BARREL"
    elif f"SMALL_{type_potion}_BARREL" in catalog and gold >= catalog[f"SMALL_{type_potion}_BARREL"].price:
        return f"SMALL_{type_potion}_BARREL"
    elif f"MINI_{type_potion}_BARREL" in catalog and gold >= catalog[f"MINI_{type_potion}_BARREL"].price:
        return f"MINI_{type_potion}_BARREL"
    return None    

# TODO: Determine total barrels to get based off ml/potions
def get_quantity():
    return 1


@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")
    with db.engine.begin() as connection:
        for barrel in barrels_delivered:
            color = get_potion_color(barrel.potion_type)
            if color != None:
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = gold - {barrel.price}"))
                connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_{color}_ml = num_{color}_ml + {barrel.ml_per_barrel}"))
                print(f"Added potion ML: {color}  total_ml_stored: {barrel.ml_per_barrel}")

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

    order = get_potion_buying_order()
    purhcase_plan = []
    for type_potion, ml in order.items():
        # change to total potions perhaps
        if ml < 10000:
            size = get_size(gold, type_potion, catalog)
            quantity = get_quantity()
            if size:
                print(f"purchasing: {size} {quantity}")
                purhcase_plan.append({"sku": size, "quantity": 1})
                gold -= catalog[size].price * quantity
    print(purhcase_plan, flush=True)
    return purhcase_plan
    

