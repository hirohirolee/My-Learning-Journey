document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const trainForm = document.getElementById("train-form");
    const algoSelect = document.getElementById("algorithm-select");
    const kFeaturesSelect = document.getElementById("k-features-select");
    const alphaGroup = document.getElementById("alpha-group");
    const depthGroup = document.getElementById("depth-group");
    const testSizeRange = document.getElementById("test-size-range");
    const testSizeVal = document.getElementById("test-size-val");
    const slidersContainer = document.getElementById("sliders-container");
    const oceanProximitySelect = document.getElementById("ocean-proximity-select");
    const btnTrain = document.getElementById("btn-train");
    const btnLoader = btnTrain.querySelector(".loader");
    const btnText = btnTrain.querySelector(".btn-text");

    // Metrics elements
    const testRmseEl = document.getElementById("test-rmse");
    const testR2El = document.getElementById("test-r2");
    const trainMetricsEl = document.getElementById("train-metrics");
    const featureTagsEl = document.getElementById("feature-tags");
    const predictedPriceEl = document.getElementById("predicted-price");

    let numericalFeatures = []; // Holds list of available features and bounds
    let isTraining = false;

    // Toggle hyperparameter UI based on selected algorithm
    algoSelect.addEventListener("change", () => {
        const val = algoSelect.value;
        if (['Ridge', 'Lasso', 'ElasticNet', 'SVR'].includes(val)) {
            alphaGroup.classList.remove("hidden");
            depthGroup.classList.add("hidden");
        } else if (['DecisionTree', 'RandomForest', 'GradientBoosting', 'XGBoost'].includes(val)) {
            alphaGroup.classList.add("hidden");
            depthGroup.classList.remove("hidden");
        } else {
            alphaGroup.classList.add("hidden");
            depthGroup.classList.add("hidden");
        }
    });

    // Update test split size label
    testSizeRange.addEventListener("input", () => {
        testSizeVal.textContent = `${Math.round(testSizeRange.value * 100)}%`;
    });

    // 1. Fetch features metadata and dynamically create predictors
    async function initFeatures() {
        try {
            const res = await fetch("/api/features");
            const data = await res.json();
            numericalFeatures = data.numerical_features;
            
            // Build prediction sliders in UI
            slidersContainer.innerHTML = "";
            numericalFeatures.forEach(feat => {
                const group = document.createElement("div");
                group.className = "slider-group";
                
                const step = feat.step.toFixed(4);
                
                group.innerHTML = `
                    <div class="slider-header">
                        <span class="slider-label">${feat.name}</span>
                        <span class="slider-val" id="val-${feat.name}">${feat.mean.toFixed(2)}</span>
                    </div>
                    <input type="range" id="slider-${feat.name}" name="${feat.name}" 
                           min="${feat.min}" max="${feat.max}" step="${step}" value="${feat.mean}">
                `;
                
                slidersContainer.appendChild(group);

                // Add real-time event listener to update text and run prediction
                const rangeInput = group.querySelector("input[type='range']");
                const labelVal = group.querySelector(`#val-${feat.name}`);
                
                rangeInput.addEventListener("input", () => {
                    labelVal.textContent = parseFloat(rangeInput.value).toFixed(2);
                    debouncePredict();
                });
            });

            // Build Ocean Proximity selection options
            oceanProximitySelect.innerHTML = "";
            const categories = data.categorical_features.categories;
            categories.forEach(cat => {
                const opt = document.createElement("option");
                opt.value = cat;
                opt.textContent = cat;
                oceanProximitySelect.appendChild(opt);
            });

            // Trigger prediction on changing ocean proximity select box
            oceanProximitySelect.addEventListener("change", () => {
                debouncePredict();
            });

            // Initial model training
            trainModel();
            
        } catch (error) {
            console.error("Error loading features:", error);
        }
    }

    // 2. Submit form for training
    trainForm.addEventListener("submit", (e) => {
        e.preventDefault();
        trainModel();
    });

    async function trainModel() {
        if (isTraining) return;
        isTraining = true;

        // UI state: loading
        btnLoader.classList.remove("hidden");
        btnText.textContent = "訓練中...";
        btnTrain.disabled = true;

        const payload = {
            algorithm: algoSelect.value,
            k_features: parseInt(kFeaturesSelect.value),
            test_size: parseFloat(testSizeRange.value),
            alpha: parseFloat(document.getElementById("alpha-input").value),
            max_depth: document.getElementById("depth-select").value
        };

        try {
            const res = await fetch("/api/train", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await res.json();

            // Update Metrics Cards (formatted as localized currency since it's USD)
            testRmseEl.textContent = `$${Math.round(data.test_rmse).toLocaleString()}`;
            testR2El.textContent = `${(data.test_r2 * 100).toFixed(2)}%`;
            trainMetricsEl.textContent = `$${Math.round(data.train_rmse).toLocaleString()} / ${(data.train_r2 * 100).toFixed(1)}%`;

            // Display Selected Features tags
            featureTagsEl.innerHTML = "";
            data.selected_features.forEach(feat => {
                const tag = document.createElement("span");
                tag.className = "feature-tag";
                tag.textContent = feat;
                featureTagsEl.appendChild(tag);
            });

            // Plot Visualizations
            plotActualVsPredicted(data.test_actual, data.test_predicted);
            plotFeatureImportance(data.importances);
            plotModelComparison(data.benchmark_data);

            // Trigger prediction with new model
            runPrediction();

        } catch (err) {
            console.error("Error training model:", err);
            alert("模型訓練失敗，請檢查參數！");
        } finally {
            // Restore UI
            btnLoader.classList.add("hidden");
            btnText.textContent = "訓練模型與評估";
            btnTrain.disabled = false;
            isTraining = false;
        }
    }

    // 3. Debounced predictor callback
    let predictTimeout = null;
    function debouncePredict() {
        clearTimeout(predictTimeout);
        predictTimeout = setTimeout(runPrediction, 150);
    }

    async function runPrediction() {
        const sliderValues = {};
        numericalFeatures.forEach(feat => {
            const slider = document.getElementById(`slider-${feat.name}`);
            if (slider) {
                sliderValues[feat.name] = parseFloat(slider.value);
            }
        });

        // Add selected ocean proximity value
        sliderValues['ocean_proximity'] = oceanProximitySelect.value;

        const payload = {
            inputs: sliderValues,
            algorithm: algoSelect.value,
            k_features: parseInt(kFeaturesSelect.value),
            alpha: parseFloat(document.getElementById("alpha-input").value),
            max_depth: document.getElementById("depth-select").value
        };

        try {
            const res = await fetch("/api/predict", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            predictedPriceEl.textContent = Math.round(data.prediction).toLocaleString();
        } catch (err) {
            console.error("Prediction failed:", err);
        }
    }

    /* -------------------------------------------------
       PLOTLY CHARTS RENDERING
    ------------------------------------------------- */
    const commonLayout = {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#9ca3af', family: 'Inter, sans-serif' },
        margin: { t: 40, r: 20, l: 65, b: 40 }
    };

    function plotActualVsPredicted(actual, predicted) {
        const traceScatter = {
            x: actual,
            y: predicted,
            mode: 'markers',
            type: 'scatter',
            name: '預估房屋點',
            marker: { color: '#818cf8', size: 6, opacity: 0.6 }
        };

        const minVal = Math.min(...actual, ...predicted);
        const maxVal = Math.max(...actual, ...predicted);
        const traceLine = {
            x: [minVal, maxVal],
            y: [minVal, maxVal],
            mode: 'lines',
            type: 'scatter',
            name: '完美契合 (y=x)',
            line: { color: '#10b981', width: 2, dash: 'dash' }
        };

        const layout = {
            ...commonLayout,
            title: '預估房屋價值 vs. 實際房屋價值 (Test Subset)',
            xaxis: { title: '實際房價 (USD)', gridcolor: 'rgba(255,255,255,0.05)' },
            yaxis: { title: '預估房價 (USD)', gridcolor: 'rgba(255,255,255,0.05)' },
            showlegend: true,
            legend: { x: 0, y: 1 }
        };

        Plotly.newPlot('plot-scatter', [traceScatter, traceLine], layout, {responsive: true});
    }

    function plotFeatureImportance(importances) {
        if (!importances || importances.length === 0) {
            document.getElementById('plot-importance').innerHTML = 
                `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#6b7280">該演算法不支援此特徵權重圖表</div>`;
            return;
        }

        const names = importances.map(item => item.name);
        const values = importances.map(item => item.importance);

        const trace = {
            x: values,
            y: names,
            type: 'bar',
            orientation: 'h',
            marker: {
                color: '#a855f7',
                width: 0.6
            }
        };

        const layout = {
            ...commonLayout,
            title: '特徵影響權重分析',
            xaxis: { title: '權重指標 / 係數絕對值', gridcolor: 'rgba(255,255,255,0.05)' },
            yaxis: { autorange: 'reversed' }
        };

        Plotly.newPlot('plot-importance', [trace], layout, {responsive: true});
    }

    function plotModelComparison(benchmarkData) {
        const algorithms = [...new Set(benchmarkData.map(d => d.Algorithm))];
        const traces = algorithms.map(algo => {
            const algoData = benchmarkData.filter(d => d.Algorithm === algo);
            algoData.sort((a, b) => a['Number of Features'] - b['Number of Features']);
            
            return {
                x: algoData.map(d => d['Number of Features']),
                y: algoData.map(d => d.MSE),
                type: 'scatter',
                mode: 'lines+markers',
                name: algo
            };
        });

        const layout = {
            ...commonLayout,
            title: '演算法 MSE vs. 特徵數量 (3-Fold CV Log-Scale Sampled)',
            xaxis: { 
                title: '特徵選取數量', 
                dtick: 1,
                gridcolor: 'rgba(255,255,255,0.05)'
            },
            yaxis: { 
                title: '交叉驗證平均 MSE (對數刻度)', 
                type: 'log',
                gridcolor: 'rgba(255,255,255,0.05)'
            },
            showlegend: true
        };

        Plotly.newPlot('plot-comparison', traces, layout, {responsive: true});
    }

    // Window size resizing handler
    window.addEventListener("resize", () => {
        const plots = ['plot-scatter', 'plot-importance', 'plot-comparison'];
        plots.forEach(id => {
            const el = document.getElementById(id);
            if (el && el.classList.contains('js-plotly-plot')) {
                Plotly.Plots.resize(el);
            }
        });
    });

    // Start everything
    initFeatures();
});

// Tab switcher functionality
function switchTab(evt, tabId) {
    const tabPanes = document.querySelectorAll(".tab-pane");
    const tabButtons = document.querySelectorAll(".tab-btn");

    tabPanes.forEach(pane => pane.classList.remove("active-pane"));
    tabButtons.forEach(btn => btn.classList.remove("active"));

    document.getElementById(tabId).classList.add("active-pane");
    evt.currentTarget.classList.add("active");

    const chartId = document.getElementById(tabId).querySelector(".plotly-chart");
    if (chartId && chartId.classList.contains('js-plotly-plot')) {
        Plotly.Plots.resize(chartId);
    }
}
