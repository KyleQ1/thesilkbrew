from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()

def get_potions():
    with db.engine.begin() as connection:
        return connection.execute(
            sqlalchemy.text("""SELECT p.r, p.g, p.b, p.d, sum(p.quantity) as total_quantity, gp.sku, gp.price
                        FROM potions p
                        JOIN grab_potions gp ON p.grab_potion_id = gp.id
                        WHERE p.quantity > 0
                        GROUP BY p.r, p.g, p.b, p.d, gp.sku, gp.price
                        ORDER BY total_quantity DESC""")).fetchall()

@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    print("get_catalog", flush=True)
    # TODO: test
    print(get_potions())
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
    return selling_plan[:6]
