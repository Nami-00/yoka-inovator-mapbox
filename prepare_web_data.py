"""
Mapbox可視化用データ準備スクリプト
k=4,5,6,7 の各クラスター結果を web_data/ へ変換
"""
import json
import geopandas as gpd
import pandas as pd
from pathlib import Path

# ディレクトリ設定
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / 'output'
WEB_DATA_DIR = BASE_DIR / 'web_data'

# web_data ディレクトリ作成
WEB_DATA_DIR.mkdir(exist_ok=True)

def simplify_geometry(input_geojson, output_geojson, tolerance=0.0001):
    """GeoJSON の幾何形状を簡略化してファイルサイズを削減"""
    print(f"   簡略化処理: {input_geojson.name} → {output_geojson.name}")
    
    gdf = gpd.read_file(input_geojson)
    gdf['geometry'] = gdf['geometry'].simplify(tolerance)
    gdf.to_file(output_geojson, driver='GeoJSON')
    
    original_size = input_geojson.stat().st_size / 1024 / 1024
    simplified_size = output_geojson.stat().st_size / 1024 / 1024
    
    print(f"   元ファイル: {original_size:.2f} MB → 簡略化後: {simplified_size:.2f} MB ({(1 - simplified_size/original_size)*100:.1f}% 削減)")

def get_cluster_name_and_color(cluster_data):
    """
    建物用途の比率から命名ロジックに従ってクラスター名と色を決定
    
    色分けルール:
    - 住居系（純住宅、戸建住宅）: 濃い緑 #27ae60
    - 集合住宅系: 薄い緑 #7dcea0
    - 店舗併用住宅系: 黄緑 #aed581
    - 商業系（商業集積、商業混在、複合商業）: 黄色 #f1c40f
    - 業務系: 赤 #e74c3c
    - 文教施設、官公庁: 青系・紫系
    - 混合・低密度: グレー系
    """
    
    # 用途比率の計算
    total_buildings = cluster_data['建物総数'].sum()
    if total_buildings == 0:
        return "低密度地域", "#bdc3c7"
    
    # 各用途の比率を計算
    ratios = {}
    usage_cols = ['官公庁施設', '共同住宅', '住宅', '商業施設', '文教厚生施設', 
                  '業務施設', '商業系複合施設', '店舗等併用住宅', '店舗等併用共同住宅']
    
    for usage in usage_cols:
        col_name = f'建物_{usage}'
        if col_name in cluster_data.columns:
            ratios[usage] = cluster_data[col_name].sum() / total_buildings
        else:
            ratios[usage] = 0
    
    # 飲食店数の平均
    avg_restaurants = cluster_data['飲食店数'].mean()
    
    # 命名ロジック（優先度順に判定）
    商業比率 = ratios.get('商業施設', 0)
    共同住宅比率 = ratios.get('共同住宅', 0)
    住宅比率 = ratios.get('住宅', 0)
    店舗等併用共同住宅比率 = ratios.get('店舗等併用共同住宅', 0)
    店舗等併用住宅比率 = ratios.get('店舗等併用住宅', 0)
    商業系複合施設比率 = ratios.get('商業系複合施設', 0)
    業務施設比率 = ratios.get('業務施設', 0)
    文教厚生施設比率 = ratios.get('文教厚生施設', 0)
    官公庁施設比率 = ratios.get('官公庁施設', 0)
    
    # 命名ロジックと色分け
    if 商業比率 > 0.5 and avg_restaurants > 100:
        return "超高密度商業地域", "#f39c12"  # オレンジ寄りの黄色
    elif 商業比率 > 0.5:
        return "商業集積地域", "#f1c40f"  # 黄色
    elif 商業比率 > 0.1:
        return "商業混在地域", "#f4d03f"  # 明るい黄色
    elif 共同住宅比率 > 0.3:
        return "集合住宅地域", "#7dcea0"  # 薄い緑
    elif 住宅比率 > 0.7:
        return "戸建住宅地域", "#27ae60"  # 濃い緑
    elif 店舗等併用共同住宅比率 > 0.2:
        return "店舗併用集合住宅地域", "#aed581"  # 黄緑
    elif 店舗等併用住宅比率 > 0.2:
        return "店舗併用住宅地域", "#c5e1a5"  # 明るい黄緑
    elif 商業系複合施設比率 > 0.3:
        return "複合商業地域", "#ffd54f"  # 明るい黄色
    elif 業務施設比率 > 0.3:
        return "業務地域", "#e74c3c"  # 赤
    elif 文教厚生施設比率 > 0.5:
        return "文教施設地域", "#3498db"  # 青
    elif 官公庁施設比率 > 0.5:
        return "官公庁施設地域", "#9b59b6"  # 紫
    elif total_buildings / len(cluster_data) < 50:  # 平均建物数が50未満
        return "低密度地域", "#95a5a6"  # グレー
    else:
        return "混合地域", "#e67e22"  # オレンジ

