#!/usr/bin/env python3
"""Milliの実在する属性組合せを検証し、ペルソナJSONを出力する。"""
from __future__ import annotations

import argparse, json
from pathlib import Path
import pandas as pd

ANCHORS = [
 ("愛知県","30代","子連れ家族","初めて","加賀","家族で楽しむ加賀の休日"),
 ("愛知県","60代","夫婦","初めて","加賀","温泉と食を楽しむ愛知の夫婦"),
 ("東京都","50代","夫婦","初めて","金沢","文化と食をめぐる東京の夫婦"),
 ("東京都","50代","一人旅","初めて","金沢","静かに金沢を歩く一人旅"),
 ("大阪府","60代","夫婦","初めて","加賀","温泉宿でのんびりする大阪の夫婦"),
 ("神奈川県","50代","夫婦","初めて","金沢","名所と海鮮を楽しむ神奈川の夫婦"),
 ("富山県","30代","子連れ家族","リピーター","加賀","何度も遊びに来る富山の家族"),
 ("福井県","30代","子連れ家族","リピーター","加賀","近県から気軽に訪れる福井の家族"),
 ("石川県","30代","子連れ家族","リピーター","加賀","県内で休日を楽しむ子連れ家族"),
 ("東京都","20代","友人","初めて","金沢","友人と金沢をめぐる東京の若者"),
 ("大阪府","20代","恋人","初めて","金沢","二人でまち歩きを楽しむ大阪の旅行者"),
 ("埼玉県","50代","夫婦","初めて","金沢","定番の名所を訪ねる埼玉の夫婦"),
 ("千葉県","60代","夫婦","初めて","金沢","ゆっくり金沢を味わう千葉の夫婦"),
 ("兵庫県","60代","夫婦","リピーター","加賀","加賀温泉に帰ってくる兵庫の夫婦"),
 ("京都府","40代","子連れ家族","リピーター","加賀","家族で再訪する京都の旅行者"),
 ("岐阜県","40代","子連れ家族","初めて","加賀","テーマパークを楽しむ岐阜の家族"),
 ("長野県","30代","子連れ家族","初めて","能登","家族で能登へ向かう長野の旅行者"),
 ("北海道","50代","夫婦","初めて","金沢","遠方から金沢へ来た北海道の夫婦"),
 ("石川県","50代","一人旅","リピーター","能登","能登を何度も訪ねる県内一人旅"),
 ("富山県","60代","夫婦","リピーター","能登","近県から能登へ通う富山の夫婦"),
]

def companion(x):
 x=str(x)
 if "夫婦" in x:return "夫婦"
 if "小学生以下" in x or "中学生以下" in x:return "子連れ家族"
 if "中学生以上" in x or x in {"家族","親","娘","姉妹","妹"}:return "家族"
 if "ひとり" in x:return "一人旅"
 if "友人" in x:return "友人"
 if "恋人" in x:return "恋人"
 return "その他"

def purposes(series):
 text=",".join(series.dropna().astype(str)); mapping=[("温泉","温泉"),("美味しい","食"),("名所","観光"),("まちあるき","まち歩き"),("テーマパーク","家族レジャー"),("祭り","イベント"),("自然","自然")]
 found=[label for key,label in mapping if key in text]
 return (found or ["観光"])[:3]

def main():
 ap=argparse.ArgumentParser();ap.add_argument("csv");ap.add_argument("--out",default="../data/personas.json");a=ap.parse_args();root=Path(__file__).resolve().parent
 df=pd.read_csv(a.csv,encoding="utf-8-sig",low_memory=False);dt=pd.to_datetime(df["回答日時"],errors="coerce");birth=pd.to_numeric(df["生年"],errors="coerce");df["_age"]=((dt.dt.year-birth)//10*10).astype("Int64").astype(str).str.replace("<NA>","不明")+"代";df["_comp"]=df["同行者"].map(companion);df["_visit"]=df["訪問回数"].map(lambda x:"初めて" if x=="初めて" else "リピーター")
 result=[]
 for i,(pref,age,comp,visit,area,name) in enumerate(ANCHORS,1):
  rows=df[(df["都道府県"]==pref)&(df["_age"]==age)&(df["_comp"]==comp)&(df["_visit"]==visit)&(df["回答エリア"]==area)]
  pur=purposes(rows["宿泊目的"])
  result.append({"id":f"P{i:02d}","name":name,"prefecture":pref,"age":age,"companion":comp,"visit":visit,"area":area,"purpose":pur,"description":f"{pref}から{comp}で訪れ、{area}で{'・'.join(pur)}を楽しむ{visit}の旅行者。","image":f"./images/persona{i:02d}.webp","sample_count":int(len(rows))})
 out=(root/a.out).resolve();out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8");print(out)
if __name__=="__main__":main()
