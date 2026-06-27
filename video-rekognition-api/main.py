import asyncio
from fastapi import FastAPI
import httpx
from .config import settings


app = FastAPI()

ip = settings.CAMERA_IP


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/move")
async def move_left(direction: str, time_sec: float):
    direction = direction.lower()
    
    direction_map = {
        "left": "revA",
        "right": "fwdA",
        "stop_horizontal": "stopA",
        "up": "fwdB",
        "down": "revB",
        "stop_vertical": "stopB",
    }

    stop_movement = (
        direction_map["stop_horizontal"]
        if (direction == "left" or direction == "right")
        else direction_map["stop_vertical"]
    )

    url_move = f"{ip}{direction_map[direction]}"
    url_stop = f"{ip}{stop_movement}"

    try:
        async with httpx.AsyncClient() as client:
            response_move = await client.get(url_move, timeout=5.0)
            response_move.raise_for_status()

            await asyncio.sleep(time_sec)

            response_stop = await client.get(url_stop, timeout=5.0)
            response_stop.raise_for_status()

        return {
            "message": "Moved left and stopped",
            "move_status": response_move.status_code,
            "stop_status": response_stop.status_code,
            "url_move": url_move,
            "url_stop": url_stop,
        }

    except httpx.HTTPError as exc:
        return {"error": f"Error en la comunicación con la cámara: {exc}"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
