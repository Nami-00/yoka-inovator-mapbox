"""
設定ファイル（追加用途対応版）
このファイルで分析のパラメータをカスタマイズできます
"""

import os

# ============================================================
# ファイルパス設定
# ============================================================

# プロジェクトのルートディレクトリ
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# データディレクトリ
DATA_DIR = os.path.join(ROOT_DIR, 'data')
INPUT_BUILDING_FILE = os.path.join(DATA_DIR, 'building_centroid_all.geojson')
INPUT_FOOD_FILE = os.path.join(DATA_DIR, 'fukuoka_40100_food_business_all.csv')
INPUT_MESH_DIR = os.path.join(DATA_DIR, 'mesh_shapefiles')

# 出力ディレクトリ
OUTPUT_DIR = os.path.join(ROOT_DIR, 'output')
REPORT_DIR = os.path.join(OUTPUT_DIR, 'reports')

# 出力ファイル名
OUTPUT_MESH_RESULT_CSV = os.path.join(OUTPUT_DIR, 'mesh_analysis_result.csv')
OUTPUT_MESH_RESULT_GEOJSON = os.path.join(OUTPUT_DIR, 'mesh_analysis_result.geojson')
OUTPUT_MESH_CLUSTER_CSV = os.path.join(OUTPUT_DIR, 'mesh_with_clusters.csv')
OUTPUT_MESH_CLUSTER_GEOJSON = os.path.join(OUTPUT_DIR, 'mesh_with_clusters.geojson')

# ============================================================
# 分析パラメータ（追加用途対応）
# ============================================================

# 対象建物用途の定義（追加用途を含む）
TARGET_USAGES = {
    '421': '官公庁施設',
    '412': '共同住宅',
    '411': '住宅',
    '402': '商業施設',
    '422': '文教厚生施設',
    '401': '業務施設',                # 追加
    '404': '商業系複合施設',          # 追加
    '413': '店舗等併用住宅',          # 追加
    '414': '店舗等併用共同住宅'      # 追加
}

# クラスタリングパラメータ
N_CLUSTERS = 6  # デフォルトクラスタ数
RANDOM_STATE = 42  # 再現性のための乱数シード
KMEANS_N_INIT = 10  # K-meansの初期化回数

# 飲食店データのフィルタリング範囲（緯度経度）
FOOD_LAT_MIN = 30.0
FOOD_LAT_MAX = 35.0
FOOD_LON_MIN = 129.0
FOOD_LON_MAX = 132.0

# ============================================================
# 可視化設定
# ============================================================

# 図のサイズとDPI
FIGURE_SIZE = (15, 12)
FIGURE_DPI = 150

# カラーマップ
CLUSTER_CMAP = 'Set3'  # クラスタ地図用
DENSITY_CMAP = 'YlOrRd'  # 密度地図用
SCATTER_COLORS = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#ffff33', '#a65628']

# グリッド表示
SHOW_GRID = True
GRID_ALPHA = 0.3

# ============================================================
# 処理設定
# ============================================================

# GeoJSON読み込み時の進捗表示間隔
PROGRESS_INTERVAL = 50000

# メモリ節約モード（大規模データ用）
MEMORY_SAVE_MODE = False

# ============================================================
# ディレクトリ作成関数
# ============================================================

def create_directories():
    """必要なディレクトリを作成"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)
    os.makedirs(INPUT_MESH_DIR, exist_ok=True)

# ============================================================
# 検証関数
# ============================================================

def validate_files():
    """必要なファイルが存在するかチェック"""
    missing_files = []
    
    if not os.path.exists(INPUT_BUILDING_FILE):
        missing_files.append(INPUT_BUILDING_FILE)
    
    if not os.path.exists(INPUT_FOOD_FILE):
        missing_files.append(INPUT_FOOD_FILE)
    
    if not os.path.exists(INPUT_MESH_DIR):
        missing_files.append(INPUT_MESH_DIR)
    
    if missing_files:
        print("⚠️ 以下のファイルが見つかりません:")
        for f in missing_files:
            print(f"  - {f}")
        return False
    
    return True

# ============================================================
# 設定情報の表示
# ============================================================

def print_config():
    """現在の設定を表示"""
    print("=" * 60)
    print("現在の設定")
    print("=" * 60)
    print(f"プロジェクトディレクトリ: {ROOT_DIR}")
    print(f"データディレクトリ: {DATA_DIR}")
    print(f"出力ディレクトリ: {OUTPUT_DIR}")
    print(f"\nクラスタ数: {N_CLUSTERS}")
    print(f"対象建物用途: {len(TARGET_USAGES)}種類")
    for code, name in TARGET_USAGES.items():
        print(f"  - {code}: {name}")
    print("=" * 60)

if __name__ == '__main__':
    # このファイルを直接実行した場合、設定をチェック
    create_directories()
    print_config()
    
    if validate_files():
        print("\n✅ すべての必要ファイルが存在します")
    else:
        print("\n❌ 一部のファイルが不足しています")
        print("\nREADME.md を参照して、データファイルを配置してください")
