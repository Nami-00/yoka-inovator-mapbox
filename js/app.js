// Mapbox アクセストークン（必ず自分のトークンに置き換えてください）
mapboxgl.accessToken = 'pk.eyJ1IjoibmFtaTAwIiwiYSI6ImNtazR4OGdiczBjajMzZnExbmc4OTZtZWcifQ.ezFfwXNOK8Ve9I7kz5AMIw';

let map;
let currentClusterCount = 6;
let currentDisplayMode = 'cluster';
let meshData = null;
let clusterConfig = null;
let visibleClusters = new Set();

document.addEventListener('DOMContentLoaded', () => {
    initMap();
    setupControls();
});

function initMap() {
    map = new mapboxgl.Map({
        container: 'map',
        style: 'mapbox://styles/mapbox/light-v11',
        center: [130.4017, 33.5904],
        zoom: 10,
        pitch: 0,
        bearing: 0
    });

    map.addControl(new mapboxgl.NavigationControl(), 'top-right');

    map.on('load', () => {
        console.log('地図読み込み完了');
        loadClusterData(currentClusterCount);
    });
}

function setupControls() {
    // クラスター数変更
    document.getElementById('cluster-count').addEventListener('change', (e) => {
        currentClusterCount = parseInt(e.target.value);
        
        // 既存レイヤーを削除
        if (map.getLayer('mesh-fill')) map.removeLayer('mesh-fill');
        if (map.getLayer('mesh-outline')) map.removeLayer('mesh-outline');
        if (map.getSource('mesh-data')) map.removeSource('mesh-data');
        
        loadClusterData(currentClusterCount);
    });

    // 表示モード変更
    document.getElementById('display-mode').addEventListener('change', (e) => {
        currentDisplayMode = e.target.value;
        updateMapStyle();
    });

    // 透明度変更
    document.getElementById('opacity-slider').addEventListener('input', (e) => {
        const opacity = parseInt(e.target.value) / 100;
        document.getElementById('opacity-value').textContent = `${e.target.value}%`;
        
        if (map.getLayer('mesh-fill')) {
            map.setPaintProperty('mesh-fill', 'fill-opacity', opacity);
        }
    });

    // リセットボタン
    document.getElementById('reset-view').addEventListener('click', () => {
        map.flyTo({
            center: [130.4017, 33.5904],
            zoom: 10,
            pitch: 0,
            bearing: 0,
            duration: 1500
        });
        
        if (clusterConfig) {
            visibleClusters = new Set(clusterConfig.clusters.map(c => c.id));
            updateClusterFilters();
            updateMapStyle();
        }
    });
}

async function loadClusterData(k) {
    try {
        console.log(`データ読み込み中 k=${k}...`);
        
        const [geojsonResponse, configResponse] = await Promise.all([
            fetch(`web_data/mesh_clusters_k${k}.geojson`),
            fetch(`web_data/cluster_config_k${k}.json`)
        ]);

        meshData = await geojsonResponse.json();
        clusterConfig = await configResponse.json();

        console.log(`データ読み込み完了: ${meshData.features.length} メッシュ`);
        
        visibleClusters = new Set(clusterConfig.clusters.map(c => c.id));
        
        // 地図が準備できるまで待機
        if (map.isStyleLoaded()) {
            updateMap();
            updateUI();
        } else {
            map.once('idle', () => {
                updateMap();
                updateUI();
            });
        }
    } catch (error) {
        console.error('データ読み込みエラー:', error);
        alert('データの読み込みに失敗しました。');
    }
}

