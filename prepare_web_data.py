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
    print(f"簡略化処理: {input_geojson.name} → {output_geojson.name}")
    
    gdf = gpd.read_file(input_geojson)
    gdf['geometry'] = gdf['geometry'].simplify(tolerance)
    gdf.to_file(output_geojson, driver='GeoJSON')
    
    original_size = input_geojson.stat().st_size / 1024 / 1024
    simplified_size = output_geojson.stat().st_size / 1024 / 1024
    
    print(f"   元ファイル: {original_size:.2f} MB → 簡略化後: {simplified_size:.2f} MB ({(1 - simplified_size/original_size)*100:.1f}% 削減)")

def extract_cluster_config(csv_file, output_json, k):
    """CSV からクラスター統計情報を抽出して JSON 化"""
    print(f"統計情報抽出: {csv_file.name} → {output_json.name}")
    
    df = pd.read_csv(csv_file)
    
    # クラスター列名（k別ではなく共通の 'cluster' を使用）
    cluster_col = 'cluster'
    
    if cluster_col not in df.columns:
        print(f"警告: '{cluster_col}' 列が見つかりません")
        print(f"   利用可能な列: {df.columns.tolist()}")
        return
    
    # クラスター統計の計算
    cluster_stats = []
    for cluster_id in sorted(df[cluster_col].unique()):
        cluster_data = df[df[cluster_col] == cluster_id]
        
        # 建物用途の集計
        building_types = {}
        for col in cluster_data.columns:
            if col.startswith('建物_'):
                building_types[col.replace('建物_', '')] = int(cluster_data[col].sum())
        
        # 統計情報
        stats = {
            'id': int(cluster_id),
            'name': f'クラスター {cluster_id}',
            'color': get_cluster_color(cluster_id, k),
            'count': int(len(cluster_data)),
            'avg_buildings': float(cluster_data['建物総数'].mean()),
            'avg_restaurants': float(cluster_data['飲食店数'].mean()),
            'building_types': building_types
        }
        
        cluster_stats.append(stats)
    
    # JSON として保存
    config = {
        'cluster_count': k,
        'total_meshes': int(len(df)),
        'clusters': cluster_stats
    }
    
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"   完了: {k}個のクラスター統計を出力\n")


def get_cluster_color(cluster_id, total_clusters):
    """クラスター ID に応じた色を返す"""
    palettes = {
        4: ['#e74c3c', '#f39c12', '#2ecc71', '#3498db'],
        5: ['#e74c3c', '#f39c12', '#2ecc71', '#3498db', '#9b59b6'],
        6: ['#e74c3c', '#e67e22', '#f1c40f', '#2ecc71', '#3498db', '#9b59b6'],
        7: ['#e74c3c', '#e67e22', '#f39c12', '#f1c40f', '#2ecc71', '#3498db', '#9b59b6']
    }
    
    colors = palettes.get(total_clusters, palettes[5])
    return colors[cluster_id % len(colors)]

def main():
    """メイン処理: k=4,5,6,7 の全データを変換"""
    
    print("=" * 60)
    print("Mapbox可視化用データ準備")
    print("=" * 60)
    print()
    
    for k in [4, 5, 6, 7]:
        print(f"--- クラスター数: {k} ---")
        
        # k04, k05, k06, k07 フォルダ内のファイルを参照
        input_geojson = OUTPUT_DIR / f'k{k:02d}' / 'mesh_with_clusters.geojson'
        input_csv = OUTPUT_DIR / f'k{k:02d}' / 'mesh_with_clusters.csv'
        
        output_geojson = WEB_DATA_DIR / f'mesh_clusters_k{k}.geojson'
        output_json = WEB_DATA_DIR / f'cluster_config_k{k}.json'
        
        if not input_geojson.exists():
            print(f"警告: {input_geojson} が見つかりません\n")
            continue
        
        simplify_geometry(input_geojson, output_geojson)
        
        if input_csv.exists():
            extract_cluster_config(input_csv, output_json, k)
        else:
            print(f"警告: {input_csv} が見つかりません\n")
    
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