def extract_cluster_config(csv_file, output_json, k):
    """CSV からクラスター統計情報を抽出して JSON 化"""
    print(f"   統計情報抽出: {csv_file.name} → {output_json.name}")
    
    df = pd.read_csv(csv_file)
    cluster_col = 'cluster'
    
    if cluster_col not in df.columns:
        print(f"   警告: '{cluster_col}' 列が見つかりません")
        print(f"   利用可能な列: {list(df.columns)}")
        return
    
    cluster_stats = []
    for cluster_id in sorted(df[cluster_col].unique()):
        cluster_data = df[df[cluster_col] == cluster_id]
        
        # クラスター名と色を決定
        cluster_name, cluster_color = get_cluster_name_and_color(cluster_data)
        
        building_types = {}
        for col in cluster_data.columns:
            if col.startswith('建物_'):
                building_types[col.replace('建物_', '')] = int(cluster_data[col].sum())
        
        stats = {
            'id': int(cluster_id),
            'name': cluster_name,  # 命名ロジックによる名前
            'color': cluster_color,  # 用途別の色
            'count': int(len(cluster_data)),
            'avg_buildings': float(cluster_data['建物総数'].mean()),
            'avg_restaurants': float(cluster_data['飲食店数'].mean()),
            'building_types': building_types
        }
        
        cluster_stats.append(stats)
    
    config = {
        'cluster_count': k,
        'total_meshes': int(len(df)),
        'clusters': cluster_stats
    }
    
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"   完了: {k}個のクラスター統計を出力")
    
    # クラスター名と色を表示
    for stats in cluster_stats:
        print(f"      クラスター {stats['id']}: {stats['name']} ({stats['color']})")
    print()

def main():
    """メイン処理: k=4,5,6,7 の全データを変換"""
    
    print("=" * 60)
    print("Mapbox可視化用データ準備")
    print("=" * 60)
    print()
    
    for k in [4, 5, 6, 7]:
        print(f"--- クラスター数: {k} ---")
        
        input_geojson = OUTPUT_DIR / f'k{k:02d}' / 'mesh_with_clusters.geojson'
        input_csv = OUTPUT_DIR / f'k{k:02d}' / 'mesh_with_clusters.csv'
        
        output_geojson = WEB_DATA_DIR / f'mesh_clusters_k{k}.geojson'
        output_json = WEB_DATA_DIR / f'cluster_config_k{k}.json'
        
        if not input_geojson.exists():
            print(f"   スキップ: {input_geojson} が見つかりません\n")
            continue
        
        simplify_geometry(input_geojson, output_geojson)
        
        if input_csv.exists():
            extract_cluster_config(input_csv, output_json, k)
        else:
            print(f"   統計情報スキップ: {input_csv} が見つかりません\n")
    
    print("=" * 60)
    print("データ準備完了")
    print("=" * 60)
    print(f"\n出力先: {WEB_DATA_DIR}")
    print("\n次のステップ:")
    print("1) index.html の mapbox.accessToken を設定")
    print("2) ローカルで動作確認: python -m http.server 8000")
    print("3) ブラウザで http://localhost:8000 を開く\n")

if __name__ == '__main__':
    main()