function updateMap() {
    // 地図が準備できていない場合は待機
    if (!map.isStyleLoaded()) {
        console.log('地図スタイル読み込み待機中...');
        map.once('idle', updateMap);
        return;
    }

    // データが準備できていない場合は何もしない
    if (!meshData) {
        console.log('データがまだ読み込まれていません');
        return;
    }

    // 既存レイヤーとソースを削除
    if (map.getLayer('mesh-fill')) map.removeLayer('mesh-fill');
    if (map.getLayer('mesh-outline')) map.removeLayer('mesh-outline');
    if (map.getSource('mesh-data')) map.removeSource('mesh-data');

    map.addSource('mesh-data', {
        type: 'geojson',
        data: meshData
    });

    updateMapStyle();
    
    // イベントリスナーは一度だけ登録
    if (!map._clusterEventListenersAdded) {
        map.on('click', 'mesh-fill', (e) => {
            const properties = e.features[0].properties;
            showPopup(e.lngLat, properties);
        });

        map.on('mouseenter', 'mesh-fill', () => {
            map.getCanvas().style.cursor = 'pointer';
        });
        
        map.on('mouseleave', 'mesh-fill', () => {
            map.getCanvas().style.cursor = '';
        });
        
        map._clusterEventListenersAdded = true;
    }
}

function updateMapStyle() {
    if (!map.getSource('mesh-data')) return;

    const opacity = parseInt(document.getElementById('opacity-slider').value) / 100;
    
    // フィルター条件（cluster列を参照）
    const filter = ['in', ['get', 'cluster'], ['literal', Array.from(visibleClusters)]];
    
    let fillColor;
    
    if (currentDisplayMode === 'cluster') {
        // クラスター別カラー（cluster列を参照）
        const colorExpression = ['match', ['get', 'cluster']];
        clusterConfig.clusters.forEach(cluster => {
            colorExpression.push(cluster.id, cluster.color);
        });
        colorExpression.push('#cccccc');
        fillColor = colorExpression;
        
    } else if (currentDisplayMode === 'density') {
        // 飲食店密度のヒートマップ
        fillColor = [
            'interpolate',
            ['linear'],
            ['get', '飲食店数'],
            0, '#ffffcc',
            10, '#ffeda0',
            20, '#fed976',
            30, '#feb24c',
            50, '#fd8d3c',
            100, '#fc4e2a',
            200, '#e31a1c',
            500, '#bd0026'
        ];
        
    } else if (currentDisplayMode === 'buildings') {
        // 建物総数のグラデーション
        fillColor = [
            'interpolate',
            ['linear'],
            ['get', '建物総数'],
            0, '#f0f9e8',
            50, '#ccebc5',
            100, '#a8ddb5',
            200, '#7bccc4',
            500, '#4eb3d3',
            1000, '#2b8cbe',
            2000, '#08589e'
        ];
    }

    // レイヤーを削除して再追加
    if (map.getLayer('mesh-fill')) map.removeLayer('mesh-fill');
    if (map.getLayer('mesh-outline')) map.removeLayer('mesh-outline');

    map.addLayer({
        id: 'mesh-fill',
        type: 'fill',
        source: 'mesh-data',
        paint: {
            'fill-color': fillColor,
            'fill-opacity': opacity
        },
        filter: filter
    });

    map.addLayer({
        id: 'mesh-outline',
        type: 'line',
        source: 'mesh-data',
        paint: {
            'line-color': '#888',
            'line-width': 0.5,
            'line-opacity': 0.5
        },
        filter: filter
    });
}

function updateUI() {
    updateClusterFilters();
    updateStats();
    updateLegend();
}

function updateClusterFilters() {
    const container = document.getElementById('cluster-filters');
    container.innerHTML = '';

    clusterConfig.clusters.forEach(cluster => {
        const item = document.createElement('div');
        item.className = 'cluster-filter-item';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = `cluster-${cluster.id}`;
        checkbox.checked = visibleClusters.has(cluster.id);
        checkbox.addEventListener('change', (e) => {
            if (e.target.checked) {
                visibleClusters.add(cluster.id);
            } else {
                visibleClusters.delete(cluster.id);
            }
            updateMapStyle();
            updateStats();
        });

        const colorBox = document.createElement('div');
        colorBox.className = 'cluster-color-box';
        colorBox.style.backgroundColor = cluster.color;

        const label = document.createElement('label');
        label.htmlFor = `cluster-${cluster.id}`;
        label.textContent = `${cluster.name} (${cluster.count}件)`;
        label.style.cursor = 'pointer';

        item.appendChild(checkbox);
        item.appendChild(colorBox);
        item.appendChild(label);
        container.appendChild(item);
    });
}

