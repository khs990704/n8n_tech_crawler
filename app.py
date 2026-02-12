import os
from pathlib import Path
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, RootModel
from wordcloud import WordCloud


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "wordcloud_output"
DEFAULT_FONT_PATH = BASE_DIR / "BMDOHYEON_ttf.ttf"


class PeriodFrequencies(BaseModel):
    period: str
    frequencies: Dict[str, int]


class GenerateRequest(RootModel[List[PeriodFrequencies]]):
    pass


app = FastAPI(title="Simple Payload Echo API", version="1.0.0")


def top_n_frequencies(freq: Dict[str, int], n: int = 5) -> Dict[str, int]:
    top_items = sorted(freq.items(), key=lambda item: item[1], reverse=True)[:n]
    return dict(top_items)


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
        wordcloud_img.to_file(str(OUTPUT_DIR / f"{list_name[idx]}_wordcloud.png"))

    return [
        {
            "period": item.period,
            "frequencies": top_n_frequencies(item.frequencies, 5),
        }
        for item in periods
    ]
