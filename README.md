# 福岡市・北九州市 250mメッシュクラスター分析（追加用途対応版）

## 📋 概要

福岡市と北九州市の建物用途データ（**9種類の用途**）と飲食店データを250mメッシュ単位で集計し、クラスタリング分析を実施。  
Mapbox GL JS を使用したインタラクティブWebアプリで k=4,5,6,7 のクラスター結果を可視化。

---

## ✅ **追加された建物用途（4種類）**

元の5種類に以下を追加:
- ✅ **業務施設**
- ✅ **商業系複合施設**
- ✅ **店舗等併用住宅**
- ✅ **店舗等併用共同住宅**

---

## 📊 **特徴量**

### **使用する特徴量（シンプル版）**
1. **各用途の割合（9種類）**
   - 官公庁施設割合
   - 共同住宅割合
   - 住宅割合
   - 商業施設割合
   - 文教厚生施設割合
   - **業務施設割合**（追加）
   - **商業系複合施設割合**（追加）
   - **店舗等併用住宅割合**（追加）
   - **店舗等併用共同住宅割合**（追加）

2. **飲食店密度**
   - 飲食店数 / 建物総数

3. **建物総数（対数変換）**
   - log(建物総数 + 1)

**合計: 11個の特徴量**

---

## 🗂️ ファイル構成

```
fukuoka_analysis_simple/
├── 1_mesh_analysis.py              # メッシュ集計スクリプト（9用途対応）
├── 2_cluster_analysis_multi.py     # クラスタリング分析 (k=4,5,6,7)
├── config.py                       # 設定ファイル（9用途対応）
├── prepare_web_data.py             # Web可視化データ準備
├── index.html                      # メインHTML
├── css/style.css                   # スタイルシート
├── js/app.js                       # JavaScriptロジック
├── data/                           # データ配置先
│   ├── building_centroid_all.geojson
│   ├── fukuoka_40100_food_business_all.csv
│   └── mesh_shapefiles/            # メッシュShapefile
├── output/                         # 分析結果出力先
└── README.md                       # このファイル
```

---

## 🚀 使用方法

### **1. データ準備**

以下のファイルを `data/` に配置:
- `building_centroid_all.geojson` (建物データ)
- `fukuoka_40100_food_business_all.csv` (飲食店データ)
- メッシュShapefile (.shp/.shx/.dbf/.prj) を `data/mesh_shapefiles/` に配置

### **2. 必要なライブラリをインストール**

```bash
pip install geopandas pandas scikit-learn matplotlib
```

### **3. 分析実行**

```bash
# ステップ1: メッシュ集計（9用途対応）
python 1_mesh_analysis.py

# ステップ2: クラスタリング分析 (k=4,5,6,7)
python 2_cluster_analysis_multi.py

# ステップ3: Web可視化データ準備
python prepare_web_data.py
```

### **4. Mapbox設定**

`js/app.js` の **3行目** を編集:
```javascript
mapboxgl.accessToken = 'YOUR_MAPBOX_ACCESS_TOKEN_HERE';
```

[Mapbox アクセストークンを取得](https://account.mapbox.com/)

### **5. ローカルで動作確認**

```bash
python -m http.server 8000
```

ブラウザで `http://localhost:8000` を開く

### **6. GitHub Pages にデプロイ**

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/yourusername/fukuoka-cluster-viewer.git
git push -u origin main
```

GitHub の Settings → Pages で `main` ブランチを公開

---

## 📝 クラスター命名ロジック

```python
# 商業施設の比率が高い場合
if 商業施設比率 > 0.5:
    if 平均飲食店数 > 100:
        → "超高密度商業地域"
    else:
        → "商業集積地域"
elif 商業施設比率 > 0.1:
    → "商業混在地域"

# 最大用途比率に基づく命名
elif 共同住宅比率 > 0.3:
    → "集合住宅地域"
elif 住宅比率 > 0.7:
    → "戸建住宅地域"
elif 店舗等併用共同住宅比率 > 0.2:
    → "店舗併用集合住宅地域"  # 新
elif 店舗等併用住宅比率 > 0.2:
    → "店舗併用住宅地域"       # 新
elif 商業系複合施設比率 > 0.3:
    → "複合商業地域"           # 新
elif 業務施設比率 > 0.3:
    → "業務地域"               # 新
elif 文教厚生施設比率 > 0.5:
    → "文教施設地域"
elif 官公庁施設比率 > 0.5:
    → "官公庁施設地域"
else:
    → "混合地域"
```

---

## 📊 出力ファイル

### **分析結果 (output/kXX/)**
- `mesh_with_clusters.geojson` / `.csv` - クラスタリング結果
- `cluster_statistics.png` - 統計グラフ（4種類）
  - 平均建物総数
  - 平均飲食店数
  - 建物用途比率
  - メッシュ数
- `cluster_scatter.png` - 散布図（4種類）
- `cluster_map.png` - 地図プロット
- `reports/cluster_analysis_report.md` - 詳細レポート

### **Web用データ (web_data/)**
- `mesh_clusters_k{4,5,6,7}.geojson` - 簡略化GeoJSON
- `cluster_config_k{4,5,6,7}.json` - クラスター統計JSON

---

## 🎨 Web可視化機能

✅ **クラスター数切替**: k=4/5/6/7  
✅ **表示モード**: クラスター別 / 飲食店密度 / 建物総数  
✅ **透明度調整**  
✅ **クラスターフィルター** (個別ON/OFF)  
✅ **統計情報表示**  
✅ **インタラクティブポップアップ**  

---

## 🔧 カスタマイズ

### **クラスター数を変更**
`2_cluster_analysis_multi.py` の **7行目** を編集:
```python
K_LIST = [4, 5, 6, 7, 8]  # 任意のクラスター数を追加
```

### **対象用途を変更**
`config.py` の `TARGET_USAGES` を編集

---

## 📖 ライセンス

MIT License

---

## 👤 作成者

namiさん - データ分析技術者

**追加用途対応により、より詳細な地域特性分析が可能になりました！**
