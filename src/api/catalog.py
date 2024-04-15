from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()

def get_potions():
    with db.engine.begin() as connection:
        return connection.execute(
            sqlalchemy.text("""SELECT num_red_potions, num_green_potions, 
                            num_blue_potions, num_dark_potions FROM global_inventory""")).first()

@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    print("get_catalog", flush=True)
    # TODO: test
    red, green, blue, dark = get_potions()
    selling_plan = []
    potions = [("red", red, [100, 0, 0, 0]), ("green", green, [0, 100, 0, 0]), 
               ("blue", blue, [0, 0, 100, 0]), ("dark", dark, [0, 0, 0, 100])]
    for potion in potions:
        color = potion[0]
        quantity = potion[1]
        potion_type = potion[2]
        if quantity > 0:
            selling_plan.append({
                "sku": f"{color.upper()}_POTION_0",
                "name": f"{color} potion",
                "quantity": quantity,
                "price": 50,
                "potion_type": potion_type,
            })
    return selling_plan
