# 福岡市・北九州市 250mメッシュ クラスター分析

福岡市と北九州市の建物用途と飲食店データを用いた250mメッシュクラスター分析プロジェクト

## 特徴

- **9種類の建物用途による地域特徴分析**
  - 官公庁施設、共同住宅、住宅、商業施設、文教厚生施設
  - 業務施設、商業系複合施設、店舗等併用住宅、店舗等併用共同住宅

- **k=4,5,6,7 の複数クラスター分析**
  - 各クラスター数で独立した分析結果を提供
  - 用途別比率に基づく自動命名ロジック

- **用途別の色分け表示**
  - 住居系（純住宅、戸建住宅）: 濃い緑
  - 集合住宅系: 薄い緑
  - 店舗併用住宅系: 黄緑
  - 商業系（商業集積、商業混在、複合商業）: 黄色
  - 業務系: 赤
  - 文教施設、官公庁: 青系・紫系
  - 混合地域: オレンジ
  - 低密度地域: グレー

- **Mapbox による地図可視化**
  - クラスター別の色分け表示
  - 飲食店密度ヒートマップ
  - 建物総数ヒートマップ
  - インタラクティブな凡例とフィルター

## セットアップ

### 1. データ配置

以下のファイルを `data/` フォルダに配置してください:

```
fukuoka_analysis_simple/
├── data/
│   ├── building_centroid_all.geojson       # 建物重心データ
│   ├── fukuoka_40100_food_business_all.csv # 飲食店データ
│   └── mesh_shapefiles/                    # 250mメッシュShapefile
│       ├── QXYSWQ4930/
│       │   ├── *.shp, *.shx, *.dbf, *.prj
│       ├── QXYSWQ5030/
│       │   ├── *.shp, *.shx, *.dbf, *.prj
│       ├── QXYSWQ5031/
│       │   ├── *.shp, *.shx, *.dbf, *.prj
│       └── QXYSWQ5130/
│           ├── *.shp, *.shx, *.dbf, *.prj
```

### 2. ライブラリインストール

```bash
pip install geopandas pandas scikit-learn matplotlib scipy
```

### 3. 分析実行

```bash
# ステップ1: メッシュ集計（9用途対応）
python 1_mesh_analysis.py

# ステップ2: クラスタリング（k=4,5,6,7）
python 2_cluster_analysis_multi.py

# ステップ3: Web用データ準備
python prepare_web_data.py
```

### 4. Web可視化

1) **Mapbox アクセストークンの設定**

   `js/app.js` の3行目を編集:
   ```javascript
   mapboxgl.accessToken = 'YOUR_MAPBOX_ACCESS_TOKEN_HERE';
   ```
   
   トークン取得: https://account.mapbox.com/

2) **ローカルサーバー起動**

   ```bash
   python -m http.server 8000
   ```

3) **ブラウザで確認**

   http://localhost:8000 を開く

## 出力ファイル

### 分析結果

```
output/
├── k04/  # クラスター数4の結果
│   ├── mesh_with_clusters.geojson
│   ├── mesh_with_clusters.csv
│   ├── cluster_statistics.png    # クラスター別統計グラフ（4種）
│   ├── cluster_scatter.png       # 散布図
│   └── cluster_map.png           # 地図プレビュー
├── k05/  # クラスター数5の結果
│   └── ...
├── k06/  # クラスター数6の結果
│   └── ...
└── k07/  # クラスター数7の結果
    └── ...
```

### Web用データ

```
web_data/
├── mesh_clusters_k4.geojson       # 簡略化GeoJSON（k=4）
├── cluster_config_k4.json         # 統計情報（k=4）
├── mesh_clusters_k5.geojson       # 簡略化GeoJSON（k=5）
├── cluster_config_k5.json         # 統計情報（k=5）
├── mesh_clusters_k6.geojson       # 簡略化GeoJSON（k=6）
├── cluster_config_k6.json         # 統計情報（k=6）
├── mesh_clusters_k7.geojson       # 簡略化GeoJSON（k=7）
└── cluster_config_k7.json         # 統計情報（k=7）
```

## クラスター命名ロジック

用途比率と飲食店数に基づいて自動命名:

1. 商業比率 > 0.5 かつ 平均飲食店数 > 100 → **超高密度商業地域** (オレンジ寄りの黄色)
2. 商業比率 > 0.5 → **商業集積地域** (黄色)
3. 商業比率 > 0.1 → **商業混在地域** (明るい黄色)
4. 共同住宅比率 > 0.3 → **集合住宅地域** (薄い緑)
5. 住宅比率 > 0.7 → **戸建住宅地域** (濃い緑)
6. 店舗等併用共同住宅比率 > 0.2 → **店舗併用集合住宅地域** (黄緑)
7. 店舗等併用住宅比率 > 0.2 → **店舗併用住宅地域** (明るい黄緑)
8. 商業系複合施設比率 > 0.3 → **複合商業地域** (明るい黄色)
9. 業務施設比率 > 0.3 → **業務地域** (赤)
10. 文教厚生施設比率 > 0.5 → **文教施設地域** (青)
11. 官公庁施設比率 > 0.5 → **官公庁施設地域** (紫)
12. 平均建物数 < 50 → **低密度地域** (グレー)
13. その他 → **混合地域** (オレンジ)

## 特徴量

クラスタリングに使用する特徴量（11項目）:

1. 官公庁施設比率
2. 共同住宅比率
3. 住宅比率
4. 商業施設比率
5. 文教厚生施設比率
6. 業務施設比率
7. 商業系複合施設比率
8. 店舗等併用住宅比率
9. 店舗等併用共同住宅比率
10. 飲食店密度（飲食店数 / 建物総数）
11. 建物総数（対数変換: log(建物総数 + 1)）

## GitHub Pages へのデプロイ

```bash
git init
git add .
git commit -m "Add cluster analysis viewer"
git branch -M main
git remote add origin https://github.com/yourusername/fukuoka-cluster-viewer.git
git push -u origin main
```

GitHub の Settings → Pages で main ブランチを公開

## プロジェクト構成

```
fukuoka_analysis_simple/
├── 1_mesh_analysis.py              # メッシュ集計スクリプト
├── 2_cluster_analysis_multi.py     # クラスタリングスクリプト
├── prepare_web_data.py             # Web用データ準備スクリプト
├── index.html                      # メインHTML
├── css/
│   └── style.css                   # スタイルシート
├── js/
│   └── app.js                      # JavaScript
├── .gitignore                      # Git除外設定
├── README.md                       # このファイル
├── data/                           # 入力データ（要配置）
├── output/                         # 分析結果出力先
└── web_data/                       # Web用データ出力先
```

## トラブルシューティング

### FileNotFoundError: .shp ファイルが見つかりません

- `data/mesh_shapefiles/` 内にShapefileを配置してください
- ZIP ファイルは解凍して配置してください

### Web可視化でエラーが発生

1. `prepare_web_data.py` を実行して `web_data/` フォルダを生成
2. Mapbox アクセストークンを `js/app.js` に設定
3. ブラウザのコンソールでエラーを確認

### GitHub Pages で地図が表示されない

- Mapbox アクセストークンが正しく設定されているか確認
- ブラウザの開発者ツールでエラーを確認
- `web_data/` フォルダがリポジトリに含まれているか確認

## ライセンス

このプロジェクトは分析用途のみに使用してください。
