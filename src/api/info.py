from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/info",
    tags=["info"],
    dependencies=[Depends(auth.get_api_key)],
)

class Timestamp(BaseModel):
    day: str
    hour: int

@router.post("/current_time")
def post_time(timestamp: Timestamp):
    """
    Share current time.
    """
    print("post_time")
    print(f"day: {timestamp.day} hour: {timestamp.hour}", flush=True)
    return "OK"

