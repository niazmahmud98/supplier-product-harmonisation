const { useState, useEffect } = React;

function App() {
    const [activeTab, setActiveTab] = useState('catalogue');
    const [selectedProductId, setSelectedProductId] = useState(null);

    // Navigation function to drill down into a product detail view
    const viewProductDetails = (id) => {
        setSelectedProductId(id);
        setActiveTab('detail');
    };

    return (
        <div class="min-h-screen flex flex-col">
            {/* Top Corporate Navigation Header */}
            <header class="bg-indigo-900 text-white shadow-md px-6 py-4 flex justify-between items-center">
                <div class="flex items-center space-x-3">
                    <span class="text-2xl font-bold tracking-wider">Endeavour Sync</span>
                    <span class="bg-indigo-700 text-xs px-2 py-1 rounded text-indigo-200">Phase 9 Live</span>
                </div>
                <nav class="flex space-x-2">
                    <button 
                        onClick={() => setActiveTab('catalogue')} 
                        class={`px-4 py-2 rounded-md font-medium text-sm transition-all ${activeTab === 'catalogue' ? 'bg-indigo-700 text-white' : 'text-indigo-200 hover:bg-indigo-800'}`}>
                        📦 Catalogue UI
                    </button>
                    <button 
                        onClick={() => setActiveTab('dashboard')} 
                        class={`px-4 py-2 rounded-md font-medium text-sm transition-all ${activeTab === 'dashboard' ? 'bg-indigo-700 text-white' : 'text-indigo-200 hover:bg-indigo-800'}`}>
                        📊 Quality Dashboard
                    </button>
                </nav>
            </header>

            {/* Dynamic Core Workspace View Layer */}
            <main class="flex-1 p-6 max-w-7xl w-full mx-auto">
                {activeTab === 'catalogue' && <CatalogueView onProductClick={viewProductDetails} />}
                {activeTab === 'detail' && <ProductDetailView productId={selectedProductId} onBack={() => setActiveTab('catalogue')} />}
                {activeTab === 'dashboard' && <QualityDashboardView />}
            </main>

            <footer class="bg-gray-100 text-center py-4 text-xs text-gray-500 border-t border-gray-200">
                &copy; 2026 Endeavour Harmonisation Engine. Built with React.js & FastAPI.
            </footer>
        </div>
    );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);