function updateStats() {
    const content = document.getElementById('stats-content');
    
    const totalMeshes = clusterConfig.total_meshes;
    const visibleMeshes = clusterConfig.clusters
        .filter(c => visibleClusters.has(c.id))
        .reduce((sum, c) => sum + c.count, 0);
    
    const avgBuildings = visibleMeshes > 0 ? (clusterConfig.clusters
        .filter(c => visibleClusters.has(c.id))
        .reduce((sum, c) => sum + c.avg_buildings * c.count, 0) / visibleMeshes).toFixed(1) : 0;
    
    const avgRestaurants = visibleMeshes > 0 ? (clusterConfig.clusters
        .filter(c => visibleClusters.has(c.id))
        .reduce((sum, c) => sum + c.avg_restaurants * c.count, 0) / visibleMeshes).toFixed(1) : 0;

    content.innerHTML = `
        <div class="popup-info">
            <span class="popup-label">総メッシュ数:</span>
            <span class="popup-value">${totalMeshes.toLocaleString()}</span>
            
            <span class="popup-label">表示中:</span>
            <span class="popup-value">${visibleMeshes.toLocaleString()} (${(visibleMeshes/totalMeshes*100).toFixed(1)}%)</span>
            
            <span class="popup-label">平均建物数:</span>
            <span class="popup-value">${avgBuildings}</span>
            
            <span class="popup-label">平均飲食店数:</span>
            <span class="popup-value">${avgRestaurants}</span>
        </div>
    `;
}

function updateLegend() {
    const content = document.getElementById('legend-content');
    
    if (currentDisplayMode === 'cluster') {
        content.innerHTML = clusterConfig.clusters.map(cluster => `
            <div class="legend-item">
                <div class="legend-color" style="background-color: ${cluster.color}"></div>
                <span>${cluster.name}</span>
            </div>
        `).join('');
        
    } else if (currentDisplayMode === 'density') {
        content.innerHTML = `
            <div class="legend-item">
                <div class="legend-color" style="background: linear-gradient(to right, #ffffcc, #bd0026)"></div>
                <span>飲食店密度 (低 → 高)</span>
            </div>
        `;
        
    } else if (currentDisplayMode === 'buildings') {
        content.innerHTML = `
            <div class="legend-item">
                <div class="legend-color" style="background: linear-gradient(to right, #f0f9e8, #08589e)"></div>
                <span>建物総数 (少 → 多)</span>
            </div>
        `;
    }
}

function showPopup(lngLat, properties) {
    const cluster = clusterConfig.clusters.find(c => c.id === properties['cluster']);
    
    const html = `
        <h4>メッシュ情報</h4>
        <div class="popup-info">
            <span class="popup-label">クラスター:</span>
            <span class="popup-value" style="color: ${cluster.color}; font-weight: bold;">
                ${cluster.name}
            </span>
            
            <span class="popup-label">建物総数:</span>
            <span class="popup-value">${parseInt(properties['建物総数']).toLocaleString()}</span>
            
            <span class="popup-label">飲食店数:</span>
            <span class="popup-value">${parseInt(properties['飲食店数']).toLocaleString()}</span>
            
            <span class="popup-label">住宅:</span>
            <span class="popup-value">${parseInt(properties['建物_住宅'] || 0).toLocaleString()}</span>
            
            <span class="popup-label">商業施設:</span>
            <span class="popup-value">${parseInt(properties['建物_商業施設'] || 0).toLocaleString()}</span>
        </div>
    `;
    
    new mapboxgl.Popup()
        .setLngLat(lngLat)
        .setHTML(html)
        .addTo(map);
}