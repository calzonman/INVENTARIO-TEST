<script lang="ts">
  import { onMount } from 'svelte';
  import { fade, fly } from 'svelte/transition';
  import { 
    Package, AlertTriangle, TrendingUp, DollarSign, 
    ArrowUpRight, ArrowDownRight, Activity,
    CalendarX, Clock // Nuevos iconos para vencimientos
  } from 'lucide-svelte';
  import { products, movements, lots, currentTenant, loadAllLots } from '../stores/store';

  // Cargar lotes al montar el dashboard
  onMount(() => {
    loadAllLots();
  });

  // --- CÁLCULOS REACTIVOS (Business Intelligence) ---
  
  // 1. Estadísticas Generales
  $: tenantProducts = $products.filter(p => p.tenantId === $currentTenant.id);
  $: tenantMovements = $movements.filter(m => m.tenantId === $currentTenant.id);
  
  $: stats = {
    totalProducts: tenantProducts.length,
    lowStockItems: tenantProducts.filter(p => p.currentStock < p.minStock).length,
    totalValue: tenantProducts.reduce((sum, p) => sum + (p.currentStock * p.unitPrice), 0),
    movementsToday: tenantMovements.filter(m => {
        const today = new Date().toISOString().split('T')[0];
        return m.timestamp.startsWith(today);
    }).length
  };

  // 2. Datos para Gráfica de Categorías
  $: categoryData = Object.entries(
    tenantProducts.reduce((acc, p) => {
      acc[p.category] = (acc[p.category] || 0) + p.currentStock;
      return acc;
    }, {} as Record<string, number>)
  ).sort((a, b) => b[1] - a[1]).slice(0, 5);
  
  $: maxCategoryVal = Math.max(...categoryData.map(d => d[1]), 1);

  // 3. Alertas de Stock Crítico
  $: lowStockList = tenantProducts
    .filter(p => p.currentStock < p.minStock)
    .sort((a, b) => (a.currentStock / a.minStock) - (b.currentStock / b.minStock))
    .slice(0, 5);

  // 4. Actividad Reciente
  $: recentActivity = [...tenantMovements].sort((a, b) => 
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  ).slice(0, 5);

  // --- NUEVA LÓGICA: GESTIÓN DE VENCIMIENTOS (FEFO) ---
  
  // Helper para obtener nombre del producto desde el ID del lote
  const getProductName = (productId: string) => {
      const p = $products.find(p => p.id === productId);
      return p ? p.name : 'Producto desconocido';
  };

  const today = new Date();
  today.setHours(0, 0, 0, 0); // Normalizar a medianoche

  const nextWeek = new Date(today);
  nextWeek.setDate(today.getDate() + 7); // Umbral de 7 días

  // Filtrar lotes del tenant actual que tengan stock
  $: tenantLots = $lots.filter(l => l.tenantId === $currentTenant.id && l.quantity > 0);

  // A) Lotes Vencidos (Fecha < Hoy)
  $: expiredLots = tenantLots.filter(l => {
      const exp = new Date(l.expiryDate);
      return exp < today;
  });

  // B) Lotes Por Vencer (Hoy <= Fecha <= 7 días)
  $: expiringSoonLots = tenantLots.filter(l => {
      const exp = new Date(l.expiryDate);
      return exp >= today && exp <= nextWeek;
  });

</script>

