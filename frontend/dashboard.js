

// =========================================================================
// WORK ITEM 9.1: PRODUCT CATALOGUE COMPONENT
// =========================================================================
const API_BASE_URL = "http://127.0.0.1:8000";

// =========================================================================
// WORK ITEM 9.1: PRODUCT CATALOGUE COMPONENT
// =========================================================================
function CatalogueView({ onProductClick }) {
    const [products, setProducts] = useState([]);
    const [categories, setCategories] = useState([]);
    const [suppliers, setSuppliers] = useState([]);
    const [search, setSearch] = useState("");
    const [selectedCategory, setSelectedCategory] = useState("");
    const [selectedSupplier, setSelectedSupplier] = useState("");
    const [loading, setLoading] = useState(true);

    // Suppliers একবারই load হবে
    useEffect(() => {
        fetch(`${API_BASE_URL}/suppliers`)
            .then(res => res.json())
            .then(supData => setSuppliers(supData))
            .catch(err => console.error("Error loading suppliers:", err));
    }, []);

    // Supplier বদলালে categories reload হবে
    useEffect(() => {
        let url = `${API_BASE_URL}/categories`;
        if (selectedSupplier) url += `?supplier=${encodeURIComponent(selectedSupplier)}`;

        fetch(url)
            .then(res => res.json())
            .then(catData => {
                setCategories(catData);
                setSelectedCategory(""); // supplier বদলালে category reset
            })
            .catch(err => console.error("Error loading categories:", err));
    }, [selectedSupplier]);

    useEffect(() => {
        setLoading(true);
        let url = `${API_BASE_URL}/products?`;
        if (search) url += `search=${encodeURIComponent(search)}&`;
        if (selectedCategory) url += `category=${encodeURIComponent(selectedCategory)}&`;
        if (selectedSupplier) url += `supplier=${encodeURIComponent(selectedSupplier)}&`;

        fetch(url)
            .then(res => res.json())
            .then(data => {
                setProducts(data);
                setLoading(false);
            })
            .catch(err => {
                console.error("Error fetching products:", err);
                setLoading(false);
            });
    }, [search, selectedCategory, selectedSupplier]);

    // Helper calculation metrics for table row display
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
            lowestPrice: lowestPrice === Infinity ? "0.00" : lowestPrice.toFixed(2)
        };
    };

    return (
        <div class="space-y-6">
            <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-white p-4 rounded-xl shadow-xs border border-gray-100">
                <input 
                    type="text" 
                    placeholder="🔍 Search master products or descriptions..." 
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    class="w-full md:w-1/3 px-4 py-2 border border-gray-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500 text-sm"
                />
                <div class="flex flex-wrap gap-2 w-full md:w-auto">
                    <select 
                        value={selectedSupplier} 
                        onChange={(e) => setSelectedSupplier(e.target.value)}
                        class="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-hidden focus:ring-2 focus:ring-indigo-500">
                        <option value="">All Suppliers</option>
                        {suppliers.map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                    <select 
                        value={selectedCategory} 
                        onChange={(e) => setSelectedCategory(e.target.value)}
                        class="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-hidden focus:ring-2 focus:ring-indigo-500">
                        <option value="">All Categories</option>
                        {categories.map(c => <option key={c} value={c}>{c}</option>)}
                    </select>
                </div>
            </div>

            <div class="bg-white rounded-xl shadow-md border border-gray-100 overflow-hidden">
                <table class="w-full text-left border-collapse">
                    <thead class="bg-gray-100 text-gray-700 text-xs uppercase font-semibold border-b border-gray-200">
                        <tr>
                            <th class="px-6 py-4">Product Identity & Master Name</th>
                            <th class="px-6 py-4">Category</th>
                            <th class="px-6 py-4 text-center">Suppliers</th>
                            <th class="px-6 py-4 text-right">Lowest Cost</th>
                            <th class="px-6 py-4 text-center">Inventory Stock</th>
                            <th class="px-6 py-4 text-center">Action</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-100 text-sm">
                        {loading ? (
                            <tr>
                                <td colspan="6" class="text-center py-10 text-gray-500 font-medium">Streaming records from local backend engine...</td>
                            </tr>
                        ) : products.length === 0 ? (
                            <tr>
                                <td colspan="6" class="text-center py-10 text-gray-400">No synchronized records match your active filters.</td>
                            </tr>
                        ) : products.map(p => {
                            const metrics = getProductMetrics(p);
                            return (
                                <tr key={p.id} class="hover:bg-gray-50 transition-colors">
                                    <td class="px-6 py-4 font-medium text-gray-900 max-w-md truncate">{p.name}</td>
                                    <td class="px-6 py-4"><span class="bg-gray-200 text-gray-700 px-2 py-0.5 rounded-sm text-xs font-medium">{p.category}</span></td>
                                    <td class="px-6 py-4 text-center font-semibold text-indigo-600">{metrics.supplierCount}</td>
                                    <td class="px-6 py-4 text-right font-bold text-green-600">€{metrics.lowestPrice}</td>
                                    <td class="px-6 py-4 text-center">
                                        <span class={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${metrics.stock > 0 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                                            {metrics.stock > 0 ? `${metrics.stock} In Stock` : 'Out of Stock'}
                                        </span>
                                    </td>
                                    <td class="px-6 py-4 text-center">
                                        <button onClick={() => onProductClick(p.id)} class="text-indigo-600 hover:text-indigo-900 font-medium text-xs bg-indigo-50 hover:bg-indigo-100 px-3 py-1.5 rounded-md transition-all">Inspect 🔍</button>
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

// =========================================================================
// WORK ITEM 9.2: PRODUCT DETAIL VIEW WITH COMPARISON TABLES
// =========================================================================
function ProductDetailView({ productId, onBack }) {
    const [product, setProduct] = useState(null);

    useEffect(() => {
        fetch(`${API_BASE_URL}/products/${productId}`)
            .then(res => res.json())
            .then(data => setProduct(data))
            .catch(err => console.error("Error fetching detail payload:", err));
    }, [productId]);

    if (!product) return <div class="text-center py-20 text-gray-500 font-medium text-sm">Parsing model details...</div>;

    return (
        <div class="space-y-6 animate-fade-in">
            <button onClick={onBack} class="inline-flex items-center text-sm font-medium text-gray-600 hover:text-indigo-900 bg-white border border-gray-300 rounded-lg px-4 py-2 shadow-xs transition-all hover:bg-gray-50">
                ⬅️ Back to Master Catalogue
            </button>

            <div class="bg-white p-6 rounded-2xl shadow-md border border-gray-100 grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="md:col-span-2 space-y-3">
                    <h1 class="text-2xl font-bold text-gray-900 capitalize leading-tight">{product.name}</h1>
                    <p class="text-sm text-gray-500 italic leading-relaxed">{product.description || "No harmonized specification text available for this master asset group."}</p>
                    <div class="pt-2 flex flex-wrap gap-2">
                        <span class="bg-indigo-50 text-indigo-700 border border-indigo-200 px-3 py-1 rounded-md text-xs font-semibold">Category: {product.category}</span>
                        <span class="bg-amber-50 text-amber-700 border border-amber-200 px-3 py-1 rounded-md text-xs font-semibold">Material: {product.material || "Multi-material"}</span>
                        {product.brand && <span class="bg-sky-50 text-sky-700 border border-sky-200 px-3 py-1 rounded-md text-xs font-semibold">Brand: {product.brand}</span>}
                    </div>
                </div>
            </div>

            <h2 class="text-lg font-bold text-gray-900 pt-4">⚖️ Variant Cross-Comparison & Supplier Cost Matrix</h2>
            
            <div class="space-y-4">
                {product.variants?.map((v, idx) => (
                    <div key={v.id} class="bg-white rounded-xl shadow-xs border border-gray-200 overflow-hidden">
                        <div class="bg-gray-50 px-4 py-3 border-b border-gray-200 flex justify-between items-center">
                            <span class="font-semibold text-sm text-gray-800">Variant #{idx + 1}: <span class="text-indigo-600 uppercase">{v.color}</span> / Size: <span class="text-indigo-600 font-bold">{v.size}</span></span>
                            <span class="text-xs text-gray-400 font-mono">ID: {v.id.substring(0,8)}...</span>
                        </div>
                        <table class="w-full text-left text-xs md:text-sm">
                            <thead class="bg-gray-100/50 text-gray-600 uppercase font-medium border-b border-gray-200">
                                <tr>
                                    <th class="px-4 py-3">Connected Vendor</th>
                                    <th class="px-4 py-3">Vendor SKU</th>
                                    <th class="px-4 py-3 text-center">Available Stock</th>
                                    <th class="px-4 py-3 text-right">Base Tier Unit Price</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-gray-100">
                                {v.offers?.map(o => (
                                    <tr key={o.id} class="hover:bg-indigo-50/20 transition-all">
                                        <td class="px-4 py-3 font-semibold text-gray-700">{o.supplier}</td>
                                        <td class="px-4 py-3 font-mono text-gray-500">{o.supplier_sku}</td>
                                        <td class="px-4 py-3 text-center">
                                            <span class={`px-2 py-0.5 rounded font-bold ${o.stock > 0 ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'}`}>
                                                {o.stock} pcs
                                            </span>
                                        </td>
                                        <td class="px-4 py-3 text-right font-bold text-gray-900">
                                            {o.pricing_tiers?.[0] ? `€${o.pricing_tiers[0].price.toFixed(2)}` : "N/A"}
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
// WORK ITEM 9.3: DATA QUALITY ANALYTICS DASHBOARD VIEW
// =========================================================================
function QualityDashboardView() {
    const [metrics, setMetrics] = useState(null);
    const [quality, setQuality] = useState(null);

    useEffect(() => {
        Promise.all([
            fetch(`${API_BASE_URL}/metrics`).then(res => res.json()),
            fetch(`${API_BASE_URL}/quality`).then(res => res.json())
        ]).then(([m, q]) => {
            setMetrics(m);
            setQuality(q);
            // Build the analytical chart view via raw DOM binding callback context
            setTimeout(() => renderAnalyticsChart(q), 100);
        }).catch(err => console.error("Error initializing metrics dashboard:", err));
    }, []);

    const renderAnalyticsChart = (qualityData) => {
        const ctx = document.getElementById('qualityChartCanvas');
        if (!ctx) return;
        
        // Destructure existing global active chart contexts to prevent overlapping memory errors
        if (window.activeChartInstance) window.activeChartInstance.destroy();

        window.activeChartInstance = new Chart(ctx, {
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
                plugins: {
                    legend: { position: 'bottom', labels: { font: { size: 12 } } }
                }
            }
        });
    };

    if (!metrics || !quality) return <div class="text-center py-20 text-gray-500 font-medium text-sm">Aggregating platform metrics charts...</div>;

    return (
        <div class="space-y-6 animate-fade-in">
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div class="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm">
                    <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Master Unified Products</p>
                    <p class="text-3xl font-extrabold text-gray-900 pt-1">{metrics.total_harmonized_products}</p>
                </div>
                <div class="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm">
                    <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Resolved Variant Specifications</p>
                    <p class="text-3xl font-extrabold text-indigo-600 pt-1">{metrics.total_resolved_variants}</p>
                </div>
                <div class="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm">
                    <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Integrated Supplier Offers</p>
                    <p class="text-3xl font-extrabold text-amber-500 pt-1">{metrics.total_supplier_offers}</p>
                </div>
                <div class="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm">
                    <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Overall Sync Quality Score</p>
                    <p class="text-3xl font-extrabold text-emerald-600 pt-1">{quality.overall_harmonisation_quality}</p>
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="bg-white p-6 rounded-2xl border border-gray-100 shadow-md flex flex-col items-center justify-center">
                    <h3 class="text-sm font-bold text-gray-800 pb-4 text-center">Visual Category Harmonisation Breakdown</h3>
                    <div class="relative w-full h-56">
                        <canvas id="qualityChartCanvas"></canvas>
                    </div>
                </div>
                <div class="bg-white p-6 rounded-2xl border border-gray-100 shadow-md md:col-span-2 space-y-4">
                    <h3 class="text-sm font-bold text-gray-800 border-b border-gray-100 pb-2">Normalization Data Statistics</h3>
                    <div class="divide-y divide-gray-100 text-sm space-y-3">
                        <div class="flex justify-between items-center pt-2">
                            <span class="text-gray-500 font-medium">Total Evaluated Records</span>
                            <span class="font-bold text-gray-900">{quality.total_records_evaluated}</span>
                        </div>
                        <div class="flex justify-between items-center pt-3">
                            <span class="text-gray-500 font-medium">Successfully Mapped Rows</span>
                            <span class="font-bold text-indigo-600">{quality.successfully_categorized}</span>
                        </div>
                        <div class="flex justify-between items-center pt-3">
                            <span class="text-gray-500 font-medium">Flagged & Isolated Records (Category Fragmentation)</span>
                            <span class="font-bold text-rose-500">{quality.flagged_uncategorized_records}</span>
                        </div>
                    </div>
                    <div class="bg-indigo-50 p-4 rounded-xl border border-indigo-100 text-xs text-indigo-800 leading-relaxed">
                        💡 <strong>Engine Note:</strong> The flagged uncategorized records represent raw feed data that lacked taxonomy rules. The pipeline safely encapsulated them under <em>"Uncategorized"</em> to guarantee zero data loss during high-velocity cloud streaming.
                    </div>
                </div>
            </div>
        </div>
    );
}