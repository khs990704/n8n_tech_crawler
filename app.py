import os
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Literal, Optional

from fastapi import FastAPI, HTTPException, Query
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
    counts: int


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


class KeywordChangeItem(BaseModel):
    keyword: str
    cur: int
    prev: int
    delta: int
    pct: Optional[float]


class WindowBound(BaseModel):
    start: date
    end: date


class KeywordChangeWindow(BaseModel):
    current: WindowBound
    previous: WindowBound


class KeywordChangeResponse(BaseModel):
    period: str
    window: KeywordChangeWindow
    rising: List[KeywordChangeItem]
    falling: List[KeywordChangeItem]
    new: List[KeywordChangeItem]


def _get_period_windows(period: str) -> tuple[WindowBound, WindowBound]:
    yesterday = date.today() - timedelta(days=1)
    if period == "3day":
        days = 3
    elif period == "7day":
        days = 7
    else:
        days = 30
    current = WindowBound(start=yesterday - timedelta(days=days), end=yesterday)
    previous = WindowBound(
        start=yesterday - timedelta(days=days * 2),
        end=yesterday - timedelta(days=days),
    )
    return current, previous


@app.get("/keyword-change/{period}", response_model=KeywordChangeResponse)
def get_keyword_change(
    period: Literal["3day", "7day", "1month"],
    limit: int = Query(default=5, ge=1),
    min_count: int = Query(default=0, ge=0),
):
    current, previous = _get_period_windows(period)

    query = """
        WITH current_counts AS (
            SELECT keyword, COUNT(*) AS cnt
            FROM public.rss_article_keyword
            WHERE date >= %(cur_start)s AND date <= %(cur_end)s
            GROUP BY keyword
        ),
        prev_counts AS (
            SELECT keyword, COUNT(*) AS cnt
            FROM public.rss_article_keyword
            WHERE date >= %(prev_start)s AND date < %(prev_end)s
            GROUP BY keyword
        ),
        combined AS (
            SELECT
                COALESCE(c.keyword, p.keyword) AS keyword,
                COALESCE(c.cnt, 0) AS cur,
                COALESCE(p.cnt, 0) AS prev
            FROM current_counts c
            FULL OUTER JOIN prev_counts p ON c.keyword = p.keyword
        )
        SELECT
            keyword,
            cur,
            prev,
            (cur - prev) AS delta,
            CASE
                WHEN prev = 0 THEN NULL
                ELSE ROUND(((cur - prev)::numeric / prev) * 100, 4)
            END AS pct
        FROM combined
        WHERE (cur > 0 OR prev > 0)
          AND (cur >= %(min_count)s OR prev >= %(min_count)s)
    """
    params = {
        "cur_start": current.start,
        "cur_end": current.end,
        "prev_start": previous.start,
        "prev_end": previous.end,
        "min_count": min_count,
    }

    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                rows = cur.fetchall()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"DB query failed: {exc}")

    _KEYWORD_BLOCKLIST = {"ai", "ai 모델"}

    rising, falling, new = [], [], []
    for row in rows:
        item = KeywordChangeItem(**row)
        word = item.keyword.strip()
        if len(word) < 2:
            continue
        if word.lower() in _KEYWORD_BLOCKLIST:
            continue
        if item.prev == 0 and item.cur > 0:
            new.append(item)
        elif item.delta > 0:
            rising.append(item)
        elif item.delta < 0:
            falling.append(item)

    rising.sort(key=lambda x: x.delta, reverse=True)
    falling.sort(key=lambda x: x.delta)
    new.sort(key=lambda x: x.cur, reverse=True)

    return KeywordChangeResponse(
        period=period,
        window=KeywordChangeWindow(current=current, previous=previous),
        rising=rising[:limit],
        falling=falling[:limit],
        new=new[:limit],
    )


_PERIOD_LABEL: Dict[str, str] = {
    "3day": "최근 3일",
    "7day": "최근 7일",
    "1month": "최근 1개월",
}

_COMPANY_KEYWORDS = {
    "openai", "google", "microsoft", "meta", "anthropic", "xai", "nvidia",
    "apple", "amazon", "samsung", "sk", "lg", "kakao", "naver", "baidu",
    "deepmind", "mistral", "cohere", "stability ai", "hugging face",
}


class SummaryPeriodInput(BaseModel):
    period: str
    frequencies: Dict[str, int]
    rising: List[KeywordChangeItem] = []


class KeywordSummaryRequest(BaseModel):
    data: List[SummaryPeriodInput]


class PeriodSummary(BaseModel):
    period: str
    summary: str


def _build_summary(item: SummaryPeriodInput) -> str:
    label = _PERIOD_LABEL.get(item.period, item.period)
    sentences = []

    if not item.frequencies:
        return f"{label} 동안 유의미한 AI 키워드 언급이 집계되지 않았습니다."

    top3 = sorted(item.frequencies.items(), key=lambda x: x[1], reverse=True)[:3]
    top3_names = ", ".join(k for k, _ in top3)
    sentences.append(f"{label} 동안 AI 뉴스에서 가장 많이 언급된 키워드는 {top3_names} 입니다.")

    if item.rising:
        best = max(item.rising, key=lambda x: x.delta)
        if best.pct is not None:
            pct_int = round(best.pct)
            sentences.append(
                f"특히 {best.keyword} 언급이 이전 동일 기간 대비 +{pct_int}% 증가했습니다."
            )
        else:
            sentences.append(
                f"특히 {best.keyword} 언급이 이전 동일 기간 대비 +{best.delta}건 증가했습니다."
            )

    company_hits = [
        (k, v) for k, v in item.frequencies.items()
        if k.lower() in _COMPANY_KEYWORDS
    ]
    if len(company_hits) >= 2:
        top_companies = sorted(company_hits, key=lambda x: x[1], reverse=True)[:3]
        company_names = ", ".join(k for k, _ in top_companies)
        sentences.append(f"기업 언급은 {company_names} 순으로 많았습니다.")

    return " ".join(sentences)


@app.post("/keyword-summary", response_model=List[PeriodSummary])
def get_keyword_summary(payload: KeywordSummaryRequest):
    return [
        PeriodSummary(period=item.period, summary=_build_summary(item))
        for item in payload.data
    ]


@app.get("/keyword-info/{period}", response_model=List[KeywordInfoRow])
def get_keyword_info(period: Literal["3day", "7day", "1month"]):
    query = """
        SELECT keyword, title, link, counts
        FROM public.keyword_info
        WHERE period = %s
        ORDER BY counts DESC, keyword, title
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (period,))
                rows = cur.fetchall()
                return [KeywordInfoRow(**row) for row in rows]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"DB query failed: {exc}")
