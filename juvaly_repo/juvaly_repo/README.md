# Juvaly 網路聲量與競品輿情分析

保養品牌 **Juvaly** 的網路聲量分析專案。從公開評論中挖掘競品痛點，轉化為 Juvaly 的產品設計與行銷機會，最終產出給品牌方的 Executive Summary。

## 專案核心發現

1. **「質地黏膩」是全品類共通罩門** — 五個競品（含主打清爽者）無一例外，而 Juvaly 的「輕盈不黏」是差異化武器。
2. **新銳競品聲量「水分」高** — Inna Organic 非評論（邀稿文）佔 36%、nomel 29%，Juvaly 為 0%，真實口碑密度最高。
3. **競品口碑偏平淡** — 「效果無感」是共通弱點，Juvaly 的「修護有感」可正面切入。

## 資料管線（Data Pipeline）

```
爬取(@cosme) → 清洗 → 人工標註(黃金標準) → LLM 自動標註(經驗證) → 整合判讀 → 視覺化/報告
```

| 階段 | 腳本 | 說明 |
|------|------|------|
| 爬取 | `scripts/crawler_brand.py` | 抓 @cosme 品牌頁多頁評論（含 503 重試） |
| 清洗 | `scripts/clean_reviews.py` | 通用清洗函式（去文案、去過短、去重複） |
| 清洗 | `scripts/clean_brand.py` | 移除品牌頁評論前的作者資訊 |
| 標註驗證 | `scripts/groq_validate.py` | 用人工標註當考題，驗證 LLM 準確率 |
| 大規模標註 | `scripts/groq_label_batch.py` | LLM 自動標註（含限速處理、斷點續跑） |
| 分析 | `scripts/analyze.py` | 整合各品牌資料、產出圖表與總表 |

## 方法論重點

- **小樣本驅動 LLM 標註**：以 33 則人工精標當 few-shot 黃金標準，先驗證 LLM 情感準確率（達 82%）才大規模套用。
- **LLM 初篩 + 人工複核**：自動標註後，關鍵痛點再經人工逐則複核，確保結論可信。
- **誠實標示限制**：質化探索而非統計普查；小樣本品牌結論視為「方向訊號」。

## 安裝與執行

```bash
# 1. 安裝套件
pip install -r requirements.txt

# 2. 設定金鑰（複製範本後填入你的 Groq API key）
cp .env.example .env
# 編輯 .env，填入 GROQ_API_KEY

# 3. 爬取競品評論（修改腳本設定區的 BRAND_ID）
python scripts/crawler_brand.py

# 4. 清洗
python scripts/clean_brand.py

# 5. 先驗證 LLM 準確率，再標註
python scripts/groq_validate.py
python scripts/groq_label_batch.py

# 6. 整合分析
python scripts/analyze.py
```

## 目錄結構

```
juvaly_repo/
├── scripts/          # 所有 Python 腳本
├── data/raw/         # 原始抓取資料（.gitignore 排除，可重新產生）
├── data/labeled/     # 標註後資料
├── outputs/          # 圖表、總表、報告
├── docs/             # Executive Summary 等文件
├── requirements.txt
├── .env.example      # 金鑰範本（實際 .env 不上傳）
└── .gitignore
```

## 競品清單

| 品牌 | 定位 | 角色 |
|------|------|------|
| Juvaly | 抗氧化修護 | 本品牌 |
| Inna Organic | 有機精油 | 競品 |
| nomel | 清爽純淨 | 競品 |
| menomeno | 極簡天然 | 競品 |
| 簡單 JAN DAN | 天然低敏 | 競品 |
| DR.WU | 醫美保濕 | 對照組 |

## 資料倫理

- 僅抓取公開評論，遵守禮貌性抓取間隔。
- 不蒐集個資；分析以彙整統計為主。
- API 金鑰透過 `.env` 管理，不進版控。
