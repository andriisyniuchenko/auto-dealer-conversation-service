from fastapi import FastAPI

app = FastAPI(title="Auto Dealer Conversation Service")


@app.get("/health")
def health():
    return {"status": "ok"}