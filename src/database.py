import os
import dotenv
from sqlalchemy import create_engine, MetaData, Table

def database_connection_url():
    dotenv.load_dotenv()

    return os.environ.get("POSTGRES_URI")

engine = create_engine(database_connection_url(), pool_pre_ping=True)
metadata = MetaData()
cart_items = Table('cart_items', metadata, autoload_with=engine)
potions = Table('potions', metadata, autoload_with=engine)
carts = Table('carts', metadata, autoload_with=engine)