from fastapi import FastAPI


app = FastAPI(
    title="Agentic URL Shortener",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "message": "Agentic URL Shortener API"
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }