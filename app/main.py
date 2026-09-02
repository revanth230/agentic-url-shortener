from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl
import secrets
import string

from app.database import Base, engine
from app import models

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Agentic URL Shortener",
    version="0.1.0",
)


url_store = {}
click_store = {}


class URLRequest(BaseModel):
    url: HttpUrl


class URLResponse(BaseModel):
    original_url: HttpUrl
    short_code: str
    short_url: str


def generate_short_code(length: int = 6) -> str:
    characters = string.ascii_letters + string.digits

    return "".join(
        secrets.choice(characters)
        for _ in range(length)
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


@app.post(
    "/urls",
    response_model=URLResponse,
    status_code=201,
)
def create_short_url(request: URLRequest):
    short_code = generate_short_code()

    while short_code in url_store:
        short_code = generate_short_code()

    url_store[short_code] = str(request.url)
    click_store[short_code] = 0

    return {
        "original_url": request.url,
        "short_code": short_code,
        "short_url": f"http://127.0.0.1:8000/{short_code}",
    }

@app.get("/{short_code}")
def redirect_to_original(short_code: str):
    original_url = url_store.get(short_code)

    if original_url is None:
        raise HTTPException(
            status_code=404,
            detail="Short URL not found",
        )

    click_store[short_code] += 1

    return RedirectResponse(
        url=original_url,
        status_code=307,
    )

@app.get("/urls/{short_code}/analytics")
def get_analytics(short_code: str):
    if short_code not in url_store:
        raise HTTPException(
            status_code=404,
            detail="Short URL not found",
        )

    return {
        "short_code": short_code,
        "original_url": url_store[short_code],
        "clicks": click_store[short_code],
    }