from typing import Dict, List

from fastapi import FastAPI
from pydantic import BaseModel, RootModel
from wordcloud import WordCloud


font_path = "/home/hskim/project/n8n/BMDOHYEON_ttf.ttf"


class PeriodFrequencies(BaseModel):
    period: str
    frequencies: Dict[str, int]


class GenerateRequest(RootModel[List[PeriodFrequencies]]):
    pass


app = FastAPI(title="Simple Payload Echo API", version="1.0.0")


@app.post("/wordclouds/generate")
def generate_wordclouds(payload: GenerateRequest):

    keywords_3days = dict(payload.root[0].frequencies)

    keywords_7days = dict(payload.root[1].frequencies)
    # print(f"[LOG] 7Days Keywords: {keywords_7days}")

    keywords_30days = dict(payload.root[2].frequencies)
    # print(f"[LOG] 1Month Keywords: {keywords_30days}")

    keywords_list = [keywords_3days, keywords_7days, keywords_30days]
    list_name = ["3days", "7days", "1month"]

    wc = WordCloud(width=1000, height=700, font_path=font_path)

    for idx, keywords in enumerate(keywords_list):
        wordcloud_img = wc.generate_from_frequencies(keywords)
        wordcloud_img.to_file(f"/home/hskim/project/n8n/wordcloud_output/{list_name[idx]}_wordcloud.png")

    return payload.root
