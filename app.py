import os
from pathlib import Path
from typing import Dict, List, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, RootModel
import psycopg2
from psycopg2.extras import RealDictCursor
from wordcloud import WordCloud


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "wordcloud_output"
DEFAULT_FONT_PATH = BASE_DIR / "BMDOHYEON_ttf.ttf"


class PeriodFrequencies(BaseModel):
    period: str
    frequencies: Dict[str, int]
    keyword_articles: Dict[str, List[int]] = {}


class GenerateRequest(RootModel[List[PeriodFrequencies]]):
    pass


app = FastAPI(title="Simple Payload Echo API", version="1.0.0")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(OUTPUT_DIR)), name="media")

cors_origins = os.getenv(
    "CORS_ALLOW_ORIGINS",
    "http://localhost:6075,http://localhost:5173,http://localhost:3000",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class KeywordInfoRow(BaseModel):
    keyword: str
    title: str
    link: str


def get_required_env(*keys: str) -> str:
    for key in keys:
        value = os.getenv(key)
        if value:
            return value
    raise HTTPException(
        status_code=500,
        detail=f"Missing required environment variable. Expected one of: {', '.join(keys)}",
    )


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=get_required_env("DB_NAME", "N8N_DB_NAME"),
        user=get_required_env("DB_USER", "N8N_DB_USER"),
        password=get_required_env("DB_PASSWORD", "N8N_DB_PASSWORD"),
    )


def top_n_frequencies(freq: Dict[str, int], n: int = 5) -> Dict[str, int]:
    top_items = sorted(freq.items(), key=lambda item: item[1], reverse=True)[:n]
    return dict(top_items)


def top_n_keyword_articles(
    top_freq: Dict[str, int], keyword_articles: Dict[str, List[int]]
) -> Dict[str, List[int]]:
    return {
        keyword: keyword_articles.get(keyword, [])
        for keyword in top_freq.keys()
    }


@app.post("/wordclouds/generate")
def generate_wordclouds(payload: GenerateRequest):

    periods = payload.root
    keywords_list = [dict(item.frequencies) for item in periods]
    list_name = [item.period for item in periods]

    font_path = Path(os.getenv("WORDCLOUD_FONT_PATH", str(DEFAULT_FONT_PATH)))
    if not font_path.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Font file not found: {font_path}",
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    wc = WordCloud(width=1000, height=700, font_path=str(font_path))

    for idx, keywords in enumerate(keywords_list):
        wordcloud_img = wc.generate_from_frequencies(keywords)
        wordcloud_img.to_file(str(OUTPUT_DIR / f"wordcloud_{list_name[idx]}.png"))

    response = []
    for item in periods:
        top_freq = top_n_frequencies(item.frequencies, 5)
        response.append(
            {
                "period": item.period,
                "frequencies": top_freq,
                "keyword_articles": top_n_keyword_articles(
                    top_freq, item.keyword_articles
                ),
            }
        )

    return response


@app.get("/keyword-info/{period}", response_model=List[KeywordInfoRow])
def get_keyword_info(period: Literal["3day", "7day", "1month"]):
    query = """
        SELECT keyword, title, link
        FROM public.keyword_info
        WHERE period = %s
        ORDER BY keyword, title
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (period,))
                rows = cur.fetchall()
                return [KeywordInfoRow(**row) for row in rows]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"DB query failed: {exc}")
