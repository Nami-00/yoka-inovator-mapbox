#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ステップ2: クラスタリング分析スクリプト（追加用途対応版）
k=4,5,6,7 で同条件で繰り返し実行
"""
# ===============================
# クラスタ数の設定
# ===============================
K_LIST = [4, 5, 6, 7]

import sys
import time
from pathlib import Path

import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

# japanize_matplotlib（日本語表示）
try:
    import japanize_matplotlib  # noqa: F401
except ImportError:
    # フォールバック: MS Gothic
    matplotlib.rcParams['font.sans-serif'] = ['MS Gothic', 'Yu Gothic', 'Meiryo']
    matplotlib.rcParams["axes.unicode_minus"] = False

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

import warnings
warnings.filterwarnings('ignore')

# 設定ファイルのインポート
try:
    import config
except ImportError:
    print("❌ config.py が見つかりません")
    sys.exit(1)

plt.rcParams['figure.figsize'] = config.FIGURE_SIZE


def print_section(title):
    """セクションタイトルを表示"""
    print(f"\n{'=' * 60}")
    print(f"{title}")
    print('=' * 60)


def load_data():
    """ステップ1の結果を読み込み"""
    print_section("1. データ読み込み")

    if not Path(config.OUTPUT_MESH_RESULT_CSV).exists():
        raise FileNotFoundError(
            f"集計結果が見つかりません: {config.OUTPUT_MESH_RESULT_CSV}\n"
            "先に 1_mesh_analysis.py を実行してください"
        )

    print(f"  CSVを読み込み中: {config.OUTPUT_MESH_RESULT_CSV}")
    result_df = pd.read_csv(config.OUTPUT_MESH_RESULT_CSV, encoding='utf-8-sig')

    print(f"  GeoJSONを読み込み中: {config.OUTPUT_MESH_RESULT_GEOJSON}")
    result_gdf = gpd.read_file(config.OUTPUT_MESH_RESULT_GEOJSON)

    print(f"\n  ✓ メッシュ数: {len(result_df):,}")
    print(f"  ✓ カラム数: {len(result_df.columns)}")

    return result_df, result_gdf


def create_features(result_df: pd.DataFrame):
    """
    特徴量を作成（元のロジックを維持、追加用途のみ対応）
    
    特徴量:
    - 各用途の割合 (%) ← 9種類に拡張
    - 飲食店密度
    - 建物総数（対数変換）
    """
    print_section("2. 特徴量エンジニアリング")

    feature_cols = []

    # 各用途の比率を計算（9用途対応）
    print("  建物用途比率を計算中...")
    for col in result_df.columns:
        if col.startswith('建物_'):
            ratio_col = col + '_比率'
            result_df[ratio_col] = result_df[col] / (result_df['建物総数'] + 1e-6)
            feature_cols.append(ratio_col)

    # 飲食店密度
    print("  飲食店密度を計算中...")
    result_df['飲食店密度'] = result_df['飲食店数'] / (result_df['建物総数'] + 1e-6)
    feature_cols.append('飲食店密度')

    # 建物総数（対数変換）
    result_df['建物総数_log'] = np.log1p(result_df['建物総数'])
    feature_cols.append('建物総数_log')

    print(f"\n  ✓ 作成された特徴量: {len(feature_cols)}個")
    for feat in feature_cols:
        print(f"    - {feat}")

    return result_df, feature_cols


def perform_clustering(result_df: pd.DataFrame, feature_cols, n_clusters: int):
    """K-meansクラスタリングを実行"""
    print_section(f"3. クラスタリング実行（k={n_clusters}）")

    X = result_df[feature_cols].fillna(0).values

    print("  特徴量を標準化中...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    print(f"  K-means実行中（k={n_clusters}）...")
    start_time = time.time()

    kmeans = KMeans(
        n_clusters=n_clusters,
        random_state=config.RANDOM_STATE,
        n_init=config.KMEANS_N_INIT
    )
    result_df = result_df.copy()
    result_df['cluster'] = kmeans.fit_predict(X_scaled)

    elapsed = time.time() - start_time
    print(f"  ✓ クラスタリング完了 ({elapsed:.1f}秒)")

    print("\n  クラスタ別メッシュ数:")
    for cluster_id in range(n_clusters):
        count = int((result_df['cluster'] == cluster_id).sum())
        pct = (count / len(result_df)) * 100
        print(f"    クラスタ{cluster_id}: {count:,}メッシュ ({pct:.1f}%)")

    return result_df, kmeans


def analyze_clusters(result_df: pd.DataFrame, n_clusters: int):
    """クラスタの特徴を分析"""
    print_section("4. クラスタ特徴分析")

    cluster_profiles = []

    for cluster_id in range(n_clusters):
        cluster_data = result_df[result_df['cluster'] == cluster_id]

        profile = {
            'クラスタID': cluster_id,
            'メッシュ数': len(cluster_data),
            '平均建物総数': cluster_data['建物総数'].mean(),
            '平均飲食店数': cluster_data['飲食店数'].mean(),
        }

        # 用途別平均比率
        for col in result_df.columns:
            if col.endswith('_比率') and col.startswith('建物_'):
                usage_name = col.replace('建物_', '').replace('_比率', '')
                profile[f'平均{usage_name}比率'] = cluster_data[col].mean()

        cluster_profiles.append(profile)

    cluster_df = pd.DataFrame(cluster_profiles)

    print("\n  クラスタプロファイル:")
    print(cluster_df.to_string(index=False))

    return cluster_df


def self_assign_name(row, ratio_cols):
    """比率に基づいてクラスタ名を自動決定"""
    max_ratio = 0
    max_usage = ''

    for col in ratio_cols:
        if row[col] > max_ratio:
            max_ratio = row[col]
            max_usage = col.replace('平均', '').replace('比率', '')

    # 命名ロジック（追加用途対応）
    if '共同住宅' in max_usage and max_ratio > 0.3:
        return '集合住宅地域'
    elif '住宅' in max_usage and max_ratio > 0.7:
        return '戸建住宅地域'
    elif '店舗等併用共同住宅' in max_usage and max_ratio > 0.2:
        return '店舗併用集合住宅地域'
    elif '店舗等併用住宅' in max_usage and max_ratio > 0.2:
        return '店舗併用住宅地域'
    elif '商業系複合施設' in max_usage and max_ratio > 0.3:
        return '複合商業地域'
    elif '業務施設' in max_usage and max_ratio > 0.3:
        return '業務地域'
    elif '文教厚生施設' in max_usage and max_ratio > 0.5:
        return '文教施設地域'
    elif '官公庁施設' in max_usage and max_ratio > 0.5:
        return '官公庁施設地域'
    else:
        return '混合地域'


def assign_cluster_names(result_df: pd.DataFrame, cluster_df: pd.DataFrame, n_clusters: int):
    """クラスタに名前を付ける（元のロジックを維持、追加用途対応）"""
    print_section("5. クラスタ命名")

    cluster_names = {}

    for _, row in cluster_df.iterrows():
        cluster_id = int(row['クラスタID'])

        ratio_cols = [c for c in row.index if c.endswith('比率')]

        # 商業施設の比率チェック
        if any('商業施設' in c for c in ratio_cols):
            com_ratio = row[[c for c in ratio_cols if '商業施設' in c][0]]
            if com_ratio > 0.5:
                if row['平均飲食店数'] > 100:
                    name = '超高密度商業地域'
                else:
                    name = '商業集積地域'
            elif com_ratio > 0.1:
                name = '商業混在地域'
            else:
                name = self_assign_name(row, ratio_cols)
        else:
            name = self_assign_name(row, ratio_cols)

        cluster_names[cluster_id] = name

    result_df = result_df.copy()
    result_df['cluster_name'] = result_df['cluster'].map(cluster_names)

    print("\n  クラスタ名:")
    for cid, cname in cluster_names.items():
        count = int((result_df['cluster'] == cid).sum())
        print(f"    クラスタ{cid}: {cname} ({count:,}メッシュ)")

    return result_df, cluster_names


def create_scatter_plots(result_df: pd.DataFrame, cluster_names: dict, n_clusters: int, out_dir: Path):
    """散布図マトリックスを作成"""
    fig, axes = plt.subplots(2, 2, figsize=config.FIGURE_SIZE)

    scatter_features = [
        ('建物総数', '飲食店数'),
        ('建物_住宅_比率', '建物_共同住宅_比率'),
        ('建物_商業施設_比率', '飲食店密度'),
        ('建物_文教厚生施設_比率', '建物_官公庁施設_比率')
    ]

    for idx, (feat1, feat2) in enumerate(scatter_features):
        if feat1 not in result_df.columns or feat2 not in result_df.columns:
            continue

        ax = axes[idx // 2, idx % 2]

        for cluster_id in range(n_clusters):
            cluster_data = result_df[result_df['cluster'] == cluster_id]
            ax.scatter(
                cluster_data[feat1],
                cluster_data[feat2],
                alpha=0.5,
                s=20,
                c=config.SCATTER_COLORS[cluster_id % len(config.SCATTER_COLORS)],
                label=f'C{cluster_id}: {cluster_names.get(cluster_id, "")}'
            )

        ax.set_xlabel(feat1.replace('建物_', '').replace('_', ' '))
        ax.set_ylabel(feat2.replace('建物_', '').replace('_', ' '))
        ax.set_title(f'{feat1} vs {feat2}', fontsize=12, fontweight='bold')
        ax.legend(fontsize=7, loc='best')
        if config.SHOW_GRID:
            ax.grid(alpha=config.GRID_ALPHA)

    plt.tight_layout()
    output_path = out_dir / 'cluster_scatter.png'
    plt.savefig(output_path, dpi=config.FIGURE_DPI, bbox_inches='tight')
    plt.close()
    print(f"  ✓ {output_path}")


def create_maps(result_df: pd.DataFrame, n_clusters: int, out_dir: Path):
    """地図を作成"""
    result_gdf = gpd.read_file(config.OUTPUT_MESH_RESULT_GEOJSON)
    result_gdf['cluster'] = result_df['cluster'].values
    result_gdf['飲食店数'] = result_df['飲食店数'].values

    fig, axes = plt.subplots(1, 2, figsize=(20, 10))

    ax = axes[0]
    result_gdf.plot(column='cluster', ax=ax, cmap=config.CLUSTER_CMAP,
                    legend=True, edgecolor='none', alpha=0.7)
    ax.set_title(f'クラスター分布地図 (k={n_clusters})', fontsize=16, fontweight='bold')
    ax.set_xlabel('経度')
    ax.set_ylabel('緯度')
    if config.SHOW_GRID:
        ax.grid(alpha=config.GRID_ALPHA)

    ax = axes[1]
    result_gdf.plot(column='飲食店数', ax=ax, cmap=config.DENSITY_CMAP,
                    legend=True, edgecolor='none', alpha=0.7)
    ax.set_title('飲食店密度マップ', fontsize=16, fontweight='bold')
    ax.set_xlabel('経度')
    ax.set_ylabel('緯度')
    if config.SHOW_GRID:
        ax.grid(alpha=config.GRID_ALPHA)

    plt.tight_layout()
    output_path = out_dir / 'cluster_map.png'
    plt.savefig(output_path, dpi=config.FIGURE_DPI, bbox_inches='tight')
    plt.close()
    print(f"  ✓ {output_path}")


def create_visualizations(result_df, cluster_df, cluster_names, n_clusters, out_dir: Path):
    """可視化を作成"""
    out_dir.mkdir(parents=True, exist_ok=True)

    print_section("6. 可視化作成")

    print("  統計グラフを作成中...")
    fig, axes = plt.subplots(2, 2, figsize=config.FIGURE_SIZE)

    ax = axes[0, 0]
    cluster_df.plot(x='クラスタID', y='平均建物総数', kind='bar', ax=ax, color='skyblue')
    ax.set_title('クラスタ別平均建物総数', fontsize=14, fontweight='bold')
    ax.set_xlabel('クラスタID')
    ax.set_ylabel('平均建物数')
    if config.SHOW_GRID:
        ax.grid(axis='y', alpha=config.GRID_ALPHA)

    ax = axes[0, 1]
    cluster_df.plot(x='クラスタID', y='平均飲食店数', kind='bar', ax=ax, color='coral')
    ax.set_title('クラスタ別平均飲食店数', fontsize=14, fontweight='bold')
    ax.set_xlabel('クラスタID')
    ax.set_ylabel('平均飲食店数')
    if config.SHOW_GRID:
        ax.grid(axis='y', alpha=config.GRID_ALPHA)

    ax = axes[1, 0]
    usage_cols = [c for c in cluster_df.columns if c.endswith('比率')][:4]
    if usage_cols:
        cluster_df[usage_cols].plot(
            kind='bar', stacked=True, ax=ax,
            color=['#8dd3c7', '#ffffb3', '#bebada', '#fb8072']
        )
        ax.set_title('クラスタ別建物用途比率', fontsize=14, fontweight='bold')
        ax.set_xlabel('クラスタID')
        ax.set_ylabel('比率')
        ax.set_xticklabels([str(i) for i in range(n_clusters)], rotation=0)
        ax.legend(fontsize=8, loc='best')
        if config.SHOW_GRID:
            ax.grid(axis='y', alpha=config.GRID_ALPHA)

    ax = axes[1, 1]
    cluster_df.plot(x='クラスタID', y='メッシュ数', kind='bar', ax=ax, color='lightgreen')
    ax.set_title('クラスタ別メッシュ数', fontsize=14, fontweight='bold')
    ax.set_xlabel('クラスタID')
    ax.set_ylabel('メッシュ数')
    if config.SHOW_GRID:
        ax.grid(axis='y', alpha=config.GRID_ALPHA)

    plt.tight_layout()
    output_path = out_dir / 'cluster_statistics.png'
    plt.savefig(output_path, dpi=config.FIGURE_DPI, bbox_inches='tight')
    plt.close()
    print(f"  ✓ {output_path}")

    print("  散布図を作成中...")
    create_scatter_plots(result_df, cluster_names, n_clusters, out_dir)

    print("  地図を作成中...")
    create_maps(result_df, n_clusters, out_dir)


def create_cluster_report(result_df: pd.DataFrame, cluster_df: pd.DataFrame, cluster_names: dict,
                          n_clusters: int, report_dir: Path):
    """クラスタ分析レポートを作成"""
    report = []
    report.append("# 福岡市・北九州市 250mメッシュ地域特性分析\n")
    report.append("## 1. 概要")
    report.append(f"- 分析メッシュ数: {len(result_df):,}")
    report.append(f"- 総建物数: {result_df['建物総数'].sum():,.0f}")
    report.append(f"- 総飲食店数: {result_df['飲食店数'].sum():,.0f}")
    report.append(f"- クラスタ数: {n_clusters}\n")

    report.append("## 2. クラスタ別特徴\n")

    for cluster_id in range(n_clusters):
        cluster_data = result_df[result_df['cluster'] == cluster_id]
        cname = cluster_names.get(cluster_id, "")

        report.append(f"### クラスタ{cluster_id}: {cname}")
        report.append(f"- メッシュ数: {len(cluster_data):,}")
        report.append(f"- 平均建物総数: {cluster_data['建物総数'].mean():.1f}棟")
        report.append(f"- 平均飲食店数: {cluster_data['飲食店数'].mean():.1f}件")

        if len(cluster_data) > 0:
            top3 = cluster_data.nlargest(3, '建物総数')
            report.append("- 代表的メッシュ:")
            for _, mesh in top3.iterrows():
                report.append(
                    f"  - {mesh['mesh_code']}: 建物{mesh['建物総数']:.0f}棟, "
                    f"飲食店{mesh['飲食店数']:.0f}件"
                )
        report.append("")

    report_text = '\n'.join(report)

    report_path = report_dir / 'cluster_analysis_report.md'
    with open(report_path, 'w', encoding='utf-8-sig', newline='\n') as f:
        f.write(report_text)

    print(f"  ✓ {report_path}")


def save_results(result_df: pd.DataFrame, base_gdf: gpd.GeoDataFrame, cluster_df: pd.DataFrame,
                 cluster_names: dict, n_clusters: int, out_dir: Path):
    """結果を保存"""
    print_section("7. 結果の保存")

    out_dir.mkdir(parents=True, exist_ok=True)
    report_dir = (out_dir / "reports")
    report_dir.mkdir(parents=True, exist_ok=True)

    # GeoDataFrameにクラスタ情報を追加
    result_gdf = base_gdf.copy()
    result_gdf['cluster'] = result_df['cluster'].values
    result_gdf['cluster_name'] = result_df['cluster_name'].values

    geojson_path = out_dir / 'mesh_with_clusters.geojson'
    csv_path = out_dir / 'mesh_with_clusters.csv'

    print("  GeoJSONを保存中...")
    result_gdf.to_file(geojson_path, driver='GeoJSON', encoding='utf-8')
    print(f"  ✓ {geojson_path}")

    print("  CSVを保存中...")
    result_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"  ✓ {csv_path}")

    print("  レポートを作成中...")
    create_cluster_report(result_df, cluster_df, cluster_names, n_clusters, report_dir)


def run_for_k(base_df: pd.DataFrame, base_gdf: gpd.GeoDataFrame, feature_cols, n_clusters: int):
    """kを固定して一連の処理を実行"""
    df_k, _ = perform_clustering(base_df, feature_cols, n_clusters)
    cluster_df = analyze_clusters(df_k, n_clusters)
    df_k, cluster_names = assign_cluster_names(df_k, cluster_df, n_clusters)

    out_dir = Path(config.OUTPUT_DIR) / f'k{n_clusters:02d}'

    create_visualizations(df_k, cluster_df, cluster_names, n_clusters, out_dir)
    save_results(df_k, base_gdf, cluster_df, cluster_names, n_clusters, out_dir)


def main():
    start_time = time.time()

    k_list = K_LIST

    print("=" * 60)
    print("福岡市・北九州市 クラスタリング分析（追加用途対応版）")
    print(f"対象k: {k_list}")
    print("=" * 60)

    try:
        result_df, result_gdf = load_data()
        result_df, feature_cols = create_features(result_df)

        for k in k_list:
            run_for_k(result_df, result_gdf, feature_cols, k)

        elapsed = time.time() - start_time
        print_section("処理完了")
        print(f"  総処理時間: {elapsed:.1f}秒")
        print("\n✅ すべてのkの処理が完了しました")
        print(f"  結果フォルダ: {config.OUTPUT_DIR} / kXX")

    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
