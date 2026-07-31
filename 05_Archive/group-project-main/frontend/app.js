window.PRE_INJECTED_DATA = null;
const API_BASE = window.API_BASE || (
    window.location.protocol === 'file:' ? 'http://127.0.0.1:8000' : window.location.origin
);
const API_BASE_CANDIDATES = [...new Set([
    API_BASE,
    'http://127.0.0.1:8001',
    'http://localhost:8001',
    'http://127.0.0.1:8000',
    'http://localhost:8000'
])];
const DASHBOARD_SELECT_FIELDS = [
    'master_review_id', 'business_id', 'business_name', 'platform', 'posts_id', 'post_published_at',
    'post_title', 'post_author_id', 'post_author_name', 'comment_author_id', 'comment_author_name',
    'comment_content', 'comment_published_at', 'sentiment_label', 'sentiment_score', 'risk_score',
    'risk_level', 'emotion_joy', 'emotion_anger', 'emotion_disappointment', 'reviews_tag',
    'analyzed_at', 'is_meaningful', 'content_type', 'content_quality_score', 'filter_reason',
    'reviews_response', 'status', 'created_at', 'updated_at'
].join(',');
const DEFAULT_BUSINESS_FILTER = '文章牛肉湯';
const INITIAL_DATA_LIMIT = 0;
const buildDashboardApiPath = (businessName, options = {}) => {
    const params = new URLSearchParams({
        table: 'master_reviews_result',
        select: DASHBOARD_SELECT_FIELDS,
        order: 'comment_published_at.desc.nullslast'
    });
    const limit = Number(options.limit || 0);
    if (limit > 0) params.set('limit', String(limit));
    if (businessName) params.set('business_name', businessName);
    return `/api/supabase-query?${params.toString()}`;
};
const API_PATH = buildDashboardApiPath(DEFAULT_BUSINESS_FILTER, { limit: INITIAL_DATA_LIMIT });
const API_URL = `${API_BASE}${API_PATH}`;

// ── ⚙️ 小組討論功能控制鍵 ──
const ENABLE_GOTO_SOURCE_BUTTON = true;

