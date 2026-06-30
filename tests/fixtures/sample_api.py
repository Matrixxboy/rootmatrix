from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str = None):
    # Heavy logic
    db = get_db()
    result = db.query(item_id)
    return {"item_id": item_id, "q": q, "result": result}
