from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()

def get_potions():
    with db.engine.begin() as connection:
        return connection.execute(
            sqlalchemy.text("""SELECT gp.r, gp.g, gp.b, gp.d, sum(p.quantity) as total_quantity, gp.sku, gp.price
                        FROM potion_ledger p
                        JOIN grab_potions gp ON p.grab_potion_id = gp.id
                        WHERE p.quantity > 0
                        GROUP BY gp.r, gp.g, gp.b, gp.d, gp.sku, gp.price
                        ORDER BY total_quantity DESC""")).fetchall()

@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    print("get_catalog")
    result = get_potions()
    selling_plan = []
    for row in result:
        r, g, b, d, quant, sku, price = row
        selling_plan.append({
                "sku": sku,
                "name": f"{sku} potion",
                "quantity": quant,
                "price": price,
                "potion_type": [r, g, b, d],
            })

    selling_plan = sorted(selling_plan, key = lambda inventory : (inventory["price"], -inventory["quantity"]))
    print("Selling Plan: ", selling_plan[:6])
    return selling_plan[:6]
