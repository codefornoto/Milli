#!/usr/bin/env python3
"""Milli CSVから文字単位の学習データを作る。"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd

TEXT_COLUMNS = {
    "満足度理由（交通手段）": "交通手段についてどう感じましたか？",
    "訪問施設（前）自由記入": "ここへ来る前はどこに行きましたか？",
    "訪問施設（後）自由記入": "この後はどこへ行きますか？",
    "満足度理由（商品・サービス）": "商品やサービスで良かったことは？",
    "満足度理由（施設）": "施設で印象に残ったことは？",
    "不便理由": "旅行中に不便だったことは？",
    "自由意見（施設）": "この施設についてどう思いましたか？",
    "自由意見（県内）": "石川県に求めるものはありますか？",
    "今回の旅行またはお出かけにおいて、特に人に薦めたいと感じたものとその理由について具体的に教えてください。": "人に薦めたいものは何ですか？",
}
EMPTY = re.compile(r"^(特に[は、, ]*)?(なし|無し|ない|ありません|ございません)[。.!！ ]*$")


def clean(value: object) -> str | None:
    if pd.isna(value):
        return None
    text = re.sub(r"\s+", " ", str(value)).strip()
    if len(text) < 2 or EMPTY.fullmatch(text):
        return None
    return text[:500]


def load_personas(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_companion(value: object) -> str:
    text = str(value)
    if "夫婦" in text: return "夫婦"
    if "小学生以下" in text or "中学生以下" in text: return "子連れ家族"
    if "中学生以上" in text or text in {"家族", "親", "娘", "姉妹", "妹"}: return "家族"
    if "ひとり" in text: return "一人旅"
    if "友人" in text: return "友人"
    if "恋人" in text: return "恋人"
    return "その他"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--personas", default="../data/personas.json")
    ap.add_argument("--out", default="../data/training_data.json")
    ap.add_argument("--corpus", default="../data/corpus.txt")
    ap.add_argument("--max-per-persona", type=int, default=700)
    args = ap.parse_args()
    root = Path(__file__).resolve().parent
    personas = load_personas((root / args.personas).resolve())
    df = pd.read_csv(args.csv, encoding="utf-8-sig", low_memory=False)
    df["回答日時"] = pd.to_datetime(df.get("回答日時"), errors="coerce")
    birth = pd.to_numeric(df.get("生年"), errors="coerce")
    df["_age"] = ((df["回答日時"].dt.year - birth) // 10 * 10).astype("Int64").astype(str).str.replace("<NA>", "不明") + "代"
    df["_companion"] = df.get("同行者", "").map(normalize_companion)
    df["_visit"] = df.get("訪問回数", "").map(lambda x: "初めて" if x == "初めて" else "リピーター")

    records: list[dict] = []
    for p in personas:
        mask = (
            (df.get("都道府県") == p["prefecture"])
            & (df["_age"] == p["age"])
            & (df["_companion"] == p["companion"])
            & (df["_visit"] == p["visit"])
            & (df.get("回答エリア") == p["area"])
        )
        rows = df[mask]
        candidates = []
        for _, row in rows.iterrows():
            for col, question in TEXT_COLUMNS.items():
                if col not in df: continue
                answer = clean(row[col])
                if answer:
                    candidates.append({"persona_id": p["id"], "question": question, "answer": answer, "source_column": col})
        records.extend(candidates[: args.max_per_persona])

    # 全体の言葉も取りこぼさないよう、単独文章として追加。
    raw_texts = []
    for col in TEXT_COLUMNS:
        if col in df:
            raw_texts.extend(x for x in (clean(v) for v in df[col]) if x)
    seen = set()
    raw_texts = [x for x in raw_texts if not (x in seen or seen.add(x))]
    corpus_lines = [f"<{r['persona_id']}>\n質問：{r['question']}\n観光客：{r['answer']}\n" for r in records]
    corpus_lines += [f"観光客：{text}\n" for text in raw_texts]

    out = (root / args.out).resolve(); out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "meta": {"source_rows": len(df), "persona_pairs": len(records), "unique_texts": len(raw_texts)},
        "persona_pairs": records,
        "texts": raw_texts,
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (root / args.corpus).resolve().write_text("\n".join(corpus_lines), encoding="utf-8")
    print(json.dumps({"rows": len(df), "persona_pairs": len(records), "unique_texts": len(raw_texts), "characters": sum(map(len, corpus_lines))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