const App = {
    data: [],
    filteredData: [],
    currentListRows: [],
    listRenderLimit: 200,
    listRenderStep: 200,
    dataLoadToken: 0,
    isLoadingAllData: false,
    businessOptions: [],
    businessOptionsPromise: null,
    defaultBusinessFilter: DEFAULT_BUSINESS_FILTER,
    businessDefaultApplied: false,
    loadedAllBusinesses: false,
    activeRange: 'all',
    activeListFilter: null,
    activeTrendFilter: null,
    currentWorkspaceView: 'overview',
    listFilterState: {
        overview: { platform: ['all'], content: ['all'], risk: ['all'], activeListFilter: null },
        crisis: { platform: ['all'], content: ['all'], risk: ['all'], activeListFilter: null }
    },
    currentActiveId: null,
    chart: null,
    platformChart: null,
    radarChart: null,
    historyChartInstance: null,
    aiProvider: { provider: 'gemini', endpoint: '', model: 'gemini-3.6-flash', apiKey: '', configured: false, models: [] },
    aiProviderModels: {
        ollama: ['qwen2.5:3b', 'qwen2.5:7b', 'llama3.1:8b', 'llama3.2:3b', 'gemma2:2b', 'mistral:7b'],
        gemini: ['gemini-3.6-flash', 'gemini-3.5-flash-lite', 'gemini-3.5-flash', 'gemini-flash-latest'],
        huggingface: ['meta-llama/Llama-3.1-8B-Instruct', 'mistralai/Mistral-7B-Instruct-v0.3', 'Qwen/Qwen2.5-7B-Instruct', 'google/gemma-2-2b-it']
    },
    keywordSeeds: ['牛肉湯', '牛肉', '湯頭', '肉質', '好吃', '難吃', '服務', '態度', '店員', '等待', '排隊', '出餐', '衛生', '環境', '座位', '停車', '價格', '貴', 'CP', '食安', '異物', '蒼蠅', '蟲', '中毒', '拉肚子', '檢舉', '提告', '消保', '退款', '補償', '冷掉', '份量'],
    keywordPatterns: null,
    flagMeta: {
        food_safety: { label: '食安風險', field: 'flag_food_safety', cls: 'bg-red-50 text-red-700 border-red-200' },
        legal_risk: { label: '法務風險', field: 'flag_legal_risk', cls: 'bg-purple-50 text-purple-700 border-purple-200' },
        hygiene_risk: { label: '衛生風險', field: 'flag_hygiene_risk', cls: 'bg-amber-50 text-amber-700 border-amber-200' }
    },
    tagMeta: {
        food: { label: '餐點 (Food)', cls: 'bg-yellow-50 border-yellow-200 text-yellow-800', icon: '🍜' },
        service: { label: '服務 (Service)', cls: 'bg-blue-50 border-blue-200 text-blue-800', icon: '🙋' },
        environment: { label: '環境 (Environment)', cls: 'bg-green-50 border-green-200 text-green-800', icon: '🏠' },
        price: { label: '價格 (Price)', cls: 'bg-pink-50 border-pink-200 text-pink-800', icon: '💰' },
        other: { label: '其他 (Other)', cls: 'bg-slate-50 border-slate-200 text-slate-700', icon: '🏷️' }
    },
    contentTypeMeta: {
        meaningful_review: { label: '實質評論', cls: 'bg-success-50 text-success-600 border-success-100' },
        meaningless: { label: '無意義留言', cls: 'bg-slate-100 text-slate-500 border-slate-200' },
        spam_or_noise: { label: '垃圾/灌水', cls: 'bg-warning-50 text-warning-600 border-warning-100' },
        non_customer_comment: { label: '非消費體驗', cls: 'bg-purple-50 text-purple-700 border-purple-100' },
        news_discussion: { label: '新聞討論', cls: 'bg-blue-50 text-blue-700 border-blue-100' },
        unknown: { label: '未分類', cls: 'bg-slate-50 text-slate-500 border-slate-200' }
    },

    async init() {
        this.showInitialLoading();
        this.setupBrowserClasses();
        this.setFilterValues();
        this.setupResponsiveHandlers();
        this.setupMultiSelectClose();
        this.setupMobileBusinessPicker();
        this.registerServiceWorker();
        try {
            await this.loadBusinessOptions();
            await this.loadData();
            this.setDateRange('all');
        } catch (error) {
            console.error('[dashboard] initial load failed', error);
            this.showEmptyState(`資料讀取失敗：${error.message}`);
        } finally {
            this.hideInitialLoading();
        }
    },

    showInitialLoading() {
        document.getElementById('app-loading')?.classList.remove('hidden');
    },

    hideInitialLoading() {
        document.getElementById('app-loading')?.classList.add('hidden');
    },

    setupBrowserClasses() {
        const ua = navigator.userAgent || '';
        const isMobile = /Android|iPhone|iPad|iPod/i.test(ua);
        const isChrome = /Chrome|CriOS/i.test(ua) && !/Edg|OPR|SamsungBrowser/i.test(ua);
        document.body.classList.toggle('chrome-mobile', isMobile && isChrome);
    },

    registerServiceWorker() {
        if (!('serviceWorker' in navigator) || window.location.protocol === 'file:') return;
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('./sw.js').catch(error => {
                console.warn('[pwa] service worker registration failed', error);
            });
        });
    },

    setupResponsiveHandlers() {
        const compactQuery = window.matchMedia('(max-width: 1023px)');
        const closeOnCompact = event => {
            if (event.matches) {
                this.closeDetailPanel(false);
            } else if (!document.getElementById('view-trends')?.classList.contains('hidden')) {
                this.closeDetailPanel(false);
            } else if (this.currentActiveId || this.filteredData.length > 0) {
                const targetId = this.currentActiveId || this.filteredData[0]?.id;
                if (targetId) this.selectIncident(targetId);
            }
        };
        closeOnCompact(compactQuery);
        if (compactQuery.addEventListener) {
            compactQuery.addEventListener('change', closeOnCompact);
        } else if (compactQuery.addListener) {
            compactQuery.addListener(closeOnCompact);
        }
    },

    setFilterValues() {
        const filter = document.getElementById('risk-filter');
        if (filter) {
            if (filter.options[0]) filter.options[0].value = 'all';
            if (filter.options[1]) filter.options[1].value = 'high';
            if (filter.options[2]) filter.options[2].value = 'medium';
            this.setSelectValues('risk-filter', ['all']);
        }
        this.syncMultiSelectControls([
            'platform-filter', 'content-filter', 'risk-filter',
            'trend-platform-filter', 'trend-content-filter', 'trend-risk-filter', 'trend-sentiment-filter'
        ]);
    },

    getSelectValues(id) {
        const el = document.getElementById(id);
        if (!el) return ['all'];
        const values = [...el.selectedOptions].map(option => option.value).filter(Boolean);
        if (values.length > 1 && values.includes('all')) return values.filter(value => value !== 'all');
        return values.length ? values : ['all'];
    },

    setSelectValues(id, values = ['all']) {
        const el = document.getElementById(id);
        if (!el) return;
        const wanted = new Set((Array.isArray(values) ? values : [values]).filter(Boolean));
        if (!wanted.size) wanted.add('all');
        [...el.options].forEach(option => { option.selected = wanted.has(option.value); });
        if (![...el.selectedOptions].length && el.options[0]) el.options[0].selected = true;
        this.updateMultiSelectUi(id);
    },

    isAllSelection(values) {
        return !values?.length || values.includes('all');
    },

    matchesSelection(value, selected) {
        return this.isAllSelection(selected) || selected.includes(value);
    },

    setupMultiSelectClose() {
        document.addEventListener('click', event => {
            if (event.target.closest('.multi-select')) return;
            document.querySelectorAll('.multi-select-menu').forEach(menu => {
                menu.classList.add('hidden');
                menu.closest('.multi-select')?.classList.remove('multi-select-open');
            });
        });
    },

    setupMobileBusinessPicker() {
        const picker = document.getElementById('mobile-business-picker');
        const trigger = document.getElementById('mobile-business-trigger');
        const menu = document.getElementById('mobile-business-menu');
        if (!picker || !trigger || !menu) return;
        trigger.addEventListener('click', async event => {
            event.stopPropagation();
            if (window.matchMedia('(max-width: 767px)').matches && menu.parentElement !== document.body) {
                document.body.appendChild(menu);
            }
            if (!this.businessOptions.length) {
                await (this.businessOptionsPromise || this.loadBusinessOptions());
            }
            this.renderMobileBusinessMenu(document.getElementById('mobile-business-filter')?.value || 'all');
            menu.classList.toggle('hidden');
            if (!menu.classList.contains('hidden')) this.positionMobileBusinessMenu();
            picker.classList.toggle('mobile-business-open', !menu.classList.contains('hidden'));
            document.body.classList.toggle('mobile-business-menu-open', !menu.classList.contains('hidden'));
            trigger.setAttribute('aria-expanded', String(!menu.classList.contains('hidden')));
        });
        window.addEventListener('resize', () => {
            if (!menu.classList.contains('hidden')) this.positionMobileBusinessMenu();
        });
        menu.addEventListener('scroll', event => event.stopPropagation(), { passive: true });
        const closeOnScroll = event => {
            if (event.target?.closest?.('#mobile-business-menu')) return;
            this.closeMobileBusinessMenu();
        };
        const closeOnPageMove = event => {
            if (menu.classList.contains('hidden')) return;
            if (event.type === 'pointermove' && event.pointerType === 'mouse') return;
            if (event.target?.closest?.('#mobile-business-menu')) return;
            this.closeMobileBusinessMenu();
        };
        window.addEventListener('scroll', closeOnScroll, true);
        window.addEventListener('wheel', closeOnPageMove, { passive: true, capture: true });
        window.addEventListener('pointermove', closeOnPageMove, { passive: true, capture: true });
        window.addEventListener('touchstart', closeOnPageMove, { passive: true, capture: true });
        window.addEventListener('touchmove', closeOnPageMove, { passive: true, capture: true });
        document.querySelectorAll('.overview-pane, #incident-scroll-area, #view-trends, #detail-content-area').forEach(element => {
            element.addEventListener('scroll', closeOnScroll, { passive: true });
            element.addEventListener('wheel', closeOnPageMove, { passive: true });
            element.addEventListener('pointermove', closeOnPageMove, { passive: true });
            element.addEventListener('touchstart', closeOnPageMove, { passive: true });
            element.addEventListener('touchmove', closeOnPageMove, { passive: true });
        });
        document.addEventListener('click', event => {
            if (event.target.closest('#mobile-business-picker') || event.target.closest('#mobile-business-menu')) return;
            this.closeMobileBusinessMenu();
        });
    },

    closeMobileBusinessMenu() {
        const picker = document.getElementById('mobile-business-picker');
        const menu = document.getElementById('mobile-business-menu');
        if (!menu) return;
        menu.classList.add('hidden');
        menu.removeAttribute('style');
        picker?.classList.remove('mobile-business-open');
        document.body.classList.remove('mobile-business-menu-open');
        document.getElementById('mobile-business-trigger')?.setAttribute('aria-expanded', 'false');
    },

    positionMobileBusinessMenu() {
        const trigger = document.getElementById('mobile-business-trigger');
        const menu = document.getElementById('mobile-business-menu');
        if (!trigger || !menu) return;
        const rect = trigger.getBoundingClientRect();
        const gutter = 12;
        const isMobile = window.matchMedia('(max-width: 767px)').matches;
        if (isMobile) {
            menu.removeAttribute('style');
            return;
        }
        const menuWidth = isMobile ? window.innerWidth - gutter * 2 : Math.min(288, window.innerWidth - gutter * 2);
        const left = isMobile
            ? gutter
            : Math.max(gutter, Math.min(rect.right - menuWidth, window.innerWidth - gutter - menuWidth));
        if (menu.parentElement === document.body) {
            menu.style.top = `${Math.ceil(rect.bottom + 8 + window.scrollY)}px`;
            menu.style.left = `${Math.ceil(left)}px`;
            menu.style.right = 'auto';
        } else {
            menu.style.top = '';
            menu.style.left = '';
            menu.style.right = '';
        }
        menu.style.width = `${Math.ceil(menuWidth)}px`;
    },

    async loadBusinessOptions() {
        if (this.businessOptionsPromise) return this.businessOptionsPromise;
        this.businessOptionsPromise = (async () => {
        try {
            const { payload } = await this.fetchJsonWithFallback('/api/businesses', {}, 12000);
            if (!Array.isArray(payload)) return;
            this.businessOptions = payload
                .map(item => ({
                    name: item.business_name || item.businessName || '',
                    count: Number(item.count || 0)
                }))
                .filter(item => item.name);
            this.updateListFilterOptions(this.filteredData);
        } catch (error) {
            console.warn('[dashboard] business options load failed', error);
        }
        })();
        return this.businessOptionsPromise;
    },

    syncMultiSelectControls(ids = []) {
        ids.forEach(id => this.renderMultiSelect(id));
    },

    renderMultiSelect(id) {
        const source = document.getElementById(id);
        if (!source) return;
        let wrapper = source.nextElementSibling;
        if (!wrapper || !wrapper.classList.contains('multi-select')) {
            wrapper = document.createElement('div');
            /* Topic 4: 加入 flex-auto 讓手機版篩選器可彈性折行延展 */
            wrapper.className = 'multi-select w-[48%] md:w-auto flex-auto md:flex-none';
            source.insertAdjacentElement('afterend', wrapper);
        }
        const selected = this.getSelectValues(id);
        const defaultLabel = source.dataset.label || source.options[0]?.textContent || '全部';
        const selectedLabels = selected
            .filter(value => value !== 'all')
            .map(value => source.querySelector(`option[value="${CSS.escape(value)}"]`)?.textContent || value);
        const buttonLabel = selectedLabels.length
            ? (selectedLabels.length === 1 ? selectedLabels[0] : `已選 ${selectedLabels.length} 項`)
            : defaultLabel;
        const options = [...source.options].map(option => {
            const checked = selected.includes(option.value);
            return `<label class="multi-select-option">
                <input type="checkbox" value="${this.escapeHtml(option.value)}" ${checked ? 'checked' : ''}>
                <span>${this.escapeHtml(option.textContent)}</span>
            </label>`;
        }).join('');
        wrapper.innerHTML = `
            <button type="button" class="multi-select-trigger" aria-haspopup="listbox" aria-expanded="false">
                <span class="truncate">${this.escapeHtml(buttonLabel)}</span>
                <i class="ph-bold ph-caret-down text-[11px] text-slate-400"></i>
            </button>
            <div class="multi-select-menu hidden">${options}</div>
        `;
        const trigger = wrapper.querySelector('.multi-select-trigger');
        const menu = wrapper.querySelector('.multi-select-menu');
        trigger.addEventListener('click', event => {
            event.stopPropagation();
            document.querySelectorAll('.multi-select-menu').forEach(other => {
                if (other !== menu) {
                    other.classList.add('hidden');
                    other.closest('.multi-select')?.classList.remove('multi-select-open');
                }
            });
            menu.classList.toggle('hidden');
            wrapper.classList.toggle('multi-select-open', !menu.classList.contains('hidden'));
            trigger.setAttribute('aria-expanded', String(!menu.classList.contains('hidden')));
        });
        menu.querySelectorAll('input[type="checkbox"]').forEach(input => {
            input.addEventListener('click', event => event.stopPropagation());
            input.addEventListener('change', () => {
                let values = [...menu.querySelectorAll('input[type="checkbox"]:checked')].map(item => item.value);
                if (input.value === 'all' && input.checked) values = ['all'];
                if (input.value !== 'all' && input.checked) values = values.filter(value => value !== 'all');
                if (!values.length) values = ['all'];
                this.setSelectValues(id, values);
                source.dispatchEvent(new Event('change', { bubbles: true }));
            });
        });
    },

    updateMultiSelectUi(id) {
        const source = document.getElementById(id);
        const wrapper = source?.nextElementSibling;
        if (!source || !wrapper?.classList.contains('multi-select')) return;
        const selected = this.getSelectValues(id);
        const defaultLabel = source.dataset.label || source.options[0]?.textContent || '全部';
        const selectedLabels = selected
            .filter(value => value !== 'all')
            .map(value => source.querySelector(`option[value="${CSS.escape(value)}"]`)?.textContent || value);
        const label = selectedLabels.length
            ? (selectedLabels.length === 1 ? selectedLabels[0] : `已選 ${selectedLabels.length} 項`)
            : defaultLabel;
        const text = wrapper.querySelector('.multi-select-trigger span');
        if (text) text.textContent = label;
        wrapper.querySelectorAll('input[type="checkbox"]').forEach(input => {
            input.checked = selected.includes(input.value);
        });
    },

    renderMobileBusinessMenu(selectedValue = 'all', entries = null) {
        const menu = document.getElementById('mobile-business-menu');
        const label = document.getElementById('mobile-business-label');
        const picker = document.getElementById('mobile-business-picker');
        if (!menu || !label) return;
        const sourceEntries = Array.isArray(entries) && entries.length
            ? entries
            : this.businessOptions.map(item => ({ name: item.name, count: item.count }));
        const options = [
            { name: '全部品牌', value: 'all', count: null },
            ...sourceEntries.map(item => ({ name: item.name, value: item.name, count: item.count }))
        ];
        const selected = options.find(option => option.value === selectedValue) || options[0];
        label.textContent = selected.name;
        menu.innerHTML = options.map(option => {
            const active = option.value === selected.value;
            const countText = option.count === null ? '' : `<span class="text-[10px] text-slate-400">${Number(option.count || 0).toLocaleString()}</span>`;
            return `<button type="button" class="mobile-business-option ${active ? 'active' : ''}" data-value="${this.escapeHtml(option.value)}">
                <span class="truncate">${this.escapeHtml(option.name)}</span>${countText}
            </button>`;
        }).join('');
        menu.querySelectorAll('.mobile-business-option').forEach(button => {
            button.addEventListener('click', event => {
                event.stopPropagation();
                const value = button.dataset.value || 'all';
                this.closeMobileBusinessMenu();
                this.applyBusinessFilter(value);
            });
        });
    },

    async loadData(options = {}) {
        const {
            path = API_PATH,
            fullPath = null,
            lazy = false,
            loadedAllBusinesses = false
        } = options;
        const timeoutMs = Number(options.timeoutMs || 30000);
        const token = ++this.dataLoadToken;
        try {
            const hasInjectedData = Array.isArray(window.PRE_INJECTED_DATA);
            const source = hasInjectedData ? window.PRE_INJECTED_DATA : await this.fetchRows(path, timeoutMs);
            if (token !== this.dataLoadToken) return;
            this.data = this.adaptRows(source).sort((a, b) => (b.date?.getTime() || 0) - (a.date?.getTime() || 0));
            if (hasInjectedData) {
                this.loadedAllBusinesses = true;
            } else {
                this.loadedAllBusinesses = loadedAllBusinesses;
            }
            if (lazy && !hasInjectedData && fullPath) {
                this.loadRemainingData(fullPath, token, loadedAllBusinesses);
            }
        } catch (error) {
            console.error('[dashboard] failed to load data', error);
            this.data = [];
            this.filteredData = [];
            this.showEmptyState(`資料讀取失敗：${error.message}`);
        }
    },

    async loadRemainingData(fullPath, token, loadedAllBusinesses = false) {
        this.isLoadingAllData = true;
        try {
            const source = await this.fetchRows(fullPath, 30000);
            if (token !== this.dataLoadToken) return;
            const rows = this.adaptRows(source).sort((a, b) => (b.date?.getTime() || 0) - (a.date?.getTime() || 0));
            if (rows.length < this.data.length) return;
            this.data = rows;
            this.loadedAllBusinesses = loadedAllBusinesses;
            this.setDateRange(this.activeRange || 'all');
            this.updateListFilterOptions(this.filteredData);
            this.filterList();
            this.updateLastUpdatedLabel();
            if (source.length > INITIAL_DATA_LIMIT) this.showToast(`完整資料已載入：${source.length.toLocaleString()} 筆`);
        } catch (error) {
            console.warn('[dashboard] deferred full data load failed', error);
            this.showToast(`完整資料背景載入失敗：${error.message}`);
        } finally {
            if (token === this.dataLoadToken) this.isLoadingAllData = false;
        }
    },

    async refreshData() {
        await this.loadData();
        this.setDateRange(this.activeRange || 'all');
        this.updateLastUpdatedLabel();
        this.showToast('資料已重新整理');
    },

    async syncNewData() {
        const button = document.getElementById('sync-new-data-btn');
        const modeSelect = document.getElementById('sync-mode');
        const syncMode = modeSelect?.value === 'all' ? 'all' : 'new';
        const isFullSync = syncMode === 'all';
        if (isFullSync && !confirm('全部更新會先清空所有分析結果，再依 master_reviews 的現有資料重新分析。此操作可能需要較久時間，確定要執行嗎？')) {
            return;
        }
        const originalHtml = button?.innerHTML;
        if (button) {
            button.disabled = true;
            button.innerHTML = '<i class="ph-bold ph-spinner-gap animate-spin text-base"></i><span>同步中...</span>';
        }
        if (modeSelect) modeSelect.disabled = true;
        try {
            const { payload } = await this.fetchJsonWithFallback(`/api/ml-dashboard/sync?dry_run=false&force=${isFullSync}`, {
                method: 'POST'
            });
            const job = payload?.job;
            if (!job?.id) throw new Error('後端未回傳同步任務 ID');
            if (payload?.already_running) {
                this.showToast('已有同步任務執行中，正在接續顯示進度');
            }
            const completedJob = await this.waitForSyncJob(job.id, button);
            const result = completedJob?.summary || {};
            const completedFullSync = Boolean(completedJob?.force);
            await this.loadData();
            this.setDateRange(this.activeRange || 'all');
            this.updateLastUpdatedLabel();

            const updated = Number(result.updated || 0);
            const skipped = Number(result.skipped_existing || 0);
            const failed = Number(result.failed || 0);
            const cleared = Number(result.cleared_rows || 0);
            const message = failed > 0
                ? `${completedFullSync ? '全部更新' : '同步新增'}完成：更新 ${updated} 筆，失敗 ${failed} 筆`
                : (completedFullSync ? `全部更新完成：清除 ${cleared} 筆，重建 ${updated} 筆` : `同步新增完成：新增 ${updated} 筆，已存在 ${skipped} 筆`);
            this.showToast(message);
        } catch (error) {
            alert(`同步失敗：${error.message}`);
        } finally {
            if (button) {
                button.disabled = false;
                button.innerHTML = originalHtml;
            }
            if (modeSelect) modeSelect.disabled = false;
        }
    },

    async waitForSyncJob(jobId, button) {
        const phaseLabels = {
            queued: '排隊中',
            fetching_source: '讀取來源',
            fetching_existing: '比對現有資料',
            preparing: '準備資料',
            analyzing: '分析中',
            clearing_results: '清除舊結果',
            writing_results: '寫入結果'
        };
        while (true) {
            const { payload } = await this.fetchJsonWithFallback(
                `/api/ml-dashboard/sync/status?job_id=${encodeURIComponent(jobId)}`
            );
            const job = payload?.job;
            if (!job) throw new Error('無法取得同步任務狀態');
            if (job.status === 'completed') return job;
            if (job.status === 'failed') throw new Error(job.error || '背景同步失敗');

            const phase = phaseLabels[job.phase] || '同步中';
            const processed = Number(job.processed || 0);
            const total = Number(job.total || 0);
            const progress = total > 0 ? ` ${processed}/${total}` : '';
            if (button) {
                button.innerHTML = `<i class="ph-bold ph-spinner-gap animate-spin text-base"></i><span>${phase}${progress}</span>`;
            }
            await new Promise(resolve => setTimeout(resolve, 2000));
        }
    },

    updateLastUpdatedLabel() {
        const label = document.getElementById('last-updated-label');
        if (!label) return;
        label.textContent = new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' });
    },

    showToast(message) {
        const toast = document.getElementById('toast');
        if (!toast) return;
        const text = toast.querySelector('p');
        if (text) text.textContent = message;
        toast.classList.remove('translate-y-20', 'opacity-0');
        clearTimeout(this.toastTimer);
        this.toastTimer = setTimeout(() => toast.classList.add('translate-y-20', 'opacity-0'), 3000);
    },

    async fetchRows(path = API_PATH, timeoutMs = 8000) {
        const urls = this.getApiUrls(path);
        let lastError = null;
        for (const url of urls) {
            let timer = null;
            try {
                const controller = new AbortController();
                timer = setTimeout(() => controller.abort(), timeoutMs);
                const response = await fetch(url, { headers: { Accept: 'application/json' }, signal: controller.signal });
                const payload = await response.json();
                if (!response.ok || payload?.error) throw new Error(payload?.error || `HTTP ${response.status}`);
                return Array.isArray(payload) ? payload : [];
            } catch (error) {
                lastError = error;
            } finally {
                if (timer) clearTimeout(timer);
            }
        }
        throw lastError || new Error('無法連線到資料 API');
    },

    getApiUrls(path) {
        const isLocalPage = ['file:', 'http:'].includes(window.location.protocol)
            && ['localhost', '127.0.0.1', ''].includes(window.location.hostname);
        if (!isLocalPage) return [`${API_BASE}${path}`];
        return [...new Set([`${API_BASE}${path}`, ...API_BASE_CANDIDATES.map(base => `${base}${path}`)])];
    },

    async fetchJsonWithFallback(path, options = {}, timeoutMs = 8000) {
        let lastError = null;
        for (const url of this.getApiUrls(path)) {
            let timer = null;
            try {
                const controller = new AbortController();
                if (timeoutMs !== null) { timer = setTimeout(() => controller.abort('request_timeout'), timeoutMs); }
                const response = await fetch(url, { ...options, headers: { Accept: 'application/json', ...(options.headers || {}) }, signal: controller.signal });
                const text = await response.text();
                let payload = null;
                try { payload = text ? JSON.parse(text) : null; } catch (parseError) {
                    if (!response.ok) throw new Error(`HTTP ${response.status}: ${text || response.statusText}`);
                    throw parseError;
                }
                if (!response.ok || payload?.error || payload?.detail) {
                    throw new Error(payload?.error || payload?.detail || `HTTP ${response.status}`);
                }
                return { response, payload, text, url };
            } catch (error) {
                if (error.name === 'AbortError' || error.message?.includes('signal is aborted')) {
                    lastError = new Error('後端回應逾時，請稍後確認同步是否已在背景完成。');
                } else {
                    lastError = error;
                }
            } finally {
                if (timer) clearTimeout(timer);
            }
        }
        throw lastError || new Error('無法連線到後端 API');
    },

    normalizeSentiment(value) {
        const normalized = String(value || '').trim().toLowerCase();
        if (['positive', 'pos', '正面'].includes(normalized)) return 'positive';
        if (['negative', 'neg', '負面'].includes(normalized)) return 'negative';
        return 'neutral';
    },

    adaptRows(rows) {
        return rows.map((row, index) => {
            const risk = String(row.risk_level || '').toLowerCase();
            const levelMap = {
                critical: { label: '緊急風險', cls: 'bg-danger-50 text-danger-600 border-danger-200' },
                high: { label: '高風險', cls: 'bg-danger-50 text-danger-600 border-danger-200' },
                medium: { label: '中風險', cls: 'bg-warning-50 text-warning-600 border-warning-200' },
                low: { label: '低風險', cls: 'bg-slate-100 text-slate-500 border-slate-200' }
            };
            const dateValue = row.comment_published_at || row.post_published_at || row.review_time || row.analyzed_at || row.created_at || null;
            const date = this.parseDate(dateValue);
            const platform = row.platform || 'Unknown';
            const text = row.comment_content || row.raw_text || row.review || row.content || '尚無評論內容';
            const tag = row.reviews_tag || this.inferTag(text);
            const contentType = row.content_type || 'unknown';
            const flags = this.resolveRiskFlags(row, text);
            const sentiment = this.normalizeSentiment(row.sentiment_label || row.sentiment);
            const item = {
                id: String(row.review_id || row.master_review_id || row.id || `ROW-${index + 1}`),
                masterReviewId: row.master_review_id || row.review_id || row.id || null,
                businessName: row.businessName || row.business_name || row.busninessNAME || row.store_name || '',
                contentType,
                isMeaningful: row.is_meaningful !== false,
                contentQualityScore: Number(row.content_quality_score ?? 0),
                filterReason: row.filter_reason || '',
                platform,
                ...this.platformIcon(platform),
                level: levelMap[risk]?.label || '低風險',
                levelKey: levelMap[risk] ? risk : 'low',
                levelClass: levelMap[risk]?.cls || levelMap.low.cls,
                text,
                time: this.formatReviewTime(dateValue),
                reviewDate: dateValue,
                date,
                status: row.status || (row.reviews_response ? 'resolved' : 'pending'),
                stars: (row.rating !== null && row.rating !== undefined && Number(row.rating) > 0)
                    ? Number(row.rating)
                    : (sentiment === 'positive' ? 5 : (sentiment === 'negative' ? 1 : 3)),
                riskScore: Number(row.risk_score || row.risk_percent || 0),
                sentiment,
                tag,
                flags,
                emotionJoy: Number(row.emotion_joy || 0),
                emotionAnger: Number(row.emotion_anger || 0),
                emotionDisappointment: Number(row.emotion_disappointment || 0),
                raw: row,
                ai: null
            };
            item.ai = row.report_content ? this.parseAiReport(row.report_content) : this.localAiFallback(item, 'professional');
            return item;
        });
    },

    resolveRiskFlags(row, text) {
        const source = `${text || ''} ${row.post_title || ''} ${row.filter_reason || ''}`;
        const hasAny = words => words.some(word => source.includes(word));
        return {
            food_safety: Boolean(row.flag_food_safety) || hasAny(['食安', '食物中毒', '中毒', '拉肚子', '腹瀉', '上吐下瀉', '異物', '蟲', '蒼蠅', '蟑螂', '發霉', '臭酸', '過期', '沒熟']),
            legal_risk: Boolean(row.flag_legal_risk) || hasAny(['檢舉', '提告', '告你', '法院', '法務', '消保', '消基會', '衛生局', '投訴', '客訴', '申訴', '求償', '賠償', '退費', '退款', '違法', '罰款']),
            hygiene_risk: Boolean(row.flag_hygiene_risk) || hasAny(['衛生', '髒', '很髒', '不乾淨', '油垢', '黏黏', '臭味', '發臭', '廁所', '桌子髒', '地板髒', '蟲', '蒼蠅', '蟑螂', '老鼠'])
        };
    },

    parseDate(value) {
        if (!value) return null;
        const date = new Date(value);
        return Number.isNaN(date.getTime()) ? null : date;
    },

    platformIcon(platform) {
        const name = String(platform).toLowerCase();
        if (name.includes('google')) return { iconClass: 'plat-google', iconContent: '<img src="https://www.google.com/images/branding/googleg/1x/googleg_standard_color_128dp.png" class="w-3.5 h-3.5 object-contain" alt="Google Maps">' };
        if (name.includes('thread')) return { iconClass: 'plat-threads', iconContent: '<svg viewBox="0 0 24 24" class="w-3.5 h-3.5" aria-label="Threads" role="img"><path fill="currentColor" d="M12.186 24h-.007c-3.581-.024-6.334-1.205-8.184-3.509C2.35 18.44 1.5 15.586 1.472 12.01v-.017c.03-3.579.879-6.43 2.525-8.482C5.845 1.205 8.6.024 12.18 0h.014c2.746.02 5.043.725 6.826 2.098 1.677 1.29 2.858 3.13 3.509 5.467l-2.04.569c-1.104-3.96-3.898-5.984-8.304-6.015-2.91.022-5.11.936-6.54 2.717-1.335 1.664-2.024 4.079-2.046 7.18.022 3.1.71 5.515 2.046 7.18 1.43 1.783 3.631 2.698 6.54 2.717 2.623-.02 4.358-.631 5.8-2.045 1.647-1.613 1.618-3.593 1.08-4.798-.31-.693-.85-1.27-1.542-1.684-.173 1.242-.56 2.246-1.163 3.019-.811 1.04-1.977 1.613-3.464 1.703-1.124.068-2.21-.205-3.058-.768-1.004-.667-1.6-1.702-1.633-2.84-.065-2.235 1.753-3.834 4.52-3.978.987-.052 1.913-.009 2.753.127-.111-.665-.338-1.197-.681-1.589-.47-.536-1.2-.81-2.164-.816h-.036c-.777 0-1.833.215-2.478 1.232l-1.786-.956c.875-1.547 2.451-2.397 4.281-2.368 3.089.02 4.882 1.964 5.066 5.463.077.03.153.062.228.095 1.43.63 2.542 1.687 3.13 2.975.813 1.779.892 4.545-1.476 6.866C17.297 23.077 15.03 23.976 12.186 24Zm1.003-9.88c-.2 0-.403.005-.608.016-1.577.083-2.516.813-2.484 1.936.034 1.164 1.313 1.824 2.55 1.754 1.898-.114 2.9-1.304 3.033-3.595-.774-.07-1.608-.111-2.491-.111Z"/></svg>' };
        if (name.includes('dcard')) return { iconClass: 'plat-dcard', iconContent: '<span class="text-[10px] font-black">D</span>' };
        if (name.includes('ptt')) return { iconClass: 'bg-[#001b44] text-white', iconContent: '<span class="text-[9px] font-black tracking-tight">PTT</span>' };
        if (name.includes('instagram') || name.includes('ig')) return { iconClass: 'bg-pink-500 text-white', iconContent: '<img src="https://custom.simpleicons.org/instagram/white" class="w-3.5 h-3.5 object-contain" alt="Instagram">' };
        if (name.includes('facebook') || name === 'fb') return { iconClass: 'bg-blue-600 text-white', iconContent: '<img src="https://custom.simpleicons.org/facebook/white" class="w-3.5 h-3.5 object-contain" alt="Facebook">' };
        if (name.includes('tripadvisor')) return { iconClass: 'bg-green-600 text-white', iconContent: '<img src="https://custom.simpleicons.org/tripadvisor/white" class="w-3.5 h-3.5 object-contain" alt="Tripadvisor">' };
        return { iconClass: 'bg-slate-200 text-slate-600', iconContent: '<i class="ph ph-chat-circle-text text-xs"></i>' };
    },

    formatReviewTime(value) {
        const date = this.parseDate(value);
        if (!date) return value ? String(value) : '--';
        return date.toLocaleString('zh-TW', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false });
    },

    getAnchorDate() {
        const dates = this.data.map(item => item.date).filter(Boolean);
        if (!dates.length) return new Date();
        return new Date(Math.max(...dates.map(date => date.getTime())));
    },

    setDateRange(days) {
        this.activeRange = String(days || 7);
        document.querySelectorAll('.date-range-btn').forEach(btn => {
            const active = btn.dataset.range === this.activeRange;
            btn.classList.toggle('bg-white', active);
            btn.classList.toggle('text-slate-800', active);
            btn.classList.toggle('shadow-sm', active);
            btn.classList.toggle('text-slate-600', !active);
        });
        this.applyDateFilter();
    },

    applyDateFilter() {
        if (this.activeRange === 'all') {
            this.filteredData = [...this.data];
            this.renderTrends();
            this.updateListFilterOptions(this.filteredData);
            this.filterList();
            return;
        }
        const anchor = this.getAnchorDate();
        const from = new Date(anchor);
        const days = Number(this.activeRange) || 7;
        from.setDate(from.getDate() - days);
        this.filteredData = this.data.filter(item => !item.date || item.date >= from && item.date <= anchor);
        if (this.data.length > 0 && this.filteredData.length === 0) {
            this.filteredData = [...this.data];
            this.activeRange = 'all';
            document.querySelectorAll('.date-range-btn').forEach(btn => {
                const active = btn.dataset.range === 'all';
                btn.classList.toggle('bg-white', active);
                btn.classList.toggle('text-slate-800', active);
                btn.classList.toggle('shadow-sm', active);
                btn.classList.toggle('text-slate-600', !active);
            });
        }
        this.renderTrends();
        this.updateListFilterOptions(this.filteredData);
        this.filterList();
        if (this.currentActiveId && !this.filteredData.some(item => item.id === this.currentActiveId)) {
            this.currentActiveId = null;
        }
    },

    updateListFilterOptions(rows = this.filteredData) {
        const businessFilter = document.getElementById('business-filter');
        const mobileBusinessFilter = document.getElementById('mobile-business-filter');
        const platformFilter = document.getElementById('platform-filter');
        const contentFilter = document.getElementById('content-filter');
        const trendPlatformFilter = document.getElementById('trend-platform-filter');
        const trendContentFilter = document.getElementById('trend-content-filter');
        
        const currentBusiness = businessFilter?.value || mobileBusinessFilter?.value || 'all';
        const currentPlatform = this.getSelectValues('platform-filter');
        const currentContent = this.getSelectValues('content-filter');
        const currentTrendPlatform = this.getSelectValues('trend-platform-filter');
        const currentTrendContent = this.getSelectValues('trend-content-filter');
        
        const businessCounts = {};
        const counts = {};
        const contentCounts = {};
        rows.forEach(item => {
            const business = item.businessName || '未命名品牌';
            businessCounts[business] = (businessCounts[business] || 0) + 1;
            const platform = item.platform || 'Unknown';
            counts[platform] = (counts[platform] || 0) + 1;
            const type = item.contentType || 'unknown';
            contentCounts[type] = (contentCounts[type] || 0) + 1;
        });

        // 確保雙邊選單都有連動更新。品牌清單優先使用後端完整清單，避免 lazy loading 初始資料只顯示單一品牌。
        if (businessFilter || mobileBusinessFilter) {
            const businessEntries = (this.businessOptions.length
                ? this.businessOptions.map(item => ({ name: item.name, count: item.count }))
                : Object.entries(businessCounts).map(([name, count]) => ({ name, count })))
                .filter(entry => entry.name)
                .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name));
            const businessNames = new Set(businessEntries.map(entry => entry.name));
            const options = businessEntries
                .map(entry => {
                    return `<option value="${this.escapeHtml(entry.name)}">${this.escapeHtml(entry.name)}</option>`;
                })
                .join('');
            
            const html = `<option value="all">全部品牌</option>${options}`;
            if (businessFilter) businessFilter.innerHTML = html;
            if (mobileBusinessFilter) mobileBusinessFilter.innerHTML = html;
            
            let nextBusiness = businessNames.has(currentBusiness) ? currentBusiness : 'all';
            if (!this.businessDefaultApplied && businessNames.has(this.defaultBusinessFilter)) {
                nextBusiness = this.defaultBusinessFilter;
                this.businessDefaultApplied = true;
            }
            if(businessFilter) businessFilter.value = nextBusiness;
            if(mobileBusinessFilter) mobileBusinessFilter.value = nextBusiness;
            this.renderMobileBusinessMenu(nextBusiness, businessEntries);
        }

        if (platformFilter) {
            const options = Object.entries(counts)
                .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
                .map(([platform]) => `<option value="${this.escapeHtml(platform)}">${this.escapeHtml(platform)}</option>`)
                .join('');
            platformFilter.innerHTML = `<option value="all">所有平台</option>${options}`;
            this.setSelectValues('platform-filter', currentPlatform.filter(value => value === 'all' || counts[value]));
        }
        if (trendPlatformFilter) {
            const options = Object.entries(counts)
                .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
                .map(([platform]) => `<option value="${this.escapeHtml(platform)}">${this.escapeHtml(platform)}</option>`)
                .join('');
            trendPlatformFilter.innerHTML = `<option value="all">所有平台</option>${options}`;
            this.setSelectValues('trend-platform-filter', currentTrendPlatform.filter(value => value === 'all' || counts[value]));
        }
        if (contentFilter) {
            const orderedTypes = ['meaningless', 'spam_or_noise', 'non_customer_comment', 'news_discussion', 'meaningful_review', 'unknown'];
            const options = orderedTypes
                .filter(type => contentCounts[type])
                .map(type => {
                    const label = this.contentTypeMeta[type]?.label || type;
                    return `<option value="${this.escapeHtml(type)}">${this.escapeHtml(label)}</option>`;
                })
                .join('');
            contentFilter.innerHTML = `<option value="all">所有內容類型</option>${options}`;
            this.setSelectValues('content-filter', currentContent.filter(value => value === 'all' || contentCounts[value]));
        }
        if (trendContentFilter) {
            const orderedTypes = ['meaningless', 'spam_or_noise', 'non_customer_comment', 'news_discussion', 'meaningful_review', 'unknown'];
            const options = orderedTypes
                .filter(type => contentCounts[type])
                .map(type => {
                    const label = this.contentTypeMeta[type]?.label || type;
                    return `<option value="${this.escapeHtml(type)}">${this.escapeHtml(label)}</option>`;
                })
                .join('');
            trendContentFilter.innerHTML = `<option value="all">所有內容類型</option>${options}`;
            this.setSelectValues('trend-content-filter', currentTrendContent.filter(value => value === 'all' || contentCounts[value]));
        }
        this.syncMultiSelectControls([
            'platform-filter', 'content-filter', 'risk-filter',
            'trend-platform-filter', 'trend-content-filter', 'trend-risk-filter', 'trend-sentiment-filter'
        ]);
    },

    parseAiReport(markdown) {
        const empty = { painpoint: '尚未生成 AI 報告，請先執行分析流程。', advice: '目前沒有可用的行動建議。', sop: '尚未觸發 SOP', draft: '尚無回覆草稿可複製。' };
        if (!markdown || !String(markdown).trim()) return empty;
        const text = String(markdown).replace(/\[SCORE_START\][\s\S]*?\[SCORE_END\]/g, '').trim();
        const clean = value => (value || '').replace(/核心痛点/g, '核心痛點').replace(/行动建议/g, '行動建議').replace(/回复草稿/g, '回覆草稿').replace(/公开回复/g, '公開回覆').replace(/^\s{0,3}>\s?/gm, '').replace(/^\s*[-*]\s?/gm, '').replace(/\*\*/g, '').replace(/#{1,6}\s*/g, '').trim();
        const sectionBoundaries = [
            '核心痛點', '核心痛点', '痛點', '痛点', '危機評估', '危机评估', '滿意度分析', '满意度分析',
            '行動建議', '行动建议', '建議', '建议', '觸發\\s*SOP', '触发\\s*SOP', 'SOP',
            '回覆草稿', '回复草稿', '公開回覆草稿', '公开回复草稿', '公開回覆', '公开回复', '店家回覆', '商家回覆', '店家回應', '商家回應',
            '公開致謝與推薦回覆', '公开致謝與推薦回复', '致謝回覆', '致谢回复', '回覆', '回复', '回應', '回应'
        ].join('|');
        const section = labels => {
            for (const label of labels) {
                const escaped = label.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                const re = new RegExp(`(?:^|\\n)\\s*(?:#{1,6}\\s*)?(?:\\d+[.、)]\\s*)?[^\\n]*${escaped}[^\\n]*[:：]?\\s*\\n?([\\s\\S]*?)(?=\\n\\s*(?:#{1,6}\\s*)?(?:\\d+[.、)]\\s*)?[^\\n]*(?:${sectionBoundaries})|$)`, 'iu');
                const match = text.match(re);
                if (match && clean(match[1])) return clean(match[1]);
            }
            return '';
        };
        const lineContaining = labels => text.split(/\n+/).map(clean).filter(Boolean).find(line => labels.some(label => line.includes(label))) || '';
        const fallbackDraft = () => {
            const cleaned = clean(text);
            if (!cleaned) return '';
            const index = cleaned.search(/(?:回覆草稿|回复草稿|公開回覆|公开回复|店家回覆|商家回覆|店家回應|商家回應|致謝回覆|致谢回复|回覆|回复|回應|回应|致謝|致谢)/i);
            if (index !== -1) {
                let candidateBlock = cleaned.substring(index);
                const nextHeaderIndex = candidateBlock.search(/(?:\n\s*(?:#{1,6}\\s*)?(?:\d+[\.\s、)]\\s*)?[^\n]*(?:私訊|私信|法務|法务|內部應對|內部對策|對策|SOP|\[SCORE_START\]))/i);
                if (nextHeaderIndex !== -1) {
                    candidateBlock = candidateBlock.substring(0, nextHeaderIndex);
                }
                const linesAfter = candidateBlock.split('\n');
                linesAfter.shift();
                const result = linesAfter.join('\n').trim();
                if (result) return result;
            }
            const lines = cleaned.split(/\n+/).map(line => line.trim()).filter(Boolean);
            const candidate = lines.filter(line => !/^(核心痛點|行動建議|觸發\s*SOP|SOP|回覆草稿|危機評估|滿意度分析|法務與內部應對策略)[:：]?$/i.test(line)).join('\n');
            return candidate || cleaned;
        };
        return {
            painpoint: section(['核心痛點', '核心痛点', '危機評估', '危机评估', '滿意度分析', '满意度分析']) || lineContaining(['核心關鍵字', '核心关键字', '危機等級', '危机等级']) || empty.painpoint,
            advice: section(['行動建議', '行动建议', '法務與內部應對策略', '法务与内部应对策略', '內部應對策略', '内部应对策略']) || empty.advice,
            sop: section(['觸發 SOP', '触发 SOP', 'SOP']) || lineContaining(['SOP']) || this.inferSop(text),
            draft: section([
                '回覆草稿', '回复草稿', '公開回覆草稿', '公开回复草稿', '公開致謝與推薦回覆', '公开致謝與推薦回覆',
                '公開回覆', '公开回复', '店家回覆', '商家回覆', '店家回應', '商家回應', '致謝回覆', '致谢回复', '回覆', '回复', '回應', '回应'
            ]) || fallbackDraft() || empty.draft
        };
    },

    inferSop(text) {
        if (/食安|衛生|異物|中毒|蒼蠅|蟲/.test(text)) return 'SOP-003: 食安與衛生事件處理';
        if (/服務|態度|等候|等待/.test(text)) return 'SOP-008: 服務體驗客訴處理';
        if (/價格|收費|退款|補償/.test(text)) return 'SOP-005: 價格與補償爭議處理';
        return 'SOP-001: 一般評論回覆流程';
    },

    inferTag(text) {
        if (/服務|態度|等待|店員|排隊|出餐/.test(text)) return 'service';
        if (/環境|衛生|髒|廁所|座位|停車/.test(text)) return 'environment';
        if (/價格|貴|便宜|CP|收費|退款/.test(text)) return 'price';
        return 'food';
    },

    localAiFallback(item, toneType = 'professional', reason = '') {
        const flags = item.flags || {};
        const topics = [];
        if (flags.food_safety) topics.push('食安疑慮');
        if (flags.hygiene_risk) topics.push('環境/衛生疑慮');
        if (flags.legal_risk) topics.push('潛在法務風險');
        if (!topics.length && ['critical', 'high'].includes(item.levelKey)) topics.push('高風險負評');
        if (!topics.length) topics.push(this.tagMeta[item.tag]?.label || '一般顧客體驗');

        const painpoint = `${topics.join('、')}；評論重點：${item.text.slice(0, 80)}${item.text.length > 80 ? '...' : ''}`;
        const advice = flags.legal_risk
            ? '先保留紀錄與現場佐證，回覆時避免承認未查證責任，並邀請顧客私訊提供消費資訊以便查核。'
            : flags.food_safety || flags.hygiene_risk
                ? '立即啟動店內衛生查核，確認當班流程、環境清潔與食材狀況，公開回覆中先承接感受並說明會完成內部改善。'
                : '先感謝顧客具體回饋，針對體驗落差提出可執行改善，並邀請再次聯繫補充細節。';
        const customerResponse = flags.legal_risk
            ? '我們會非常重視您的反饋，目前已著手進行內部調查與程序檢視。'
            : flags.food_safety || flags.hygiene_risk
                ? '我們非常重視食品衛生與環境清潔，已安排相關人員進行全面的衛生查核與流程改善。'
                : '我們會針對您提到的體驗落差進行檢討與改進。';
        const sop = flags.food_safety
            ? 'SOP-003: 食安與衛生事件處理'
            : flags.legal_risk
                ? 'SOP-006: 法務與消保風險回應'
                : flags.hygiene_risk
                    ? 'SOP-004: 環境衛生查核'
                    : 'SOP-001: 一般評論回覆流程';
        const opening = toneType === 'apologetic'
            ? '您好，非常抱歉讓您有這次不舒服的體驗。'
            : '您好，感謝您提供這次具體回饋。';
        const draft = `${opening}我們已將您的意見記錄下來，並會依照內部流程檢視相關環節。${customerResponse}若您方便，也歡迎私訊提供用餐日期、時段與更多細節，讓我們能更精準地追查並改善。再次謝謝您的提醒。`;
        return {
            painpoint,
            advice: reason ? `${advice}（目前模型服務未連線，先提供本地規則建議。）` : advice,
            sop,
            draft
        };
    },

    renderDashboard(rows = this.getListFilteredRows()) {
        const pendingRisk = rows.filter(item => item.status !== 'resolved' && ['critical', 'high'].includes(item.levelKey)).length;
        const rated = rows.filter(item => item.stars > 0);
        const avgRating = rated.length ? (rated.reduce((sum, item) => sum + item.stars, 0) / rated.length).toFixed(1) : '0.0';
        
        // 更新桌機與手機的徽章數字
        this.setText('urgent-badge', pendingRisk);
        this.setText('mobile-urgent-badge', pendingRisk);
        
        this.setText('kpi-urgent', pendingRisk);
        this.setText('kpi-total', rows.length.toLocaleString());
        const rating = document.getElementById('kpi-rating');
        if (rating) rating.innerHTML = `${avgRating}<span class="text-sm font-medium text-slate-400">/5</span>`;
        this.renderHotKeywords(rows);
        this.renderQuickFilterState();
    },

    getListFilteredRows() {
        const riskValues = this.getSelectValues('risk-filter');
        const platformValues = this.getSelectValues('platform-filter');
        const contentValues = this.getSelectValues('content-filter');
        let rows = this.getBusinessFilteredRows();
        if (!this.isAllSelection(platformValues)) rows = rows.filter(item => platformValues.includes(item.platform));
        if (!this.isAllSelection(contentValues)) rows = rows.filter(item => contentValues.includes(item.contentType));
        if (!this.isAllSelection(riskValues)) {
            rows = rows.filter(item => {
                if (riskValues.includes(item.levelKey)) return true;
                if (riskValues.includes('high') && ['critical', 'high'].includes(item.levelKey)) return true;
                if (riskValues.includes('medium') && ['critical', 'high', 'medium'].includes(item.levelKey)) return true;
                return false;
            });
        }
        if (this.activeListFilter?.type === 'urgent') {
            rows = rows.filter(item => item.status !== 'resolved' && ['critical', 'high'].includes(item.levelKey));
        }
        if (this.activeListFilter?.type === 'keyword') {
            rows = rows.filter(item => (item.text || '').includes(this.activeListFilter.value));
        }
        if (this.activeListFilter?.type === 'flag') {
            rows = rows.filter(item => item.flags?.[this.activeListFilter.value]);
        }
        return rows;
    },

    getBusinessFilteredRows() {
        const dSelect = document.getElementById('business-filter')?.value || 'all';
        const mSelect = document.getElementById('mobile-business-filter')?.value || 'all';
        // 因為事件觸發可能會導致兩者短暫不同步，我們以剛被改動或非預設的為主
        const businessValue = (dSelect !== 'all') ? dSelect : mSelect;
        
        let rows = [...this.filteredData];
        if (businessValue !== 'all') {
            rows = rows.filter(item => (item.businessName || '未命名品牌') === businessValue);
        }
        return rows;
    },

    async applyBusinessFilter(val) {
        const businessValue = val || document.getElementById('business-filter')?.value || 'all';
        
        // 同步雙邊選單數值
        const dSelect = document.getElementById('business-filter');
        const mSelect = document.getElementById('mobile-business-filter');
        if(dSelect && dSelect.value !== businessValue) dSelect.value = businessValue;
        if(mSelect && mSelect.value !== businessValue) mSelect.value = businessValue;
        this.renderMobileBusinessMenu(businessValue);

        if (businessValue !== 'all' && !Array.isArray(window.PRE_INJECTED_DATA)) {
            const hasBusinessRows = this.data.some(item => (item.businessName || '未命名品牌') === businessValue);
            if (!hasBusinessRows) {
                try {
                    await this.loadData({
                        path: buildDashboardApiPath(businessValue),
                        lazy: false,
                        loadedAllBusinesses: false
                    });
                    this.filteredData = [...this.data];
                    this.businessDefaultApplied = true;
                    this.updateListFilterOptions(this.filteredData);
                    if (dSelect) dSelect.value = businessValue;
                    if (mSelect) mSelect.value = businessValue;
                    this.renderMobileBusinessMenu(businessValue);
                } catch (error) {
                    this.showToast(`品牌資料載入失敗：${error.message}`);
                }
            }
        }
        
        if (businessValue === 'all' && !this.loadedAllBusinesses) {
            if (Array.isArray(window.PRE_INJECTED_DATA)) {
                this.loadedAllBusinesses = true;
                this.businessDefaultApplied = true;
            } else {
            try {
                await this.loadData({
                    path: buildDashboardApiPath(''),
                    lazy: false,
                    loadedAllBusinesses: true
                });
                this.filteredData = [...this.data];
                this.businessDefaultApplied = true;
                this.updateListFilterOptions(this.filteredData);
                
                if (dSelect) dSelect.value = 'all';
                if (mSelect) mSelect.value = 'all';
            } catch (error) {
                this.showToast(`全部品牌載入失敗：${error.message}`);
            }
            }
        }
        this.renderTrends();
        this.filterList();
    },

    renderHotKeywords(rows) {
        const el = document.getElementById('hot-keywords');
        if (!el) return;
        const keywords = this.topKeywords(rows).slice(0, 4);
        const keywordHtml = keywords.length
            ? keywords.map(([kw, count]) => {
                const active = this.activeListFilter?.type === 'keyword' && this.activeListFilter.value === kw;
                return `<button type="button" data-keyword="${this.escapeHtml(kw)}" class="keyword-filter-btn keyword-tag hot ${active ? 'ring-2 ring-danger-300' : ''}">${this.escapeHtml(kw)} <span class="opacity-60 text-[10px]">${count}</span></button>`;
            }).join('')
            : '<span class="text-xs text-slate-400">暫無痛點</span>';
        const flagHtml = Object.entries(this.flagMeta).map(([key, meta]) => {
            const count = rows.filter(item => item.flags?.[key]).length;
            const active = this.activeListFilter?.type === 'flag' && this.activeListFilter.value === key;
            return `<button type="button" onclick="App.toggleFlagFilter('${key}')" class="inline-flex items-center gap-1 px-2 py-1 rounded border text-[11px] font-bold ${meta.cls} ${active ? 'ring-2 ring-primary-300' : ''}">${meta.label}<span class="bg-white/60 px-1 rounded">${count}</span></button>`;
        }).join('');
        el.innerHTML = `${keywordHtml}<div class="basis-full"></div>${flagHtml}`;
        el.querySelectorAll('.keyword-filter-btn').forEach(btn => {
            btn.addEventListener('click', () => this.toggleKeywordFilter(btn.dataset.keyword || ''));
        });
    },

    toggleUrgentFilter() {
        const active = this.activeListFilter?.type === 'urgent';
        this.activeListFilter = active ? null : { type: 'urgent', label: '需緊急處理' };
        this.filterList();
    },

    toggleKeywordFilter(keyword) {
        const active = this.activeListFilter?.type === 'keyword' && this.activeListFilter.value === keyword;
        this.activeListFilter = active ? null : { type: 'keyword', value: keyword, label: `熱門痛點：${keyword}` };
        this.filterList();
    },

    toggleFlagFilter(flagKey) {
        const meta = this.flagMeta[flagKey];
        if (!meta) return;
        const active = this.activeListFilter?.type === 'flag' && this.activeListFilter.value === flagKey;
        this.activeListFilter = active ? null : { type: 'flag', value: flagKey, label: meta.label };
        this.filterList();
    },

    clearListFilter() {
        this.activeListFilter = null;
        this.setSelectValues('risk-filter', ['all']);
        this.setSelectValues('platform-filter', ['all']);
        this.setSelectValues('content-filter', ['all']);
        this.filterList();
    },

    renderQuickFilterState() {
        const urgent = document.getElementById('urgent-filter-card');
        if (urgent) urgent.classList.toggle('ring-2', this.activeListFilter?.type === 'urgent');
        if (urgent) urgent.classList.toggle('ring-danger-300', this.activeListFilter?.type === 'urgent');
        const clear = document.getElementById('clear-list-filter');
        if (!clear) return;
        const riskValues = this.getSelectValues('risk-filter');
        const platformValues = this.getSelectValues('platform-filter');
        const contentValues = this.getSelectValues('content-filter');
        const hasFilter = Boolean(this.activeListFilter)
            || !this.isAllSelection(riskValues)
            || !this.isAllSelection(platformValues)
            || !this.isAllSelection(contentValues);
        clear.classList.toggle('hidden', !hasFilter);
        if (this.activeListFilter) {
            clear.textContent = `清除篩選：${this.activeListFilter.label}`;
        } else if (!this.isAllSelection(contentValues)) {
            const labels = contentValues.map(value => this.contentTypeMeta[value]?.label || value);
            clear.textContent = `清除篩選：${labels.join('、')}`;
        } else if (!this.isAllSelection(platformValues)) {
            clear.textContent = `清除篩選：${platformValues.join('、')}`;
        } else {
            clear.textContent = '清除篩選';
        }
    },

    renderTrends() {
        const rows = this.getTrendRows();
        const total = rows.length || 0;
        const pct = count => {
            if (!total) return 0;
            const value = count / total * 100;
            return value > 0 && value < 1 ? Number(value.toFixed(1)) : Math.round(value);
        };
        const sentiment = {
            positive: rows.filter(item => item.sentiment === 'positive').length,
            neutral: rows.filter(item => item.sentiment === 'neutral').length,
            negative: rows.filter(item => item.sentiment === 'negative').length
        };
        this.setText('trend-total-count', `共 ${total.toLocaleString()} 則`);
        this.setPct('trend-positive', pct(sentiment.positive), sentiment.positive);
        this.setPct('trend-neutral', pct(sentiment.neutral), sentiment.neutral);
        this.setPct('trend-negative', pct(sentiment.negative), sentiment.negative);

        const avg = key => total ? Math.round(rows.reduce((sum, item) => sum + (Number(item[key]) || 0), 0) / total * 100) : 0;
        this.setPct('emotion-joy', avg('emotionJoy'));
        this.setPct('emotion-anger', avg('emotionAnger'));
        this.setPct('emotion-disappointment', avg('emotionDisappointment'));

        const riskCounts = { critical: 0, high: 0, medium: 0, low: 0 };
        rows.forEach(item => { riskCounts[item.levelKey] = (riskCounts[item.levelKey] || 0) + 1; });
        this.setText('risk-critical-count', riskCounts.critical || 0);
        this.setText('risk-high-count', riskCounts.high || 0);
        this.setText('risk-medium-count', riskCounts.medium || 0);
        this.setText('risk-low-count', riskCounts.low || 0);
        this.renderTrendKeywords(rows);
        this.renderTrendTags(rows);

        const avgStarsVal = rows.length
            ? (rows.reduce((sum, item) => sum + (Number(item.stars) || 0), 0) / rows.length).toFixed(1)
            : '0.0';
        this.setText('kpi-avg-stars', `${avgStarsVal} ★`);

        const negativeReviews = rows.filter(item => item.sentiment === 'negative');
        const resolvedNegative = negativeReviews.filter(item => item.status === 'resolved' || item.raw.reviews_response);
        const replyRateVal = negativeReviews.length
            ? Math.round(resolvedNegative.length / negativeReviews.length * 100)
            : 100;
        this.setText('kpi-reply-rate', `${replyRateVal}%`);

        const crisisReviews = rows.filter(item => item.levelKey === 'critical' || item.levelKey === 'high');
        const resolvedCrisis = crisisReviews.filter(item => item.status === 'resolved' || item.raw.reviews_response);
        const resolutionRateVal = crisisReviews.length
            ? Math.round(resolvedCrisis.length / crisisReviews.length * 100)
            : 100;
        this.setText('kpi-resolution-rate', `${resolutionRateVal}%`);

        this.renderTrendCharts(rows);
        this.renderTrendFilterSummary(rows);
        this.renderTrendEventList(rows);
    },
    
    getTrendRows() {
        let rows = this.getBusinessFilteredRows();
        const platformValues = this.getSelectValues('trend-platform-filter');
        const contentValues = this.getSelectValues('trend-content-filter');
        const riskValues = this.getSelectValues('trend-risk-filter');
        const sentimentValues = this.getSelectValues('trend-sentiment-filter');
        if (!this.isAllSelection(platformValues)) rows = rows.filter(item => platformValues.includes(item.platform));
        if (!this.isAllSelection(contentValues)) rows = rows.filter(item => contentValues.includes(item.contentType));
        if (!this.isAllSelection(riskValues)) rows = rows.filter(item => riskValues.includes(item.levelKey));
        if (!this.isAllSelection(sentimentValues)) rows = rows.filter(item => sentimentValues.includes(item.sentiment));
        const filter = this.activeTrendFilter;
        if (!filter) return rows;
        if (filter.type === 'sentiment') rows = rows.filter(item => item.sentiment === filter.value);
        if (filter.type === 'platform') rows = rows.filter(item => item.platform === filter.value);
        if (filter.type === 'tag') rows = rows.filter(item => (item.tag || 'other') === filter.value);
        if (filter.type === 'risk') rows = rows.filter(item => item.levelKey === filter.value);
        if (filter.type === 'date') rows = rows.filter(item => item.date && item.date.toISOString().slice(0, 10) === filter.value);
        if (filter.type === 'keyword') rows = rows.filter(item => (item.text || '').includes(filter.value));
        if (filter.type === 'emotion') rows = rows.filter(item => Number(item[filter.value]) >= 0.5);
        return rows;
    },

    setTrendFilter(type, value, label) {
        this.activeTrendFilter = { type, value, label: label || value };
        this.renderTrends();
        const list = document.getElementById('trend-event-list');
        list?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    },

    clearTrendFilter() {
        this.activeTrendFilter = null;
        this.renderTrends();
    },

    applyTrendControls() {
        this.activeTrendFilter = null;
        this.renderTrends();
    },

    clearTrendControls() {
        ['trend-platform-filter', 'trend-content-filter', 'trend-risk-filter', 'trend-sentiment-filter'].forEach(id => {
            this.setSelectValues(id, ['all']);
        });
        this.activeTrendFilter = null;
        this.renderTrends();
    },

    renderTrendFilterSummary(rows) {
        const summary = document.getElementById('trend-filter-summary');
        const clear = document.getElementById('trend-clear-filter');
        if (!summary || !clear) return;
        const controlLabels = this.getTrendControlLabels();
        if (!this.activeTrendFilter) {
            const prefix = controlLabels.length ? `目前篩選：${controlLabels.join('、')}` : '目前顯示全部趨勢事件';
            summary.innerText = `${prefix}，共 ${rows.length.toLocaleString()} 則。點選任一圖表區塊可交叉篩選。`;
            clear.classList.add('hidden');
            return;
        }
        const labels = [...controlLabels, this.activeTrendFilter.label];
        summary.innerText = `目前篩選：${labels.join('、')}，共 ${rows.length.toLocaleString()} 則事件。其他圖表已依此條件重新計算。`;
        clear.classList.remove('hidden');
    },

    getTrendControlLabels() {
        const labels = [];
        const platform = this.getSelectValues('trend-platform-filter');
        const content = this.getSelectValues('trend-content-filter');
        const risk = this.getSelectValues('trend-risk-filter');
        const sentiment = this.getSelectValues('trend-sentiment-filter');
        if (!this.isAllSelection(platform)) labels.push(`平台：${platform.join('、')}`);
        if (!this.isAllSelection(content)) {
            labels.push(`內容：${content.map(value => this.contentTypeMeta[value]?.label || value).join('、')}`);
        }
        const riskLabels = { critical: '緊急風險', high: '高風險', medium: '中風險', low: '低風險' };
        if (!this.isAllSelection(risk)) labels.push(`風險：${risk.map(value => riskLabels[value] || value).join('、')}`);
        const sentimentLabels = { positive: '正面', neutral: '中立', negative: '負面' };
        if (!this.isAllSelection(sentiment)) labels.push(`情緒：${sentiment.map(value => sentimentLabels[value] || value).join('、')}`);
        return labels;
    },

    renderTrendEventList(rows) {
        const el = document.getElementById('trend-event-list');
        if (!el) return;
        if (!rows.length) {
            el.innerHTML = '<div class="px-6 py-8 text-sm text-slate-500">目前沒有符合篩選條件的事件。</div>';
            return;
        }
        el.innerHTML = rows.slice(0, 80).map(item => {
            const meta = this.tagMeta[item.tag] || this.tagMeta.other;
            const sentimentClass = item.sentiment === 'positive' ? 'bg-success-50 text-success-700 border-success-100' : item.sentiment === 'negative' ? 'bg-danger-50 text-danger-700 border-danger-100' : 'bg-warning-50 text-warning-700 border-warning-100';
            const sentimentLabel = item.sentiment === 'positive' ? '正面' : item.sentiment === 'negative' ? '負面' : '中立';
            return `<button type="button" onclick="App.selectIncident('${this.escapeHtml(item.id)}')" class="w-full text-left px-6 py-4 hover:bg-slate-50 transition-colors">
                <div class="flex flex-col md:flex-row md:items-center gap-3">
                    <div class="flex-1 min-w-0">
                        <div class="flex flex-wrap items-center gap-2 mb-1.5">
                            <span class="text-[11px] font-mono text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">${this.escapeHtml(item.id)}</span>
                            <span class="border px-1.5 py-0.5 rounded text-[10px] font-bold ${item.levelClass}">${this.escapeHtml(item.level)}</span>
                            <span class="border px-1.5 py-0.5 rounded text-[10px] font-bold ${sentimentClass}">${sentimentLabel}</span>
                            <span class="text-[10px] font-bold px-1.5 py-0.5 rounded border ${meta.cls}">${meta.icon} ${meta.label}</span>
                        </div>
                        <p class="text-sm font-semibold text-slate-800 line-clamp-2">${this.escapeHtml(item.text)}</p>
                    </div>
                    <div class="text-xs text-slate-500 md:text-right shrink-0">
                        <div>${this.escapeHtml(item.platform)}</div>
                        <div>${this.escapeHtml(item.time)}</div>
                    </div>
                </div>
            </button>`;
        }).join('');
    },
    
    renderTrendCharts(rows) {
        // 1. 各平台討論佔比 (Doughnut Chart)
        const platformCanvas = document.getElementById('platformShareChart');
        if (platformCanvas && window.Chart) {
            const platformCounts = {};
            rows.forEach(item => {
                const plat = item.platform || '其他';
                platformCounts[plat] = (platformCounts[plat] || 0) + 1;
            });
            const labels = Object.keys(platformCounts);
            const data = Object.values(platformCounts);

            const ctx = platformCanvas.getContext('2d');
            const fallbackColors = ['#ef4444', '#2563eb', '#16a34a', '#f59e0b', '#7c3aed', '#db2777', '#0891b2', '#ea580c'];
            const colors = labels.map((label, index) => {
                const name = String(label).toLowerCase();
                if (name.includes('google')) return '#22c55e';
                if (name.includes('ptt')) return '#f97316';
                if (name.includes('dcard')) return '#2563eb';
                if (name.includes('thread')) return '#111827';
                if (name.includes('facebook') || name === 'fb') return '#1d4ed8';
                if (name.includes('instagram') || name === 'ig') return '#e11d48';
                if (name.includes('tripadvisor')) return '#00af87';
                return fallbackColors[index % fallbackColors.length];
            });
            const hoverColors = colors.map(color => color);

            if (this.platformChart) {
                this.platformChart.data.labels = labels;
                this.platformChart.data.datasets[0].data = data;
                this.platformChart.data.datasets[0].backgroundColor = colors;
                this.platformChart.data.datasets[0].hoverBackgroundColor = hoverColors;
                this.platformChart.update('none');
            } else {
            this.platformChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: data,
                        backgroundColor: colors,
                        hoverBackgroundColor: hoverColors,
                        borderColor: '#ffffff',
                        borderWidth: 3,
                        borderOffset: 3,
                        hoverOffset: 12
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: {
                                boxWidth: 14,
                                boxHeight: 14,
                                color: '#334155',
                                font: { size: 12, weight: '700' },
                                padding: 14
                            }
                        },
                        tooltip: { backgroundColor: 'rgba(15, 23, 42, 0.95)', padding: 10, cornerRadius: 8, displayColors: true }
                    },
                    onClick: (event, elements) => {
                        if (!elements.length) return;
                        const label = this.platformChart.data.labels[elements[0].index];
                        this.setTrendFilter('platform', label, `平台：${label}`);
                    }
                }
            });
            }
        }

        // 2. 服務與餐點維度評估 (Radar Chart)
        const radarCanvas = document.getElementById('dimensionRadarChart');
        if (radarCanvas && window.Chart) {
            const tagRatings = { food: [], service: [], environment: [], price: [] };
            rows.forEach(item => {
                const t = item.tag;
                if (tagRatings[t] !== undefined && item.stars) {
                    tagRatings[t].push(item.stars);
                }
            });

            const labels = ['🍜 餐點', '🙋 服務', '🏠 環境', '💰 價格'];
            const data = [
                tagRatings.food.length ? (tagRatings.food.reduce((a, b) => a + b, 0) / tagRatings.food.length).toFixed(2) : 0,
                tagRatings.service.length ? (tagRatings.service.reduce((a, b) => a + b, 0) / tagRatings.service.length).toFixed(2) : 0,
                tagRatings.environment.length ? (tagRatings.environment.reduce((a, b) => a + b, 0) / tagRatings.environment.length).toFixed(2) : 0,
                tagRatings.price.length ? (tagRatings.price.reduce((a, b) => a + b, 0) / tagRatings.price.length).toFixed(2) : 0,
            ];

            const ctx = radarCanvas.getContext('2d');
            if (this.radarChart) {
                this.radarChart.data.labels = labels;
                this.radarChart.data.datasets[0].data = data;
                this.radarChart.update('none');
            } else {
            this.radarChart = new Chart(ctx, {
                type: 'radar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: '平均滿意星等 (1-5)',
                        data: data,
                        backgroundColor: 'rgba(59, 130, 246, 0.15)',
                        borderColor: '#3b82f6',
                        pointBackgroundColor: '#3b82f6',
                        pointBorderColor: '#fff',
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: '#3b82f6',
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    scales: { r: { angleLines: { display: true }, suggestedMin: 1, suggestedMax: 5, ticks: { stepSize: 1, font: { size: 9 } } } },
                    plugins: { legend: { display: false } },
                    onClick: (event, elements) => {
                        if (!elements.length) return;
                        const tags = ['food', 'service', 'environment', 'price'];
                        const tag = tags[elements[0].index];
                        const meta = this.tagMeta[tag] || this.tagMeta.other;
                        this.setTrendFilter('tag', tag, `主題：${meta.label}`);
                    }
                }
            });
            }
        }

        // 3. 情感指數與評分波動走勢 (Line Chart)
        const historyCanvas = document.getElementById('sentimentHistoryChart');
        if (historyCanvas && window.Chart) {
            const trend = this.buildTrendData();
            const bins = {};
            rows.forEach(item => {
                if (!item.date) return;
                const dateStr = item.date.toISOString().slice(0, 10);
                if (!bins[dateStr]) {
                    bins[dateStr] = { positive: 0, negative: 0, totalStars: 0, count: 0 };
                }
                if (item.sentiment === 'positive') bins[dateStr].positive++;
                if (item.sentiment === 'negative') bins[dateStr].negative++;
                if (item.stars) {
                    bins[dateStr].totalStars += item.stars;
                    bins[dateStr].count++;
                }
            });

            const sortedLabels = Object.keys(bins).sort();
            const netSentimentData = [];
            const avgRatingData = [];

            sortedLabels.forEach(lbl => {
                const bin = bins[lbl];
                const totalSentiment = bin.positive + bin.negative || 1;
                const netScore = Math.round((bin.positive - bin.negative) / totalSentiment * 100);
                netSentimentData.push(netScore);
                const avgStars = bin.count ? (bin.totalStars / bin.count).toFixed(2) : 0;
                avgRatingData.push(avgStars);
            });

            const labels = sortedLabels.length ? sortedLabels : trend.labels;
            const finalNetSentiment = sortedLabels.length ? netSentimentData : trend.labels.map(() => Math.floor(Math.random() * 40) + 30);
            const finalAvgRating = sortedLabels.length ? avgRatingData : trend.labels.map(() => (Math.random() * 1.5 + 3.5).toFixed(2));

            const ctx = historyCanvas.getContext('2d');
            if (this.historyChartInstance) {
                this.historyChartInstance.data.labels = labels;
                this.historyChartInstance.data.datasets[0].data = finalNetSentiment;
                this.historyChartInstance.data.datasets[0].pointRadius = labels.length > 15 ? 1 : 3;
                this.historyChartInstance.data.datasets[1].data = finalAvgRating;
                this.historyChartInstance.data.datasets[1].pointRadius = labels.length > 15 ? 1 : 3;
                this.historyChartInstance.update('none');
            } else {
            this.historyChartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        { label: '淨正面情感率 (%)', data: finalNetSentiment, borderColor: '#10b981', backgroundColor: 'rgba(16, 185, 129, 0.05)', yAxisID: 'ySentiment', borderWidth: 2.5, tension: 0.3, fill: true, pointRadius: labels.length > 15 ? 1 : 3 },
                        { label: '平均評分 (星等)', data: finalAvgRating, borderColor: '#f59e0b', backgroundColor: 'transparent', yAxisID: 'yRating', borderWidth: 2.5, tension: 0.3, pointRadius: labels.length > 15 ? 1 : 3 }
                    ]
                },
                options: {
                    responsive: true, maintainAspectRatio: false, interaction: { mode: 'index', intersect: false },
                    onClick: (event, elements) => {
                        if (!elements.length) return;
                        const dateLabel = this.historyChartInstance.data.labels[elements[0].index];
                        this.setTrendFilter('date', dateLabel, `日期：${dateLabel}`);
                    },
                    scales: {
                        ySentiment: { type: 'linear', position: 'left', title: { display: true, text: '淨情感率 (%)', font: { size: 10 } }, ticks: { font: { size: 9 } } },
                        yRating: { type: 'linear', position: 'right', suggestedMin: 1, suggestedMax: 5, grid: { drawOnChartArea: false }, title: { display: true, text: '平均評分 (星等)', font: { size: 10 } }, ticks: { font: { size: 9 } } }
                    }
                }
            });
            }
        }
    },

    setPct(prefix, value, count = null) {
        const countText = count === null ? '' : ` (${Number(count || 0).toLocaleString()}筆)`;
        this.setText(`${prefix}-pct`, `${value}%${countText}`);
        const bar = document.getElementById(`${prefix}-bar`);
        if (bar) bar.style.width = `${value}%`;
    },

    topKeywords(rows) {
        const counts = {};
        if (!this.keywordPatterns) {
            this.keywordPatterns = this.keywordSeeds.map(keyword => [
                keyword,
                new RegExp(keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g')
            ]);
        }
        rows.forEach(item => {
            const text = item.text || '';
            this.keywordPatterns.forEach(([keyword, pattern]) => {
                pattern.lastIndex = 0;
                const matches = text.match(pattern);
                if (matches) counts[keyword] = (counts[keyword] || 0) + matches.length;
            });
        });
        return Object.entries(counts).sort((a, b) => b[1] - a[1]);
    },

    renderTrendKeywords(rows) {
        const el = document.getElementById('trend-keywords');
        if (!el) return;
        const keywords = this.topKeywords(rows).slice(0, 10);
        el.innerHTML = keywords.length
            ? keywords.map(([kw, count], index) => {
                const cls = index < 2 ? 'bg-danger-50 text-danger-700 border-danger-200' : 'bg-slate-100 text-slate-700 border-slate-200';
                return `<button type="button" onclick="App.setTrendFilter('keyword', '${this.escapeHtml(kw)}', '關鍵字：${this.escapeHtml(kw)}')" class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full ${cls} border text-sm font-bold hover:brightness-95 transition-all">${this.escapeHtml(kw)} <span class="bg-white/50 px-1.5 rounded text-xs">${count}</span></button>`;
            }).join('')
            : '<span class="text-sm text-slate-400">目前篩選區間沒有足夠關鍵詞。</span>';
    },

    renderTrendTags(rows) {
        const el = document.getElementById('trend-tags');
        if (!el) return;
        const counts = {};
        rows.forEach(item => { counts[item.tag || 'other'] = (counts[item.tag || 'other'] || 0) + 1; });
        const total = rows.length || 1;
        const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]);
        el.innerHTML = entries.length
            ? entries.map(([tag, count]) => {
                const meta = this.tagMeta[tag] || this.tagMeta.other;
                const percent = Math.round(count / total * 100);
                return `<button type="button" onclick="App.setTrendFilter('tag', '${this.escapeHtml(tag)}', '主題：${this.escapeHtml(meta.label)}')" class="theme-tag border ${meta.cls}">${meta.icon} ${meta.label} <span class="text-xs bg-white/50 px-1.5 rounded ml-1">${percent}%</span></button>`;
            }).join('')
            : '<span class="text-sm text-slate-400">目前沒有主題分類資料。</span>';
    },

    setText(id, value) {
        const el = document.getElementById(id);
        if (el) el.innerText = value;
    },

    showEmptyState(message) {
        const tbody = document.getElementById('incident-list');
        if (tbody) tbody.innerHTML = `<tr><td class="px-6 py-8 text-sm text-slate-500">${this.escapeHtml(message)}</td></tr>`;
        this.setText('list-count', '顯示 0 筆');
        this.setText('urgent-badge', '0');
        this.setText('mobile-urgent-badge', '0');
        this.setText('kpi-urgent', '0');
    },

    renderList(dataArray) {
        const tbody = document.getElementById('incident-list');
        const countLabel = document.getElementById('list-count');
        if (!tbody || !countLabel) return;
        tbody.innerHTML = '';
        const visibleRows = dataArray.slice(0, this.listRenderLimit);
        countLabel.innerText = dataArray.length > visibleRows.length
            ? `顯示 ${visibleRows.length} / ${dataArray.length} 筆`
            : `顯示 ${dataArray.length} 筆`;
        if (!dataArray.length) {
            tbody.innerHTML = '<tr><td class="px-6 py-8 text-sm text-slate-500">目前沒有符合條件的資料。</td></tr>';
            return;
        }
        const fragment = document.createDocumentFragment();
        visibleRows.forEach(item => {
            const contentMeta = this.contentTypeMeta[item.contentType] || this.contentTypeMeta.unknown;
            const statusHtml = item.status === 'resolved'
                ? '<span class="text-[10px] font-bold text-success-600 flex items-center justify-end gap-1"><i class="ph-bold ph-check text-xs"></i> 已結案</span>'
                : '<span class="text-[10px] font-bold text-warning-600 flex items-center justify-end gap-1"><i class="ph-fill ph-circle text-[6px] animate-pulse"></i> 待處理</span>';
            const tr = document.createElement('tr');
            tr.className = `incident-row tr-interactive group ${item.id === this.currentActiveId ? 'tr-active' : ''}`;
            tr.dataset.incidentId = item.id;
            tr.onclick = () => this.selectIncident(item.id);
            tr.innerHTML = `
                <td class="pl-6 py-4 w-12 text-center"><div title="${this.escapeHtml(item.platform)}" class="w-6 h-6 rounded-full flex items-center justify-center ${item.iconClass} shadow-sm group-hover:scale-110 transition-transform overflow-hidden">${item.iconContent}</div></td>
                <td class="px-3 py-4"><div class="flex flex-wrap items-center gap-2 mb-1.5"><span class="border px-1.5 py-0.5 rounded text-[10px] font-bold ${item.levelClass} shadow-sm">${this.escapeHtml(item.level)}</span><span class="border px-1.5 py-0.5 rounded text-[10px] font-bold ${contentMeta.cls}">${this.escapeHtml(contentMeta.label)}</span><span class="text-[11px] font-mono text-slate-400 bg-slate-100 px-1 rounded">${this.escapeHtml(item.id)}</span></div><p class="text-[11px] text-slate-500 mb-1 line-clamp-1">${this.escapeHtml(item.businessName || item.platform)}</p><p class="font-medium text-slate-800 line-clamp-1 pr-4">${this.escapeHtml(item.text)}</p></td>
                <td class="px-3 py-4 text-right w-24"><p class="text-xs text-slate-500 mb-1.5 font-medium">${this.escapeHtml(item.time)}</p>${statusHtml}</td>`;
            fragment.appendChild(tr);
        });
        if (dataArray.length > visibleRows.length) {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td colspan="3" class="px-6 py-4 text-center">
                    <button type="button" onclick="App.showMoreListRows()" class="px-4 py-2 rounded-md border border-slate-200 bg-white text-xs font-bold text-slate-600 hover:bg-slate-50">
                        載入更多 ${Math.min(this.listRenderStep, dataArray.length - visibleRows.length)} 筆
                    </button>
                </td>`;
            fragment.appendChild(tr);
        }
        tbody.appendChild(fragment);
    },

    filterList() {
        const filtered = this.getListFilteredRows();
        this.currentListRows = filtered;
        this.listRenderLimit = this.listRenderStep;
        this.renderList(filtered);
        this.renderQuickFilterState();
        this.renderDashboard(filtered);
        this.renderChart(filtered);
    },

    showMoreListRows() {
        this.listRenderLimit += this.listRenderStep;
        this.renderList(this.currentListRows || []);
    },

    selectIncident(id) {
        const panel = document.getElementById('detail-panel');
        const contentArea = document.getElementById('detail-content-area');
        if (panel?.classList.contains('w-0')) this.openDetailPanel();
        document.querySelectorAll('.tr-interactive').forEach(el => el.classList.remove('tr-active'));
        const activeRow = [...document.querySelectorAll('.tr-interactive')].find(el => el.dataset.incidentId === id);
        if (activeRow) activeRow.classList.add('tr-active');
        this.currentActiveId = id;
        const data = this.data.find(item => item.id === id);
        if (!data) return;
        contentArea?.classList.remove('content-fade');
        if (contentArea) void contentArea.offsetWidth;
        contentArea?.classList.add('content-fade');
        this.setText('detail-id', data.id);
        this.setText('detail-platform', data.platform);
        this.setText('detail-time', data.time);
        this.setText('detail-text', data.text);
        this.setText('detail-business', data.businessName || '--');
        this.setText('detail-filter-reason', data.filterReason ? `內容分類：${data.filterReason}` : '');
        let starsHtml = '';
        for (let i = 0; i < 5; i++) starsHtml += i < data.stars ? '<i class="ph-fill ph-star"></i>' : '<i class="ph ph-star"></i>';
        document.getElementById('detail-stars').innerHTML = starsHtml;
        const badge = document.getElementById('detail-badge');
        badge.className = `px-2.5 py-1 rounded-md text-xs font-bold shadow-sm border ${data.levelClass}`;
        badge.innerText = `${data.level} 事件`;
        const contentTypeBadge = document.getElementById('detail-content-type');
        const contentMeta = this.contentTypeMeta[data.contentType] || this.contentTypeMeta.unknown;
        if (contentTypeBadge) {
            contentTypeBadge.className = `px-2 py-0.5 rounded border text-[10px] font-bold ${contentMeta.cls}`;
            contentTypeBadge.innerText = contentMeta.label;
        }
        this.setText('ai-painpoint', data.ai.painpoint);
        this.setText('ai-advice', data.ai.advice);
        this.setText('ai-sop', data.ai.sop);
        document.getElementById('ai-draft').value = data.raw.reviews_response || data.ai.draft || '';

        const gotoBtn = document.getElementById("btn-goto-source");
        if (gotoBtn) {
            if (ENABLE_GOTO_SOURCE_BUTTON) {
                gotoBtn.classList.remove('hidden');
            } else {
                gotoBtn.classList.add('hidden');
            }
        }
    },

    gotoSourceReview() {
        if (!this.currentActiveId) return;
        const current = this.data.find(item => item.id === this.currentActiveId);
        if (!current) return;
        let targetUrl =
            current.raw?.review_link || current.raw?.source_url || current.raw?.url ||
            current.raw?.post_url || current.raw?.comment_url || current.raw?.google_url || '';

        if (!targetUrl || targetUrl === "尚無網址" || targetUrl.trim() === "") {
            const shopName = current.businessName || "文章牛肉湯";
            targetUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(shopName)}`;
        }
        window.open(targetUrl, '_blank');
    },

    openDetailPanel() {
        const detailPanel = document.getElementById('detail-panel');
        if (!detailPanel) return;
        detailPanel.classList.remove('w-0', 'opacity-0', 'border-l-0');
        detailPanel.classList.add('w-[480px]', 'opacity-100', 'border-l');
    },

    closeDetailPanel(clearActive = false) {
        const detailPanel = document.getElementById('detail-panel');
        if (!detailPanel) return;
        detailPanel.classList.remove('w-[480px]', 'opacity-100', 'border-l');
        detailPanel.classList.add('w-0', 'opacity-0', 'border-l-0');
        if (clearActive) {
            document.querySelectorAll('.tr-interactive').forEach(el => el.classList.remove('tr-active'));
            this.currentActiveId = null;
        }
    },

    saveListFilterState(viewName = this.currentWorkspaceView) {
        if (!['overview', 'crisis'].includes(viewName)) return;
        this.listFilterState[viewName] = {
            platform: this.getSelectValues('platform-filter'),
            content: this.getSelectValues('content-filter'),
            risk: this.getSelectValues('risk-filter'),
            activeListFilter: this.activeListFilter ? { ...this.activeListFilter } : null
        };
    },

    restoreListFilterState(viewName) {
        if (!['overview', 'crisis'].includes(viewName)) return;
        const state = this.listFilterState[viewName] || this.listFilterState.overview;
        const platformFilter = document.getElementById('platform-filter');
        const contentFilter = document.getElementById('content-filter');
        const riskFilter = document.getElementById('risk-filter');
        const setValue = (el, values) => {
            if (!el) return;
            const available = new Set([...el.options].map(option => option.value));
            const nextValues = (Array.isArray(values) ? values : [values])
                .filter(value => value && available.has(value));
            this.setSelectValues(el.id, nextValues.length ? nextValues : ['all']);
        };
        setValue(platformFilter, state.platform);
        setValue(contentFilter, state.content);
        setValue(riskFilter, state.risk);
        this.activeListFilter = state.activeListFilter ? { ...state.activeListFilter } : null;
        this.currentWorkspaceView = viewName;
        this.filterList();
    },

    updateWorkspaceMode(viewName) {
        const summary = document.getElementById('workspace-dashboard-summary');
        const title = document.querySelector('.event-toolbar h3');
        if (summary) summary.classList.toggle('hidden', viewName === 'crisis');
        if (title) title.textContent = viewName === 'crisis' ? '危機留言清單' : '輿情事件清單';
    },

    switchView(viewName) {
        this.closeMobileBusinessMenu();
        this.saveListFilterState();
        ['overview', 'crisis', 'trends'].forEach(nav => {
            // 桌機導覽狀態
            const el = document.getElementById(`nav-${nav}`);
            if (el) el.className = 'nav-item flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-600 hover:bg-slate-50 transition-colors';
            
            // 手機底部導覽狀態 (重置為灰色)
            const botEl = document.getElementById(`bottom-nav-${nav}`);
            if (botEl) {
                botEl.className = 'flex flex-col items-center justify-center w-full h-full text-slate-400 relative';
                const icon = botEl.querySelector('i');
                if(icon) icon.className = icon.className.replace('ph-fill', 'ph');
                const span = botEl.querySelector('span.font-bold');
                if(span) span.className = span.className.replace('font-bold', 'font-medium');
            }
        });
        const viewWorkspace = document.getElementById('view-workspace');
        const viewTrends = document.getElementById('view-trends');
        
        // 設定桌機導覽 Active
        const activeNav = document.getElementById(`nav-${viewName}`);
        if(activeNav) {
            activeNav.classList.add('active');
            activeNav.classList.remove('text-slate-600', 'hover:bg-slate-50');
        }
        
        // 設定手機底部導覽 Active (切換為藍色與實心 icon)
        const activeBotNav = document.getElementById(`bottom-nav-${viewName}`);
        if(activeBotNav) {
            activeBotNav.className = 'flex flex-col items-center justify-center w-full h-full text-blue-600 relative';
            const icon = activeBotNav.querySelector('i');
            if(icon) icon.className = icon.className.replace('ph', 'ph-fill');
            const span = activeBotNav.querySelector('span.font-medium');
            if(span) span.className = span.className.replace('font-medium', 'font-bold');
        }

        if (viewName === 'overview') {
            viewWorkspace.classList.remove('hidden');
            viewTrends.classList.add('hidden');
            this.updateWorkspaceMode('overview');
            this.restoreListFilterState('overview');
            this.closeDetailPanel(true);
        } else if (viewName === 'crisis') {
            viewWorkspace.classList.remove('hidden');
            viewTrends.classList.add('hidden');
            this.updateWorkspaceMode('crisis');
            this.restoreListFilterState('crisis');
            if (window.matchMedia('(min-width: 1024px)').matches) {
                const rows = this.getListFilteredRows();
                const targetId = this.currentActiveId || rows[0]?.id;
                if (targetId) this.selectIncident(targetId);
            }
        } else if (viewName === 'trends') {
            viewWorkspace.classList.add('hidden');
            viewTrends.classList.remove('hidden');
            this.updateWorkspaceMode('overview');
            this.closeDetailPanel(true);
            this.currentWorkspaceView = 'trends';
            this.renderTrends();
        }
    },

    renderChart(rows = this.getListFilteredRows()) {
        const canvas = document.getElementById('mainTrendChart');
        if (!canvas || !window.Chart) return;
        Chart.defaults.font.family = '"Inter", "Noto Sans TC", sans-serif';
        Chart.defaults.color = '#94a3b8';
        const ctx = canvas.getContext('2d');
        const gradient = ctx.createLinearGradient(0, 0, 0, 160);
        gradient.addColorStop(0, 'rgba(59, 130, 246, 0.2)');
        gradient.addColorStop(1, 'rgba(59, 130, 246, 0)');
        const trend = this.buildTrendData(rows);
        if (this.chart) {
            this.chart.data.labels = trend.labels;
            this.chart.data.datasets[0].data = trend.total;
            this.chart.data.datasets[1].data = trend.risk;
            this.chart.update('none');
            return;
        }
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: trend.labels, datasets: [
                    { label: '評論量', data: trend.total, borderColor: '#3b82f6', backgroundColor: gradient, borderWidth: 2, tension: 0.4, fill: true, pointBackgroundColor: '#ffffff', pointBorderColor: '#3b82f6', pointBorderWidth: 2, pointRadius: 4, pointHoverRadius: 6 },
                    { label: '風險評論', data: trend.risk, borderColor: '#ef4444', borderWidth: 2, borderDash: [5, 5], tension: 0.4, pointRadius: 0, pointHoverRadius: 5 }
                ]
            },
            options: { responsive: true, maintainAspectRatio: false, interaction: { mode: 'index', intersect: false }, plugins: { legend: { display: false }, tooltip: { backgroundColor: 'rgba(15, 23, 42, 0.9)', padding: 10, cornerRadius: 8 } }, scales: { x: { grid: { display: false, drawBorder: false } }, y: { display: false, beginAtZero: true } } }
        });
    },

    buildRecentMonthBuckets(anchor = this.getAnchorDate(), count = 6) {
        return [...Array(count)].map((_, i) => {
            const date = new Date(anchor.getFullYear(), anchor.getMonth() - (count - 1 - i), 1);
            const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
            return { key, label: `${date.getFullYear()}/${date.getMonth() + 1}`, total: 0, risk: 0 };
        });
    },

    buildTrendData(rows = this.getListFilteredRows()) {
        const anchor = this.getAnchorDate();
        if (this.activeRange === 'all') {
            const buckets = this.buildRecentMonthBuckets(anchor, 6);
            const bucketsByMonth = Object.fromEntries(buckets.map(month => [month.key, month]));
            rows.forEach(item => {
                if (!item.date) return;
                const key = `${item.date.getFullYear()}-${String(item.date.getMonth() + 1).padStart(2, '0')}`;
                if (!bucketsByMonth[key]) return;
                bucketsByMonth[key].total += 1;
                if (['critical', 'high'].includes(item.levelKey)) bucketsByMonth[key].risk += 1;
            });
            return { labels: buckets.map(d => d.label), total: buckets.map(d => d.total), risk: buckets.map(d => d.risk) };
        }
        const days = Number(this.activeRange) || 7;
        const buckets = [...Array(days)].map((_, i) => {
            const date = new Date(anchor);
            date.setDate(anchor.getDate() - (days - 1 - i));
            const key = date.toISOString().slice(0, 10);
            const label = days > 30
                ? `${date.getFullYear()}/${date.getMonth() + 1}/${date.getDate()}`
                : `${date.getMonth() + 1}/${date.getDate()}`;
            return { key, label, total: 0, risk: 0 };
        });
        const byKey = Object.fromEntries(buckets.map(day => [day.key, day]));
        rows.forEach(item => {
            if (!item.date) return;
            const key = item.date.toISOString().slice(0, 10);
            if (!byKey[key]) return;
            byKey[key].total += 1;
            if (['critical', 'high'].includes(item.levelKey)) byKey[key].risk += 1;
        });
        return { labels: buckets.map(d => d.label), total: buckets.map(d => d.total), risk: buckets.map(d => d.risk) };
    },
    renderAiModelOptions(provider) {
        const select = document.getElementById('ai-model-select');
        const input = document.getElementById('ai-model');
        if (!select || !input) return;
        const models = this.aiProviderModels[provider] || [];
        select.innerHTML = models.map(model => `<option value="${this.escapeHtml(model)}">${this.escapeHtml(model)}</option>`).join('') + '<option value="__custom__">自訂模型...</option>';
        const current = input.value || models[0] || '';
        if (models.includes(current)) {
            select.value = current;
        } else {
            select.value = '__custom__';
        }
        if (!input.value && models[0]) input.value = models[0];
    },

    syncSelectedAiModel() {
        const select = document.getElementById('ai-model-select');
        const input = document.getElementById('ai-model');
        if (!select || !input) return;
        if (select.value !== '__custom__') input.value = select.value;
        input.classList.toggle('hidden', select.value !== '__custom__');
        if (select.value === '__custom__') input.focus();
    },
    updateAiProviderFields() {
        const provider = document.getElementById('ai-provider')?.value || 'gemini';
        const endpointInput = document.getElementById('ai-endpoint');
        const modelInput = document.getElementById('ai-model');
        this.renderAiModelOptions(provider);
        const help = document.getElementById('ai-provider-help');
        const defaults = {
            ollama: { model: 'qwen2.5:3b', endpoint: 'http://localhost:11434', help: 'Ollama 會連到使用者自己的電腦。請先執行 ollama serve，必要時設定 OLLAMA_ORIGINS。' },
            gemini: { model: 'gemini-3.6-flash', endpoint: '', help: 'Gemini API Key 會由後端自動讀取 .env 的 GEMINI_API_KEY。' },
            huggingface: { model: 'meta-llama/Llama-3.1-8B-Instruct', endpoint: 'https://router.huggingface.co/v1/chat/completions', help: 'Hugging Face token 會由後端自動讀取 .env 的 HUGGINGFACE_API_KEY。可自行替換支援 Chat Completion 的模型名稱。' }
        };
        if (endpointInput) endpointInput.classList.toggle('hidden', provider !== 'ollama' && provider !== 'huggingface');
        if (modelInput && defaults[provider]) modelInput.value = defaults[provider].model;
        this.renderAiModelOptions(provider);
        this.syncSelectedAiModel();
        if (endpointInput && defaults[provider]) endpointInput.value = defaults[provider].endpoint;
        if (help && defaults[provider]) help.textContent = defaults[provider].help;
        const status = document.getElementById('ai-provider-status');
        if (status) {
            status.textContent = '尚未設定';
            status.className = 'text-[11px] font-bold text-slate-400 whitespace-nowrap';
        }
        this.aiProvider.configured = false;
    },

    async connectAiProvider() {
        const provider = document.getElementById('ai-provider')?.value || 'gemini';
        this.syncSelectedAiModel();
        const model = (document.getElementById('ai-model')?.value || '').trim();
        const endpoint = (document.getElementById('ai-endpoint')?.value || '').trim();
        const status = document.getElementById('ai-provider-status');
        const help = document.getElementById('ai-provider-help');
        const button = document.getElementById('ai-provider-connect');
        if (status) {
            status.textContent = '檢查中...';
            status.className = 'text-[11px] font-bold text-primary-600 whitespace-nowrap';
        }
        if (button) button.disabled = true;
        try {
            if (!model) throw new Error('請先輸入模型名稱');
            this.aiProvider = {
                provider,
                model,
                apiKey: '',
                endpoint: endpoint || (provider === 'ollama' ? 'http://localhost:11434' : ''),
                configured: true,
                models: []
            };
            if (provider === 'ollama') {
                const response = await fetch(`${this.aiProvider.endpoint}/api/tags`, { method: 'GET' });
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                const payload = await response.json();
                const models = Array.isArray(payload.models) ? payload.models.map(item => item.name).filter(Boolean) : [];
                this.aiProvider.models = models;
                if (!models.includes(this.aiProvider.model) && models.length) this.aiProvider.model = models[0];
            }
            if (status) {
                status.textContent = provider === 'ollama' ? `已連線：${this.aiProvider.model}` : `已設定：${provider}`;
                status.className = 'text-[11px] font-bold text-success-600 whitespace-nowrap';
            }
            if (help) help.textContent = '已套用模型設定。接下來產生回覆會優先使用此模型，並遵循原本回覆規則。';
            if (this.showToast) this.showToast('AI 模型設定已套用');
            return true;
        } catch (error) {
            this.aiProvider.configured = false;
            if (status) {
                status.textContent = '設定失敗';
                status.className = 'text-[11px] font-bold text-danger-600 whitespace-nowrap';
            }
            if (help) {
                const tip = provider === 'ollama'
                    ? '請先在本機執行 ollama serve 與 ollama pull qwen2.5:3b。若在 Streamlit Cloud 使用，請設定 OLLAMA_ORIGINS 後重啟 Ollama。'
                    : '請確認後端 .env API Key、模型名稱與供應商帳號權限。';
                help.textContent = `${tip} 錯誤：${error.message}`;
            }
            return false;
        } finally {
            if (button) button.disabled = false;
        }
    },

    buildAiReplyPrompt(item, toneType) {
        const sentimentLabel = item.sentiment === 'positive' ? '正面' : item.sentiment === 'negative' ? '負面' : '中立';
        const tone = toneType === 'apologetic' ? '誠懇致歉' : '專業說明';
        const tag = this.tagMeta[item.tag]?.label || '一般體驗';
        const risk = item.level || item.levelKey || '未指定';
        const riskNotes = [];
        if (item.flags?.food_safety) riskNotes.push('食安疑慮');
        if (item.flags?.legal_risk) riskNotes.push('法律風險');
        if (item.flags?.hygiene_risk) riskNotes.push('衛生疑慮');
        const guidance = item.sentiment === 'negative'
            ? '請展現同理、承擔與改善方向，但不要承諾退款、賠償、法律責任 or 尚未確認的事實。'
            : '請展現感謝、親切與品牌溫度，可自然邀請再次光臨。';
        return `你是台南餐飲品牌的資深客服與公關回覆專員。請根據單一顧客評論，產生可直接貼到公開平台的繁體中文回覆。\n\n必須遵守：\n- 語氣：${tone}\n- 情緒判斷：${sentimentLabel}\n- 風險等級：${risk}\n- 主題分類：${tag}\n- 風險提示：${riskNotes.join('、') || '一般體驗回饋'}\n- 平台：${item.platform}\n- 星等：${item.stars || '未提供'}\n- ${guidance}\n- 回覆 80 到 160 字。\n- 不要輸出 Markdown 標題。\n- 不要列點。\n- 不要自稱 AI。\n- 不要提到內部模型、資料庫、規則或系統分析。\n\n顧客評論：\n${item.text}`;
    },

    async generateWithSelectedAI(item, toneType) {
        if (!this.aiProvider.configured) {
            const ok = await this.connectAiProvider();
            if (!ok) throw new Error('AI 模型尚未設定完成');
        }
        const prompt = this.buildAiReplyPrompt(item, toneType);
        const { provider, model, endpoint } = this.aiProvider;
        if (provider === 'ollama') {
            const response = await fetch(`${endpoint}/api/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model, prompt, stream: false, options: { temperature: toneType === 'apologetic' ? 0.55 : 0.7 } })
            });
            if (!response.ok) throw new Error(`Ollama 回應失敗：HTTP ${response.status}`);
            const payload = await response.json();
            return (payload.response || '').trim();
        }
        if (provider === 'gemini' || provider === 'huggingface') {
            const response = await this.fetchJsonWithFallback('/api/ai-reply', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
                body: JSON.stringify({
                    provider,
                    model,
                    endpoint: provider === 'huggingface' ? endpoint : '',
                    prompt,
                    temperature: toneType === 'apologetic' ? 0.55 : 0.7
                })
            }, 60000);
            return (response.payload?.reply || '').trim();
        }
        throw new Error('不支援的 AI 供應商');
    },
    getSelectedProviderLabel() {
        const provider = document.getElementById('ai-provider')?.value || this.aiProvider.provider || 'gemini';
        return { ollama: 'Ollama', gemini: 'Gemini', huggingface: 'Hugging Face' }[provider] || provider;
    },

    hasAiProviderControls() {
        return Boolean(document.getElementById('ai-provider') && document.getElementById('ai-model'));
    },
    async changeTone(toneType) {
        const textarea = document.getElementById('ai-draft');
        const loading = document.getElementById('ai-generating');
        const current = this.data.find(item => item.id === this.currentActiveId);
        if (!textarea || !current) return;
        loading.classList.remove('hidden');
        textarea.classList.remove('typing-indicator');
        textarea.value = '正在使用 ' + this.getSelectedProviderLabel() + ' / ' + (document.getElementById('ai-model')?.value || this.aiProvider.model) + ' 產生回覆...';
        try {
            if (this.hasAiProviderControls()) {
                const draft = await this.generateWithSelectedAI(current, toneType);
                current.ai = {
                    ...(current.ai || {}),
                    draft,
                    advice: current.ai?.advice || '已使用自選 AI 模型產生回覆。',
                    painpoint: current.ai?.painpoint || '依目前評論內容產生公開回覆。',
                    sop: current.ai?.sop || 'Custom AI Provider'
                };
                this.setText('ai-painpoint', current.ai.painpoint);
                this.setText('ai-advice', current.ai.advice);
                this.setText('ai-sop', current.ai.sop);
                const status = document.getElementById('ai-provider-status');
                if (status) {
                    status.textContent = '使用中：' + this.getSelectedProviderLabel() + ' / ' + this.aiProvider.model;
                    status.className = 'text-[11px] font-bold text-success-600 whitespace-nowrap';
                }
                loading.classList.add('hidden');
                textarea.value = draft;
                return;
            }

            const { payload } = await this.fetchJsonWithFallback('/api/dashboard-reply', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
                body: JSON.stringify({
                    review: current.text,
                    rating: current.stars || 1,
                    platform: current.platform,
                    risk_level: current.levelKey,
                    sentiment_label: current.sentiment,
                    tone: toneType === 'apologetic' ? '誠懇致歉' : '專業說明',
                    engine: 'ollama',
                    flag_food_safety: Boolean(current.flags?.food_safety),
                    flag_legal_risk: Boolean(current.flags?.legal_risk),
                    flag_hygiene_risk: Boolean(current.flags?.hygiene_risk)
                })
            });
            const report = payload.report_content || payload.result_text || '';
            current.raw.report_content = report;
            current.ai = this.parseAiReport(report);
            this.setText('ai-painpoint', current.ai.painpoint);
            this.setText('ai-advice', current.ai.advice);
            this.setText('ai-sop', current.ai.sop);
            loading.classList.add('hidden');
            textarea.value = '';
            textarea.classList.add('typing-indicator');
            const newText = current.ai.draft || report || '模型已完成分析，但沒有產生可直接複製的公開回覆草稿。';
            let i = 0;
            const typing = setInterval(() => {
                textarea.value += newText.charAt(i);
                i += 1;
                if (i >= newText.length) {
                    clearInterval(typing);
                    textarea.classList.remove('typing-indicator');
                }
            }, 12);
        } catch (error) {
            loading.classList.add('hidden');
            textarea.classList.remove('typing-indicator');
            current.ai = this.localAiFallback(current, toneType, error.message);
            this.setText('ai-painpoint', current.ai.painpoint);
            this.setText('ai-advice', current.ai.advice);
            this.setText('ai-sop', current.ai.sop);
            textarea.value = `${current.ai.draft}\n\n（${this.getSelectedProviderLabel()} 模型呼叫失敗，已先使用本地規則與標籤產生回覆。原始錯誤：${error.message}）`;
        }
    },

    showConfirmModal() {
        const draftText = document.getElementById('ai-draft').value;
        if (!draftText || draftText.trim() === '' || draftText.includes('正在依據') || draftText.includes('尚無回覆草稿')) {
            alert('回覆草稿內容無效，請先生成回覆！');
            return;
        }
        const modal = document.getElementById('confirm-modal');
        if (!modal) return;
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        modal.offsetHeight;
        modal.classList.remove('opacity-0');
        modal.querySelector('div').classList.remove('scale-95');
    },

    closeConfirmModal() {
        const modal = document.getElementById('confirm-modal');
        if (!modal) return;
        modal.classList.add('opacity-0');
        modal.querySelector('div').classList.add('scale-95');
        setTimeout(() => {
            modal.classList.remove('flex');
            modal.classList.add('hidden');
        }, 300);
    },

    async persistResolvedReply(draftText) {
        const streamlitConfig = window.STREAMLIT_SUPABASE_CONFIG;
        const target = this.data.find(item => item.id === this.currentActiveId);
        if (streamlitConfig) {
            if (!streamlitConfig.supabaseUrl || !streamlitConfig.supabaseKey) {
                throw new Error('Streamlit 缺少 SUPABASE_PUBLIC_KEY，無法寫回 Supabase');
            }
            if (
                String(streamlitConfig.supabaseKey).startsWith('sb_secret_') ||
                String(streamlitConfig.supabaseKey).includes('service_role')
            ) {
                throw new Error('SUPABASE_PUBLIC_KEY 必須填 anon/public key，不能填 secret/service_role key');
            }
            const tableName = streamlitConfig.tableName || 'master_reviews_result';
            const baseEndpoint = `${streamlitConfig.supabaseUrl.replace(/\/$/, '')}/rest/v1/${tableName}`;
            const keyCandidates = [
                ['master_review_id', target?.raw?.master_review_id],
                ['review_id', target?.raw?.review_id],
                ['id', target?.raw?.id],
                ['master_review_id', target?.masterReviewId],
                ['review_id', this.currentActiveId],
                ['id', this.currentActiveId]
            ].filter((entry, index, source) => {
                const [column, value] = entry;
                return value !== null && value !== undefined && value !== ''
                    && source.findIndex(([otherColumn, otherValue]) => otherColumn === column && String(otherValue) === String(value)) === index;
            });
            const patchRow = async (column, value, body) => {
                const endpoint = `${baseEndpoint}?${column}=eq.${encodeURIComponent(value)}`;
                const response = await fetch(endpoint, {
                    method: 'PATCH',
                    headers: {
                        apikey: streamlitConfig.supabaseKey,
                        Authorization: `Bearer ${streamlitConfig.supabaseKey}`,
                        'Content-Type': 'application/json',
                        Prefer: 'return=representation'
                    },
                    body: JSON.stringify(body)
                });
                const text = await response.text();
                const payload = text ? JSON.parse(text) : null;
                if (!response.ok) throw new Error(payload?.message || payload?.error || `HTTP ${response.status}`);
                if (!Array.isArray(payload) || payload.length === 0) {
                    throw new Error(`未更新任何資料列（${column}=${value}）`);
                }
                return payload;
            };

            const updateAttempts = [
                {
                    reviews_response: draftText,
                    status: 'resolved',
                    updated_at: new Date().toISOString()
                },
                { reviews_response: draftText }
            ];
            const errors = [];
            for (const [column, value] of keyCandidates) {
                for (const body of updateAttempts) {
                    try {
                        await patchRow(column, value, body);
                        return target;
                    } catch (error) {
                        errors.push(error.message);
                    }
                }
            }
            throw new Error(`Supabase 沒有寫入任何資料。請確認主鍵欄位與 RLS update policy。嘗試結果：${errors.slice(0, 4).join('；')}`);
        }

        await this.fetchJsonWithFallback('/api/reviews/resolve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
            body: JSON.stringify({
                review_id: this.currentActiveId,
                response_text: draftText
            })
        });
        return target;
    },

    async submitAndResolve() {
        if (!this.currentActiveId) return;
        const draftText = document.getElementById('ai-draft').value;
        const submitBtn = document.getElementById('confirm-submit-btn');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="ph-bold ph-spinner-gap animate-spin"></i> 送出中...';
        }

        try {
            const target = await this.persistResolvedReply(draftText);

            try {
                await navigator.clipboard.writeText(draftText);
            } catch (clipErr) {
                const textarea = document.getElementById('ai-draft');
                textarea.select();
                document.execCommand('copy');
            }

            if (target) {
                target.status = 'resolved';
                target.raw.reviews_response = draftText;
                target.raw.status = 'resolved';
            }

            this.closeConfirmModal();

            const toast = document.getElementById('toast');
            if (toast) {
                toast.classList.remove('translate-y-20', 'opacity-0');
                setTimeout(() => toast.classList.add('translate-y-20', 'opacity-0'), 3000);
            }

            this.filterList();
            this.renderTrends();

            const activeRow = [...document.querySelectorAll('.tr-interactive')].find(el => el.dataset.incidentId === this.currentActiveId);
            if (activeRow) activeRow.classList.add('tr-active');

        } catch (err) {
            alert(`提交失敗：${err.message}`);
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '確認送出';
            }
        }
    },

    escapeHtml(value) {
        return String(value ?? '').replace(/[&<>'"]/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char]));
    },

    escapeAttr(value) {
        return this.escapeHtml(String(value ?? '').replace(/\\/g, '\\\\').replace(/'/g, "\\'"));
    }
};

window.App = App;
document.addEventListener('DOMContentLoaded', () => App.init());
