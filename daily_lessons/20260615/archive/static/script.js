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
    const btnTrain = document.getElementById("btn-train");
    const btnLoader = btnTrain.querySelector(".loader");
    const btnText = btnTrain.querySelector(".btn-text");

    // Metrics elements
    const testRmseEl = document.getElementById("test-rmse");
    const testR2El = document.getElementById("test-r2");
    const trainMetricsEl = document.getElementById("train-metrics");
    const featureTagsEl = document.getElementById("feature-tags");
    const predictedPriceEl = document.getElementById("predicted-price");

    let featuresList = []; // Holds list of available features and bounds
    let currentBenchmarkData = []; // Cached benchmark data for line chart
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
            featuresList = data.features;
            
            // Build prediction sliders in UI
            slidersContainer.innerHTML = "";
            featuresList.forEach(feat => {
                const group = document.createElement("div");
                group.className = "slider-group";
                
                // Format range values nicely
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

            // Update Metrics Cards
            testRmseEl.textContent = data.test_rmse.toFixed(4);
            testR2El.textContent = `${(data.test_r2 * 100).toFixed(2)}%`;
            trainMetricsEl.textContent = `${data.train_rmse.toFixed(4)} / ${(data.train_r2 * 100).toFixed(1)}%`;

            // Display Selected Features tags
            featureTagsEl.innerHTML = "";
            data.selected_features.forEach(feat => {
                const tag = document.createElement("span");
                tag.className = "feature-tag";
                tag.textContent = feat;
                featureTagsEl.appendChild(tag);
            });

            currentBenchmarkData = data.benchmark_data;

            // Plot Visualizations
            plotActualVsPredicted(data.test_actual, data.test_predicted);
            plotFeatureImportance(data.importances);
            plotModelComparison(data.benchmark_data);

            // Trigger real-time prediction using the newly trained parameters
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

    // 3. Debounced predictor callback to prevent API flooding
    let predictTimeout = null;
    function debouncePredict() {
        clearTimeout(predictTimeout);
        predictTimeout = setTimeout(runPrediction, 150);
    }

    async function runPrediction() {
        // Collect current values from all sliders
        const sliderValues = {};
        featuresList.forEach(feat => {
            const slider = document.getElementById(`slider-${feat.name}`);
            if (slider) {
                sliderValues[feat.name] = parseFloat(slider.value);
            }
        });

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
            predictedPriceEl.textContent = data.prediction.toFixed(2);
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
        margin: { t: 40, r: 20, l: 55, b: 40 }
    };

    function plotActualVsPredicted(actual, predicted) {
        const traceScatter = {
            x: actual,
            y: predicted,
            mode: 'markers',
            type: 'scatter',
            name: '預估資料點',
            marker: { color: '#818cf8', size: 7, opacity: 0.7 }
        };

        // Reference 45-degree identity line
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
            title: '預估房價 vs. 實際房價 (Test Set)',
            xaxis: { title: '實際房價 (MEDV)', gridcolor: 'rgba(255,255,255,0.05)' },
            yaxis: { title: '預估房價 (MEDV)', gridcolor: 'rgba(255,255,255,0.05)' },
            showlegend: true,
            legend: { x: 0, y: 1 }
        };

        Plotly.newPlot('plot-scatter', [traceScatter, traceLine], layout, {responsive: true});
    }

    function plotFeatureImportance(importances) {
        if (!importances || importances.length === 0) {
            // Placeholder text in case no importance is calculated
            document.getElementById('plot-importance').innerHTML = 
                `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#6b7280">該演算法不支援此特徵權重圖表</div>`;
            return;
        }

        // Sort descending
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
            title: '特徵權重 / 影響度分析',
            xaxis: { title: '權重指標 / 係數絕對值', gridcolor: 'rgba(255,255,255,0.05)' },
            yaxis: { autorange: 'reversed' }
        };

        Plotly.newPlot('plot-importance', [trace], layout, {responsive: true});
    }

    function plotModelComparison(benchmarkData) {
        const selectors = [...new Set(benchmarkData.map(d => d.Selector))];
        const traces = [];
        
        // Custom color palette to match teacher's plot
        const colors = {
            "Pearson Corr": "#1f77b4",
            "Spearman Corr": "#aec7e8",
            "F-test Reg": "#ff7f0e",
            "Mutual Info": "#ffbb78",
            "RFE": "#2ca02c",
            "Lasso (L1)": "#98df8a",
            "Random Forest": "#d62728",
            "SFS (Forward)": "#ff9896"
        };

        selectors.forEach(sel => {
            const selData = benchmarkData.filter(d => d.Selector === sel);
            selData.sort((a, b) => a['Number of Features'] - b['Number of Features']);
            
            // R2 trace (Left subplot)
            traces.push({
                x: selData.map(d => d['Number of Features']),
                y: selData.map(d => d.R2),
                type: 'scatter',
                mode: 'lines+markers',
                name: sel,
                xaxis: 'x1',
                yaxis: 'y1',
                legendgroup: sel,
                line: { color: colors[sel] || '#888' }
            });
            
            // MSE trace (Right subplot)
            traces.push({
                x: selData.map(d => d['Number of Features']),
                y: selData.map(d => d.MSE),
                type: 'scatter',
                mode: 'lines+markers',
                name: sel,
                xaxis: 'x2',
                yaxis: 'y2',
                legendgroup: sel,
                showlegend: false,
                line: { color: colors[sel] || '#888' }
            });
        });

        const layout = {
            ...commonLayout,
            title: 'Feature Selection Stepwise Evaluation Plot',
            grid: { rows: 1, columns: 2, pattern: 'independent' },
            xaxis1: { title: 'Number of Features in Model', dtick: 1, gridcolor: 'rgba(255,255,255,0.05)' },
            xaxis2: { title: 'Number of Features in Model', dtick: 1, gridcolor: 'rgba(255,255,255,0.05)' },
            yaxis1: { title: 'Test R-squared', gridcolor: 'rgba(255,255,255,0.05)' },
            yaxis2: { title: 'Test Mean Squared Error (MSE)', gridcolor: 'rgba(255,255,255,0.05)' },
            showlegend: true,
            legend: { orientation: 'h', y: 1.15 }
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

    // Force plotly to recalculate layout for newly active charts
    const chartId = document.getElementById(tabId).querySelector(".plotly-chart");
    if (chartId && chartId.classList.contains('js-plotly-plot')) {
        Plotly.Plots.resize(chartId);
    }
}
