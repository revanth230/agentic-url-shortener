import secrets
import string

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.database import Base, engine, get_db


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Agentic URL Shortener",
    version="0.1.0",
)


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
def create_short_url(
    request: URLRequest,
    db: Session = Depends(get_db),
):
    short_code = generate_short_code()

    existing_url = db.scalar(
        select(models.ShortURL).where(
            models.ShortURL.short_code == short_code
        )
    )

    while existing_url is not None:
        short_code = generate_short_code()

        existing_url = db.scalar(
            select(models.ShortURL).where(
                models.ShortURL.short_code == short_code
            )
        )

    new_url = models.ShortURL(
        short_code=short_code,
        original_url=str(request.url),
        clicks=0,
    )

    db.add(new_url)
    db.commit()
    db.refresh(new_url)

    return {
        "original_url": new_url.original_url,
        "short_code": new_url.short_code,
        "short_url": f"http://127.0.0.1:8000/{new_url.short_code}",
    }


@app.get("/urls/{short_code}/analytics")
def get_analytics(
    short_code: str,
    db: Session = Depends(get_db),
):
    url_record = db.scalar(
        select(models.ShortURL).where(
            models.ShortURL.short_code == short_code
        )
    )

    if url_record is None:
        raise HTTPException(
            status_code=404,
            detail="Short URL not found",
        )

    return {
        "short_code": url_record.short_code,
        "original_url": url_record.original_url,
        "clicks": url_record.clicks,
        "created_at": url_record.created_at,
    }


@app.get("/{short_code}")
def redirect_to_original(
    short_code: str,
    db: Session = Depends(get_db),
):
    url_record = db.scalar(
        select(models.ShortURL).where(
            models.ShortURL.short_code == short_code
        )
    )

    if url_record is None:
        raise HTTPException(
            status_code=404,
            detail="Short URL not found",
        )

    url_record.clicks += 1
    db.commit()

    return RedirectResponse(
        url=url_record.original_url,
        status_code=307,
    )