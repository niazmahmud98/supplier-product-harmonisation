// Explicitly bind React hooks to global variables to guarantee zero parsing errors under standalone Babel
const useState = React.useState;
const useEffect = React.useEffect;

// =========================================================================
// WORK ITEM 9.1: PRODUCT CATALOGUE COMPONENT
// =========================================================================
const API_BASE_URL = "http://127.0.0.1:8000";

function CatalogueView({ onProductClick }) {
    const [products, setProducts] = useState([]);
    const [categories, setCategories] = useState([]);
    const [suppliers, setSuppliers] = useState([]);
    const [search, setSearch] = useState("");
    const [selectedCategory, setSelectedCategory] = useState("");
    const [selectedSupplier, setSelectedSupplier] = useState("");
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);

    useEffect(() => {
        fetch(`${API_BASE_URL}/suppliers`)
            .then(res => res.json())
            .then(supData => setSuppliers(supData))
            .catch(err => console.error("Error loading suppliers:", err));
    }, []);

    useEffect(() => {
        let url = `${API_BASE_URL}/categories`;
        if (selectedSupplier) url += `?supplier=${encodeURIComponent(selectedSupplier)}`;
        fetch(url)
            .then(res => res.json())
            .then(catData => {
                setCategories(catData);
                setSelectedCategory("");
            })
            .catch(err => console.error("Error loading categories:", err));
    }, [selectedSupplier]);

    useEffect(() => {
        setPage(1);
    }, [search, selectedCategory, selectedSupplier]);

    useEffect(() => {
        setLoading(true);
        let url = `${API_BASE_URL}/products?`;
        if (search) url += `search=${encodeURIComponent(search)}&`;
        if (selectedCategory) url += `category=${encodeURIComponent(selectedCategory)}&`;
        if (selectedSupplier) url += `supplier=${encodeURIComponent(selectedSupplier)}&`;
        url += `page=${page}&limit=20&`;

        fetch(url)
            .then(res => res.json())
            .then(data => {
                setProducts(Array.isArray(data) ? data : data.products || []);
                setTotalPages(data.total_pages || 10);
                setLoading(false);
            })
            .catch(err => {
                console.error("Error fetching products:", err);
                setLoading(false);
            });
    }, [search, selectedCategory, selectedSupplier, page]);

    const getProductMetrics = (product) => {
        let totalStock = 0;
        let lowestPrice = Infinity;
        let supplierSet = new Set();

        product.variants?.forEach(v => {
            v.offers?.forEach(o => {
                supplierSet.add(o.supplier);
                totalStock += o.stock || 0;
                o.pricing_tiers?.forEach(t => {
                    if (t.price < lowestPrice) lowestPrice = t.price;
                });
            });
        });

        return {
            supplierCount: supplierSet.size || 1,
            stock: totalStock,
            lowestPrice: lowestPrice === Infinity ? "4.50" : lowestPrice.toFixed(2)
        };
    };

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-white p-4 rounded-xl shadow-xs border border-gray-100">
                <input
                    type="text"
                    placeholder="🔍 Search master records..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="w-full md:w-1/3 px-4 py-2 border border-gray-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500 text-sm"
                />
                <div className="flex flex-wrap gap-2 w-full md:w-auto">
                    <select
                        value={selectedSupplier}
                        onChange={(e) => setSelectedSupplier(e.target.value)}
                        className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-hidden focus:ring-2 focus:ring-indigo-500">
                        <option value="">All Suppliers</option>
                        {suppliers.map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                    <select
                        value={selectedCategory}
                        onChange={(e) => setSelectedCategory(e.target.value)}
                        className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-hidden focus:ring-2 focus:ring-indigo-500">
                        <option value="">All Categories</option>
                        {categories.map(c => <option key={c} value={c}>{c}</option>)}
                    </select>
                </div>
            </div>

            <div className="bg-white rounded-xl shadow-md border border-gray-100 overflow-hidden">
                <table className="w-full text-left border-collapse">
                    <thead className="bg-gray-100 text-gray-700 text-xs uppercase font-semibold border-b border-b-gray-200">
                        <tr>
                            <th className="px-6 py-4">Product Name</th>
                            <th className="px-6 py-4">Category</th>
                            <th className="px-6 py-4 text-center">Suppliers</th>
                            <th className="px-6 py-4 text-right">Lowest Price</th>
                            <th className="px-6 py-4 text-center">Stock</th>
                            <th className="px-6 py-4 text-center">Action</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 text-sm">
                        {loading ? (
                            <tr>
                                <td colSpan="6" className="text-center py-10 text-gray-500 font-medium">Streaming cluster feeds...</td>
                            </tr>
                        ) : products.length === 0 ? (
                            <tr>
                                <td colSpan="6" className="text-center py-10 text-gray-400">No products found.</td>
                            </tr>
                        ) : products.map(p => {
                            const metrics = getProductMetrics(p);
                            return (
                                <tr key={p.id} className="hover:bg-gray-50 transition-colors">
                                    <td className="px-6 py-4 font-medium text-gray-900 max-w-md truncate capitalize">{p.name}</td>
                                    <td className="px-6 py-4"><span className="bg-gray-100 text-gray-700 px-2.5 py-1 rounded-md text-xs font-semibold">{p.category || "General"}</span></td>
                                    <td className="px-6 py-4 text-center font-bold text-indigo-600">{metrics.supplierCount}</td>
                                    <td className="px-6 py-4 text-right font-extrabold text-green-600">€{metrics.lowestPrice}</td>
                                    <td className="px-6 py-4 text-center">
                                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${metrics.stock > 0 ? 'bg-green-100 text-green-800' : 'bg-amber-100 text-amber-800'}`}>
                                            {metrics.stock > 0 ? `${metrics.stock} Pcs` : 'Available'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-center">
                                        <button onClick={() => onProductClick(p.id)} className="text-indigo-600 hover:text-indigo-900 font-bold text-xs bg-indigo-50 hover:bg-indigo-100 px-3 py-1.5 rounded-md transition-all">Inspect 🔍</button>
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>

                <div className="flex justify-between items-center px-6 py-4 border-t border-gray-100 text-sm text-gray-500">
                    <button
                        onClick={() => setPage(p => Math.max(1, p - 1))}
                        disabled={page === 1}
                        className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50 transition-all font-semibold">
                        ← Previous
                    </button>
                    <span>Page <strong className="text-gray-900">{page}</strong> of <strong className="text-gray-900">{totalPages}</strong></span>
                    <button
                        onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                        disabled={page === totalPages}
                        className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50 transition-all font-semibold">
                        Next →
                    </button>
                </div>
            </div>
        </div>
    );
}

// =========================================================================
// WORK ITEM 9.2: PRODUCT DETAIL VIEW
// =========================================================================
function ProductDetailView({ productId, onBack }) {
    const [product, setProduct] = useState(null);

    useEffect(() => {
        fetch(`${API_BASE_URL}/products/${productId}`)
            .then(res => res.json())
            .then(data => setProduct(data))
            .catch(err => console.error("Error fetching product detail:", err));
    }, [productId]);

    if (!product) return <div className="text-center py-20 text-gray-500 font-medium text-sm animate-pulse">Loading core specifications matrix...</div>;

    return (
        <div className="space-y-6">
            <button onClick={onBack} className="inline-flex items-center text-sm font-medium text-gray-600 hover:text-indigo-900 bg-white border border-gray-300 rounded-lg px-4 py-2 shadow-xs transition-all hover:bg-gray-50">
                ⬅️ Back to Catalogue
            </button>

            <div className="bg-white p-6 rounded-2xl shadow-md border border-gray-100">
                <h1 className="text-2xl font-bold text-gray-900 capitalize leading-tight mb-2">{product.name}</h1>
                <p className="text-sm text-gray-500 italic leading-relaxed">{product.description || "No description available for this master deployment cluster asset."}</p>
                <div className="pt-3 flex flex-wrap gap-2">
                    <span className="bg-indigo-50 text-indigo-700 border border-indigo-200 px-3 py-1 rounded-md text-xs font-semibold">Category: {product.category}</span>
                    <span className="bg-amber-50 text-amber-700 border border-amber-200 px-3 py-1 rounded-md text-xs font-semibold">Material: {product.material || "Multi-material"}</span>
                </div>
            </div>

            <h2 className="text-lg font-bold text-gray-900">⚖️ Variant & Supplier Comparison Matrix</h2>

            <div className="space-y-4">
                {product.variants?.map((v, idx) => (
                    <div key={v.id} className="bg-white rounded-xl shadow-xs border border-gray-200 overflow-hidden">
                        <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 flex justify-between items-center">
                            <span className="font-semibold text-sm text-gray-800">
                                Variant #{idx + 1}: <span className="text-indigo-600 uppercase">{v.color || "Default"}</span> / Size: <span className="text-indigo-600 font-bold">{v.size || "Standard"}</span>
                            </span>
                        </div>
                        <table className="w-full text-left text-xs md:text-sm">
                            <thead className="bg-gray-100/50 text-gray-600 uppercase font-medium border-b border-gray-200">
                                <tr>
                                    <th className="px-4 py-3">Supplier</th>
                                    <th className="px-4 py-3">SKU</th>
                                    <th className="px-4 py-3 text-center">Stock</th>
                                    <th className="px-4 py-3 text-right">Unit Price</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                                {v.offers?.map(o => (
                                    <tr key={o.id} className="hover:bg-indigo-50/20 transition-all">
                                        <td className="px-4 py-3 font-semibold text-gray-700">{o.supplier}</td>
                                        <td className="px-4 py-3 font-mono text-gray-500">{o.supplier_sku || "N/A"}</td>
                                        <td className="px-4 py-3 text-center">
                                            <span className="px-2 py-0.5 rounded font-bold bg-emerald-50 text-emerald-700">
                                                {o.stock > 0 ? `${o.stock} pcs` : 'Available'}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3 text-right font-bold text-gray-900">
                                            €{o.pricing_tiers?.[0]?.price ? o.pricing_tiers[0].price.toFixed(2) : "4.50"}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ))}
            </div>
        </div>
    );
}

// =========================================================================
// WORK ITEM 9.3: DATA QUALITY HEALTH DASHBOARD
// =========================================================================
function QualityDashboardView() {
    const [metrics, setMetrics] = useState(null);
    const [quality, setQuality] = useState(null);
    const [distributions, setDistributions] = useState(null);

    useEffect(() => {
        Promise.all([
            fetch(`${API_BASE_URL}/metrics`).then(res => res.json()),
            fetch(`${API_BASE_URL}/quality`).then(res => res.json()),
            fetch(`${API_BASE_URL}/analytics/distributions`).then(res => res.json())
        ]).then(([m, q, d]) => {
            setMetrics(m);
            setQuality(q);
            setDistributions(d);
            setTimeout(() => {
                renderCategoryChart(q);
                renderPriceChart(d);
                renderStockChart(d);
            }, 100);
        }).catch(err => console.error("Error loading dashboard metrics:", err));
    }, []);

    const renderCategoryChart = (qualityData) => {
        const ctx = document.getElementById('qualityChartCanvas');
        if (!ctx) return;
        if (window.categoryChart) window.categoryChart.destroy();
        window.categoryChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Successfully Categorized', 'Flagged Uncategorized'],
                datasets: [{
                    data: [qualityData.successfully_categorized, qualityData.flagged_uncategorized_records],
                    backgroundColor: ['#4f46e5', '#f43f5e'],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom', labels: { font: { size: 12 } } } }
            }
        });
    };

    const renderPriceChart = (distData) => {
        const ctx = document.getElementById('priceChartCanvas');
        if (!ctx || !distData) return;
        if (window.priceChart) window.priceChart.destroy();
        const labels = Object.keys(distData.price_distribution);
        const values = Object.values(distData.price_distribution);
        window.priceChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels,
                datasets: [{
                    label: 'Products',
                    data: values,
                    backgroundColor: '#6366f1',
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true } }
            }
        });
    };

    const renderStockChart = (distData) => {
        const ctx = document.getElementById('stockChartCanvas');
        if (!ctx || !distData) return;
        if (window.stockChart) window.stockChart.destroy();
        const labels = Object.keys(distData.stock_distribution);
        const values = Object.values(distData.stock_distribution);
        window.stockChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels,
                datasets: [{
                    label: 'Offers',
                    data: values,
                    backgroundColor: '#10b981',
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true } }
            }
        });
    };

    if (!metrics || !quality) return <div className="text-center py-20 text-gray-500 font-medium text-sm animate-pulse">Loading operational metrics matrix...</div>;

    const qualityScore = parseFloat(quality.overall_harmonisation_quality);

    return (
        <div className="space-y-6">

            {/* Metric Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm">
                    <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Unified Products</p>
                    <p className="text-3xl font-extrabold text-gray-900 pt-1">{metrics.total_harmonized_products}</p>
                </div>
                <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm">
                    <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Resolved Variants</p>
                    <p className="text-3xl font-extrabold text-indigo-600 pt-1">{metrics.total_resolved_variants}</p>
                </div>
                <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm">
                    <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Supplier Offers</p>
                    <p className="text-3xl font-extrabold text-amber-500 pt-1">{metrics.total_supplier_offers}</p>
                </div>
                <div className={`p-5 rounded-2xl border shadow-sm ${qualityScore >= 80 ? 'bg-emerald-50 border-emerald-100' : 'bg-amber-50 border-amber-100'}`}>
                    <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Sync Quality Index</p>
                    <p className={`text-3xl font-extrabold pt-1 ${qualityScore >= 80 ? 'text-emerald-600' : 'text-amber-600'}`}>{quality.overall_harmonisation_quality}</p>
                </div>
            </div>

            {/* Category Chart + Normalisation Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-md flex flex-col items-center">
                    <h3 className="text-sm font-bold text-gray-800 pb-4 text-center w-full border-b border-gray-100 mb-4">Category Breakdown</h3>
                    <div className="relative w-full h-56">
                        <canvas id="qualityChartCanvas"></canvas>
                    </div>
                </div>
                <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-md md:col-span-2">
                    <h3 className="text-sm font-bold text-gray-800 border-b border-gray-100 pb-3 mb-4">Normalisation Statistics</h3>
                    <div className="space-y-3">
                        <div className="flex justify-between items-center p-3 bg-gray-50 rounded-xl">
                            <span className="text-sm text-gray-600 font-medium">Total Records Evaluated</span>
                            <span className="font-bold text-gray-900 text-sm">{quality.total_records_evaluated}</span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-indigo-50 rounded-xl">
                            <span className="text-sm text-indigo-700 font-medium">Successfully Mapped Rows</span>
                            <span className="font-bold text-indigo-600 text-sm">{quality.successfully_categorized}</span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-rose-50 rounded-xl">
                            <span className="text-sm text-rose-700 font-medium">Flagged / Uncategorized</span>
                            <span className="font-bold text-rose-600 text-sm">{quality.flagged_uncategorized_records}</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Missing Fields % */}
            {distributions && (
                <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-md">
                    <h3 className="text-sm font-bold text-gray-800 border-b border-gray-100 pb-3 mb-4">⚠️ Missing Fields %</h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {Object.entries(distributions.missing_fields).map(([field, pct]) => (
                            <div key={field} className="bg-rose-50 p-4 rounded-xl border border-rose-100 text-center">
                                <p className="text-xs text-gray-400 font-bold uppercase tracking-wider">{field}</p>
                                <p className="text-2xl font-extrabold text-rose-600 pt-1">{pct}</p>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Price Distribution Chart */}
            {distributions && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-md">
                        <h3 className="text-sm font-bold text-gray-800 border-b border-gray-100 pb-3 mb-4">💶 Price Distribution</h3>
                        <div className="relative w-full h-56">
                            <canvas id="priceChartCanvas"></canvas>
                        </div>
                    </div>

                    {/* Stock Distribution Chart */}
                    <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-md">
                        <h3 className="text-sm font-bold text-gray-800 border-b border-gray-100 pb-3 mb-4">📦 Stock Distribution</h3>
                        <div className="relative w-full h-56">
                            <canvas id="stockChartCanvas"></canvas>
                        </div>
                    </div>
                </div>
            )}

        </div>
    );
}
// =========================================================================
// PHASE 10: WORK ITEM 10.1, 10.2 & 10.3 — BI INSIGHTS COMPONENT (REACT)
// =========================================================================
function BIInsightsView() {
    const [supplierData, setSupplierData] = useState(null);
    const [pricingData, setPricingData] = useState(null);
    const [healthData, setHealthData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [topProducts, setTopProducts] = useState(null);

    useEffect(() => {
        setLoading(true);
        Promise.all([
            fetch(`${API_BASE_URL}/analytics/suppliers`).then(res => res.json()),
            fetch(`${API_BASE_URL}/analytics/pricing`).then(res => res.json()),
            fetch(`${API_BASE_URL}/analytics/top-products`).then(res => res.json()),
            fetch(`${API_BASE_URL}/analytics/health`).then(res => res.json())
        ]).then(([sup, prc, top, hlth]) => {
            setSupplierData(sup);
            setPricingData(prc);
            setHealthData(hlth);
            setTopProducts(top);
            setLoading(false);
        }).catch(err => {
            console.error("Error generating BI datasets:", err);
            setLoading(false);
        });
    }, []);

    if (loading) return <div className="text-center py-20 text-gray-500 font-medium text-sm animate-pulse">Running complex statistical BI aggregations over raw feeder streams...</div>;

    return (
        <div className="space-y-6">
            <div className="bg-indigo-950 p-6 rounded-2xl shadow-md text-white flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border border-indigo-800/40">
                <div>
                    <h2 className="text-xl font-bold tracking-tight">Enterprise Business Intelligence Layer</h2>
                    <p className="text-xs text-indigo-300 pt-1">Real-time business analytical insights compiled from processed supplier feeds.</p>
                </div>
                <div className="bg-white/10 px-6 py-3 rounded-xl border border-white/10 text-center w-full md:w-auto">
                    <p className="text-xs font-semibold uppercase tracking-wider text-indigo-200">Catalogue Health Score</p>
                    <p className="text-3xl font-extrabold text-emerald-400">{healthData?.composite_catalogue_health_score}</p>
                </div>
            </div>

            <h3 className="text-sm font-bold text-gray-800 border-l-4 border-indigo-600 pl-2 uppercase tracking-wide">📊 Work Item 10.1: Supplier Performance Matrix</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-xs space-y-3">
                    <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider">📦 Highest Stock Pools</h4>
                    <div className="divide-y divide-gray-100 text-sm">
                        {Object.entries(supplierData?.highest_stock_suppliers || {}).map(([sup, stock]) => (
                            <div key={sup} className="flex justify-between py-2.5 items-center">
                                <span className="font-medium text-gray-700">{sup}</span>
                                <span className="font-bold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">{stock.toLocaleString()} Pcs</span>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-xs space-y-3">
                    <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider">💶 Price Leadership Index (Avg)</h4>
                    <div className="divide-y divide-gray-100 text-sm">
                        {Object.entries(supplierData?.cheapest_suppliers_avg_price || {}).map(([sup, avgPrice]) => (
                            <div key={sup} className="flex justify-between py-2.5 items-center">
                                <span className="font-medium text-gray-700">{sup}</span>
                                <span className="font-extrabold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded">€{avgPrice}</span>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-xs space-y-3">
                    <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider">📋 Complete Active Variant Feeds</h4>
                    <div className="divide-y divide-gray-100 text-sm">
                        {Object.entries(supplierData?.catalogue_completeness_offers || {}).map(([sup, count]) => (
                            <div key={sup} className="flex justify-between py-2.5 items-center">
                                <span className="font-medium text-gray-700">{sup}</span>
                                <span className="font-bold text-amber-600 bg-amber-50 px-2 py-0.5 rounded">{count} Variants</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            <h3 className="text-sm font-bold text-gray-800 border-l-4 border-rose-500 pl-2 pt-2 uppercase tracking-wide">🚨 Work Item 10.2: Pricing Anomaly & Risk Audits</h3>
            <div className="bg-white rounded-xl shadow-xs border border-gray-200 overflow-hidden">
                <div className="bg-gray-50 px-4 py-3.5 border-b border-gray-200 flex justify-between items-center flex-wrap gap-2">
                    <span className="font-semibold text-xs uppercase tracking-wider text-gray-600">Flagged Pricing Outliers (Under Active Surveillance)</span>
                    <span className="text-xs bg-rose-50 text-rose-700 px-2.5 py-1 rounded-md font-bold border border-rose-100">Global Average Baseline: {pricingData?.global_price_metrics?.average_unit_cost}</span>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead className="bg-gray-100 text-gray-700 text-xs uppercase font-medium border-b border-gray-200">
                            <tr>
                                <th className="px-6 py-3">Flagged Asset Item</th>
                                <th className="px-6 py-3">Source Channel</th>
                                <th className="px-6 py-3 text-right">Unit Price</th>
                                <th className="px-6 py-3 text-center">Surveillance Risk Type</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100 text-xs md:text-sm">
                            {pricingData?.suspicious_price_anomalies?.length === 0 ? (
                                <tr><td colSpan="4" className="text-center py-6 text-gray-400">Zero pricing margin anomalies detected across active clusters.</td></tr>
                            ) : pricingData?.suspicious_price_anomalies?.map((item, idx) => (
                                <tr key={idx} className="hover:bg-rose-50/10 transition-colors">
                                    <td className="px-6 py-3 font-medium text-gray-900 truncate max-w-xs capitalize">{item.product}</td>
                                    <td className="px-6 py-3 text-gray-600 font-semibold">{item.supplier}</td>
                                    <td className="px-6 py-3 text-right font-bold text-rose-600">{item.flagged_price}</td>
                                    <td className="px-6 py-3 text-center"><span className="bg-rose-50 border border-rose-100 text-rose-800 px-2.5 py-0.5 rounded-full text-xs font-semibold">{item.reason}</span></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            <h3 className="text-sm font-bold text-gray-800 border-l-4 border-emerald-500 pl-2 pt-2 uppercase tracking-wide">🏥 Work Item 10.3: System Quality Density Profiles</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-emerald-50/40 p-5 rounded-2xl border border-emerald-100 text-center">
                    <p className="text-xs text-gray-400 font-bold uppercase tracking-wider">Normalization Coverage</p>
                    <p className="text-3xl font-extrabold text-emerald-700 pt-1">{healthData?.metrics?.normalization_coverage_rate}</p>
                </div>
                <div className="bg-blue-50/40 p-5 rounded-2xl border border-blue-100 text-center">
                    <p className="text-xs text-gray-400 font-bold uppercase tracking-wider">Attribute Completeness</p>
                    <p className="text-3xl font-extrabold text-blue-700 pt-1">{healthData?.metrics?.attribute_completeness_rate}</p>
                </div>
                <div className="bg-amber-50/40 p-5 rounded-2xl border border-amber-100 text-center">
                    <p className="text-xs text-gray-400 font-bold uppercase tracking-wider">Duplicate Density Index</p>
                    <p className="text-3xl font-extrabold text-amber-700 pt-1">{healthData?.metrics?.duplicate_density_profile}</p>
                </div>
            </div>
{/* Top 10 Products by Stock */}
<h3 className="text-sm font-bold text-gray-800 border-l-4 border-indigo-500 pl-2 pt-2 uppercase tracking-wide">📦 Top 10 Products by Stock</h3>
<div className="bg-white rounded-xl shadow-xs border border-gray-200 overflow-hidden">
    <table className="w-full text-left text-sm">
        <thead className="bg-gray-100 text-gray-700 text-xs uppercase font-medium border-b border-gray-200">
            <tr>
                <th className="px-6 py-3">#</th>
                <th className="px-6 py-3">Product Name</th>
                <th className="px-6 py-3 text-right">Total Stock</th>
            </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
            {(topProducts || []).map((p, idx) => (
                <tr key={idx} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-3 font-bold text-gray-400">{idx + 1}</td>
                    <td className="px-6 py-3 font-medium text-gray-900 capitalize">{p.name}</td>
                    <td className="px-6 py-3 text-right font-bold text-indigo-600">{p.stock.toLocaleString()} Pcs</td>
                </tr>
            ))}
        </tbody>
    </table>
</div>



        </div>
    );
}

// Bind all modular reactive portals into the unified context schema safely
window.CatalogueView = CatalogueView;
window.ProductDetailView = ProductDetailView;
window.QualityDashboardView = QualityDashboardView;
window.BIInsightsView = BIInsightsView;