const { useState } = React;

function App() {
    // Active View States: 'CATALOGUE', 'DETAIL', 'QUALITY', 'BI_INSIGHTS'
    const [currentView, setCurrentView] = useState('CATALOGUE');
    const [selectedProductId, setSelectedProductId] = useState(null);

    const navigateToDetail = (productId) => {
        setSelectedProductId(productId);
        setCurrentView('DETAIL');
    };

    return (
        <div class="min-h-screen bg-gray-50 flex flex-col">
            {/* GLOBAL ENTERPRISE TOP NAVIGATION BAR */}
            <header class="bg-indigo-900 text-white shadow-md sticky top-0 z-50">
                <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
                    <div class="flex items-center gap-2 cursor-pointer" onClick={() => setCurrentView('CATALOGUE')}>
                        <span class="text-xl">⚙️</span>
                        <h1 class="text-lg font-bold tracking-tight">Endeavour Sync <span class="text-xs font-normal text-indigo-300">v1.0</span></h1>
                    </div>
                    
                    <nav class="flex items-center gap-2">
                        <button 
                            onClick={() => setCurrentView('CATALOGUE')}
                            class={`font-semibold text-xs px-4 py-2 rounded-lg transition-all ${currentView === 'CATALOGUE' || currentView === 'DETAIL' ? 'bg-indigo-700 text-white' : 'text-indigo-200 hover:bg-indigo-800'}`}>
                            📦 Catalogue UI
                        </button>
                        <button 
                            onClick={() => setCurrentView('QUALITY')}
                            class={`font-semibold text-xs px-4 py-2 rounded-lg transition-all ${currentView === 'QUALITY' ? 'bg-indigo-700 text-white' : 'text-indigo-200 hover:bg-indigo-800'}`}>
                            🏥 Quality Health
                        </button>
                        <button 
                            onClick={() => setCurrentView('BI_INSIGHTS')}
                            class={`font-semibold text-xs px-4 py-2 rounded-lg transition-all flex items-center gap-1.5 ${currentView === 'BI_INSIGHTS' ? 'bg-indigo-600 text-white shadow-inner border border-indigo-400/30' : 'bg-indigo-950/40 hover:bg-indigo-800 text-white'}`}>
                            📊 BI Insights
                        </button>
                    </nav>
                </div>
            </header>

            {/* REACT RENDERING PORTAL ENGINE */}
            <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {currentView === 'CATALOGUE' && (
                    <CatalogueView onProductClick={navigateToDetail} />
                )}
                
                {currentView === 'DETAIL' && (
                    <ProductDetailView 
                        productId={selectedProductId} 
                        onBack={() => setCurrentView('CATALOGUE')} 
                    />
                )}

                {currentView === 'QUALITY' && (
                    <QualityDashboardView />
                )}

                {currentView === 'BI_INSIGHTS' && (
                    <BIInsightsView />
                )}
            </main>

            <footer class="bg-white border-t border-gray-100 py-4 text-center text-xs text-gray-400 font-medium">
                Enterprise Business Intelligence Layer Portfolio Staging Environment • 2026
            </footer>
        </div>
    );
}

// Bind to root element inside index.html
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);