# -*- coding: utf-8 -*-
"""@cosme 品牌頁評論爬蟲（多頁，含 503 重試）。抓不同品牌只改設定區。"""
import requests, time
from bs4 import BeautifulSoup
import pandas as pd
from clean_reviews import clean_review_df

# === 設定區 ===
BRAND_ID = "3743"
BRAND_NAME = "Inna Organic 童顏有機"
MAX_PAGES = 15

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.cosme.net.tw/",
}

def fetch_page(url, max_retries=4):
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 503:
                time.sleep(10*(attempt+1)); continue
            resp.raise_for_status(); return resp
        except Exception as e:
            print(f"    出錯：{str(e)[:50]}，重試..."); time.sleep(10*(attempt+1))
    return None

if __name__ == "__main__":
    records, fails = [], 0
    for page in range(1, MAX_PAGES+1):
        url = f"https://www.cosme.net.tw/brands/{BRAND_ID}/reviews?page={page}"
        print(f"抓取第 {page} 頁...")
        resp = fetch_page(url)
        if resp is None:
            fails += 1
            if fails >= 3: break
            continue
        fails = 0
        soup = BeautifulSoup(resp.text, "html.parser")
        blocks = soup.find_all("div", class_="review-content-container")
        if not blocks:
            print("  沒有評論，停止。"); break
        for b in blocks:
            records.append({"brand":BRAND_NAME,"title":"(品牌全品項)",
                            "content":b.get_text(strip=True),"created_at":None})
        print(f"  抓到 {len(blocks)} 則"); time.sleep(3)

    if not records:
        print("抓到 0 則，可能被限流，稍後再試。"); raise SystemExit()
    df = clean_review_df(pd.DataFrame(records))
    df.insert(0,"post_id",range(1,len(df)+1))
    df = df[["post_id","brand","title","content","created_at"]]
    fn = f"../data/raw/competitor_{BRAND_NAME}_{BRAND_ID}_multipage.csv"
    df.to_csv(fn, index=False, encoding="utf-8-sig")
    print(f"清洗後保留 {len(df)} 則 → {fn}")