<div class="space-y-6 animate-in fade-in duration-500 pb-10">
  
  <div>
    <h1 class="text-2xl font-semibold text-slate-900">Dashboard</h1>
    <p class="text-slate-600">Visión general del inventario: {$currentTenant.name}</p>
  </div>

  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
    <div class="bg-white p-6 rounded-lg border border-slate-200 shadow-sm flex justify-between items-start">
      <div>
        <p class="text-sm font-medium text-slate-500">Total Productos</p>
        <h3 class="text-2xl font-bold text-slate-900 mt-1">{stats.totalProducts}</h3>
      </div>
      <div class="p-3 bg-blue-50 text-blue-600 rounded-lg">
        <Package class="w-5 h-5" />
      </div>
    </div>

    <div class="bg-white p-6 rounded-lg border border-slate-200 shadow-sm flex justify-between items-start">
      <div>
        <p class="text-sm font-medium text-slate-500">Alertas Stock</p>
        <h3 class="text-2xl font-bold text-slate-900 mt-1">{stats.lowStockItems}</h3>
      </div>
      <div class="p-3 bg-red-50 text-red-600 rounded-lg">
        <AlertTriangle class="w-5 h-5" />
      </div>
    </div>

    <div class="bg-white p-6 rounded-lg border border-slate-200 shadow-sm flex justify-between items-start">
      <div>
        <p class="text-sm font-medium text-slate-500">Movimientos Hoy</p>
        <h3 class="text-2xl font-bold text-slate-900 mt-1">{stats.movementsToday}</h3>
      </div>
      <div class="p-3 bg-green-50 text-green-600 rounded-lg">
        <Activity class="w-5 h-5" />
      </div>
    </div>

    <div class="bg-white p-6 rounded-lg border border-slate-200 shadow-sm flex justify-between items-start">
      <div>
        <p class="text-sm font-medium text-slate-500">Valor Total</p>
        <h3 class="text-2xl font-bold text-slate-900 mt-1">
            ${stats.totalValue.toLocaleString('es-CL')}
        </h3>
      </div>
      <div class="p-3 bg-purple-50 text-purple-600 rounded-lg">
        <DollarSign class="w-5 h-5" />
      </div>
    </div>
  </div>

  {#if expiredLots.length > 0 || expiringSoonLots.length > 0}
  <div class="grid grid-cols-1 md:grid-cols-2 gap-6" in:fade>
      
      <div class="bg-white rounded-lg border border-red-200 shadow-sm overflow-hidden relative">
          <div class="absolute top-0 left-0 w-1 h-full bg-red-500"></div>
          <div class="p-4 border-b border-red-100 bg-red-50/50 flex items-center gap-2">
              <CalendarX class="w-5 h-5 text-red-600" />
              <h3 class="text-lg font-semibold text-red-900">Lotes Vencidos (Retirar)</h3>
              <span class="ml-auto bg-red-200 text-red-800 text-xs px-2 py-1 rounded-full font-bold">
                  {expiredLots.length}
              </span>
          </div>
          <div class="divide-y divide-slate-100 max-h-60 overflow-y-auto">
              {#each expiredLots as lot}
                  <div class="p-3 hover:bg-red-50 transition-colors flex justify-between items-center">
                      <div>
                          <p class="font-medium text-slate-900">{getProductName(lot.productId)}</p>
                          <p class="text-xs text-red-600 font-mono">Lote: {lot.number}</p>
                      </div>
                      <div class="text-right">
                          <p class="text-sm font-bold text-slate-700">{lot.quantity} und.</p>
                          <p class="text-xs text-red-500">Venció: {new Date(lot.expiryDate).toLocaleDateString('es-CL')}</p>
                      </div>
                  </div>
              {/each}
          </div>
      </div>

      <div class="bg-white rounded-lg border border-yellow-200 shadow-sm overflow-hidden relative">
          <div class="absolute top-0 left-0 w-1 h-full bg-yellow-400"></div>
          <div class="p-4 border-b border-yellow-100 bg-yellow-50/50 flex items-center gap-2">
              <Clock class="w-5 h-5 text-yellow-600" />
              <h3 class="text-lg font-semibold text-yellow-900">Vencen en 7 días</h3>
              <span class="ml-auto bg-yellow-200 text-yellow-800 text-xs px-2 py-1 rounded-full font-bold">
                  {expiringSoonLots.length}
              </span>
          </div>
          <div class="divide-y divide-slate-100 max-h-60 overflow-y-auto">
              {#each expiringSoonLots as lot}
                  <div class="p-3 hover:bg-yellow-50 transition-colors flex justify-between items-center">
                      <div>
                          <p class="font-medium text-slate-900">{getProductName(lot.productId)}</p>
                          <p class="text-xs text-slate-500 font-mono">Lote: {lot.number}</p>
                      </div>
                      <div class="text-right">
                          <p class="text-sm font-bold text-slate-700">{lot.quantity} und.</p>
                          <p class="text-xs text-yellow-600 font-medium">
                              {new Date(lot.expiryDate).toLocaleDateString('es-CL')}
                          </p>
                      </div>
                  </div>
              {:else}
                  <div class="p-8 text-center text-slate-400 text-sm">
                      No hay lotes próximos a vencer.
                  </div>
              {/each}
          </div>
      </div>
  </div>
  {/if}

  <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
    
    <div class="lg:col-span-2 space-y-6">
        <div class="bg-white p-6 rounded-lg border border-slate-200 shadow-sm">
            <h3 class="text-lg font-semibold mb-4 text-slate-800">Stock por Categoría</h3>
            {#if categoryData.length === 0}
                <div class="h-48 flex items-center justify-center text-slate-400">Sin datos suficientes</div>
            {:else}
                <div class="space-y-3">
                    {#each categoryData as [cat, val], i}
                        <div in:fly={{ x: -20, delay: i * 50 }}>
                            <div class="flex justify-between text-sm mb-1">
                                <span class="font-medium text-slate-700">{cat}</span>
                                <span class="text-slate-500">{val} und.</span>
                            </div>
                            <div class="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                                <div 
                                    class="bg-blue-600 h-2.5 rounded-full transition-all duration-1000 ease-out" 
                                    style="width: {(val / maxCategoryVal) * 100}%"
                                ></div>
                            </div>
                        </div>
                    {/each}
                </div>
            {/if}
        </div>

        <div class="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
            <div class="p-6 border-b border-slate-100 flex items-center gap-2">
                <AlertTriangle class="w-5 h-5 text-red-500" />
                <h3 class="text-lg font-semibold text-slate-800">Productos con Stock Crítico</h3>
            </div>
            <div class="divide-y divide-slate-100">
                {#each lowStockList as product}
                    <div class="p-4 flex items-center justify-between hover:bg-slate-50">
                        <div>
                            <p class="font-medium text-slate-900">{product.name}</p>
                            <p class="text-xs text-slate-500">Min: {product.minStock} | SKU: {product.sku}</p>
                        </div>
                        <div class="text-right">
                             <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                {product.currentStock} und.
                            </span>
                        </div>
                    </div>
                {:else}
                    <div class="p-8 text-center text-slate-500 text-sm">
                        Todo en orden. No hay alertas de stock bajo.
                    </div>
                {/each}
            </div>
        </div>
    </div>

    <div class="bg-white rounded-lg border border-slate-200 shadow-sm flex flex-col h-full">
        <div class="p-6 border-b border-slate-100 flex items-center gap-2">
            <TrendingUp class="w-5 h-5 text-slate-500" />
            <h3 class="text-lg font-semibold text-slate-800">Actividad Reciente</h3>
        </div>
        <div class="flex-1 overflow-y-auto max-h-[500px] p-2">
            {#each recentActivity as movement (movement.id)}
                <div class="flex items-start gap-3 p-3 hover:bg-slate-50 rounded-lg transition-colors" in:fade>
                    <div class={`mt-1 p-2 rounded-full ${movement.type === 'in' ? 'bg-green-100 text-green-600' : 'bg-orange-100 text-orange-600'}`}>
                        {#if movement.type === 'in'}
                            <ArrowUpRight class="w-4 h-4" />
                        {:else}
                            <ArrowDownRight class="w-4 h-4" />
                        {/if}
                    </div>
                    <div class="flex-1 min-w-0">
                        <p class="text-sm font-medium text-slate-900 truncate">{movement.productName}</p>
                        <p class="text-xs text-slate-500">
                            {new Date(movement.timestamp).toLocaleTimeString('es-CL', {hour: '2-digit', minute:'2-digit'})} 
                            · {movement.userName}
                        </p>
                    </div>
                    <span class={`text-sm font-bold ${movement.type === 'in' ? 'text-green-600' : 'text-orange-600'}`}>
                        {movement.type === 'in' ? '+' : '-'}{movement.quantity}
                    </span>
                </div>
            {:else}
                <div class="p-8 text-center text-slate-500 text-sm">
                    No hay movimientos registrados aún.
                </div>
            {/each}
        </div>
    </div>

  </div>
</div>