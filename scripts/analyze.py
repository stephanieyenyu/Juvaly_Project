# -*- coding: utf-8 -*-
"""整合各品牌標註資料，產出情感分布、痛點排名、視覺化圖表與總表"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib, os
from matplotlib import font_manager

for fp in ["/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
           "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"]:
    if os.path.exists(fp):
        font_manager.fontManager.addfont(fp)
        matplotlib.rcParams['font.family'] = font_manager.FontProperties(fname=fp).get_name()
        break
matplotlib.rcParams['axes.unicode_minus'] = False

FILES = {
    'Juvaly':'../data/labeled/juvaly_cosme_labeled.csv',
    'DR.WU':'../data/labeled/DR_WU_147_labeled.csv',
    'Inna Organic':'../data/labeled/InnaOrganic_labeled.csv',
    'nomel':'../data/labeled/nomel_labeled.csv',
    'menomeno+簡單':'../data/labeled/menomeno_jandan_labeled.csv',
    '綠藤':'../data/labeled/綠藤_110_labeled.csv',
}

def normalize_pain(p):
    p=str(p).strip()
    if '黏' in p or '膩' in p: return '質地黏膩'
    if '無感' in p or '沒感' in p: return '效果無感'
    if '香' in p or '味' in p: return '香味問題'
    if '包裝' in p or '永續' in p: return '包裝設計'
    if '價' in p: return '價格偏高'
    if '吸收' in p: return '吸收慢'
    return None

def main():
    rows=[]
    pain_counts={}
    pain_brands={}
    for brand,f in FILES.items():
        d=pd.read_csv(f); sc=d['sentiment'].value_counts().to_dict()
        total=len(d); err=sc.get('錯誤',0); nc=sc.get('非評論',0); valid=total-err-nc
        rows.append({'品牌':brand,'有效評論':valid,
            '正面率%':round(sc.get('正面',0)/valid*100) if valid else 0,
            '非評論率%':round(nc/(total-err)*100) if (total-err) else 0})

        for raw in d['pain_points'].dropna():
            for token in str(raw).split(';'):
                bucket = normalize_pain(token)
                if bucket is None:
                    continue
                pain_counts[bucket] = pain_counts.get(bucket, 0) + 1
                pain_brands.setdefault(bucket, set()).add(brand)

    summary=pd.DataFrame(rows)
    summary.to_csv('../outputs/competitor_summary_final.csv',index=False,encoding='utf-8-sig')
    print(summary.to_string(index=False))

    pain_rows=[{'痛點':k,'出現次數':v,'涉及品牌數':len(pain_brands[k]),
                '涉及品牌':'、'.join(sorted(pain_brands[k]))}
               for k,v in pain_counts.items()]
    pain_rank=pd.DataFrame(pain_rows).sort_values('出現次數',ascending=False).reset_index(drop=True)
    pain_rank.to_csv('../outputs/pain_point_ranking.csv',index=False,encoding='utf-8-sig')
    print()
    print(pain_rank.to_string(index=False))

    plot_summary(summary, pain_rank)

def plot_summary(summary, pain_rank):
    """六大痛點排行 + 各品牌非評論率／正面率，存成 outputs/final_competitor_analysis.png"""
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    axes[0].bar(pain_rank['痛點'], pain_rank['出現次數'], color='#d9534f')
    axes[0].set_title('六大痛點排行：「質地黏膩」最常見')
    axes[0].set_ylabel('提及次數')
    for i, v in enumerate(pain_rank['出現次數']):
        axes[0].text(i, v + 0.4, str(v), ha='center')
    axes[0].tick_params(axis='x', rotation=20)

    axes[1].bar(summary['品牌'], summary['非評論率%'], color='#f0ad4e')
    axes[1].set_title('「非評論/邀稿文」佔比：新銳品牌聲量水分高')
    axes[1].set_ylabel('非評論率 %')
    for i, v in enumerate(summary['非評論率%']):
        axes[1].text(i, v + 0.7, f'{v}%', ha='center')
    axes[1].tick_params(axis='x', rotation=20)

    axes[2].bar(summary['品牌'], summary['正面率%'], color='#5bc0de')
    axes[2].set_title('真實評論正面率：競品口碑偏平淡')
    axes[2].set_ylabel('正面率 %（占有效評論）')
    for i, v in enumerate(summary['正面率%']):
        axes[2].text(i, v + 0.7, f'{v}%', ha='center')
    axes[2].tick_params(axis='x', rotation=20)

    plt.tight_layout()
    plt.savefig('../outputs/final_competitor_analysis.png', dpi=150, bbox_inches='tight')
    plt.close(fig)

if __name__=="__main__":
    main()
