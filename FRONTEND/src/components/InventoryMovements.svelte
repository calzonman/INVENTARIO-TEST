<script lang="ts">
  import { slide, fade } from 'svelte/transition';
  import { 
    History, ArrowUpRight, ArrowDownRight, RefreshCw, 
    FileDown, Filter, Calendar, Search, Hash 
  } from 'lucide-svelte';
  import { movements, currentTenant } from '../stores/store';

  // --- ESTADOS LOCALES ---
  let searchTerm = '';
  let typeFilter = 'all'; // 'all', 'in', 'out', 'adjustment'
  let dateFilter = 'all'; // 'all', 'today', 'week', 'month'

  // --- LÓGICA DE FILTRADO ---
  $: tenantMovements = $movements.filter(m => m.tenantId === $currentTenant.id);
  $: filteredMovements = tenantMovements.filter(movement => {
    // 1. Filtro de Texto (Producto, SKU, Usuario, Lote)
    const searchLower = searchTerm.toLowerCase();
    const matchesSearch =
      movement.productName.toLowerCase().includes(searchLower) ||
      movement.productSku.toLowerCase().includes(searchLower) ||
      movement.userName.toLowerCase().includes(searchLower) ||
      (movement.batchNumber && movement.batchNumber.toLowerCase().includes(searchLower)); // Búsqueda por lote también

    // 2. Filtro de Tipo
    const matchesType = typeFilter === 'all' || movement.type === typeFilter;

    // 3. Filtro de Fecha
    let matchesDate = true;
    if (dateFilter !== 'all') {
      const movementDate = new Date(movement.timestamp);
      const today = new Date();
      today.setHours(0,0,0,0);
      
      if (dateFilter === 'today') {
        const mDate = new Date(movement.timestamp);
        mDate.setHours(0,0,0,0);
        matchesDate = mDate.getTime() === today.getTime();
      } else if (dateFilter === 'week') {
        const weekAgo = new Date(today);
        weekAgo.setDate(weekAgo.getDate() - 7);
        matchesDate = movementDate >= weekAgo;
      } else if (dateFilter === 'month') {
        const monthAgo = new Date(today);
        monthAgo.setMonth(monthAgo.getMonth() - 1);
        matchesDate = movementDate >= monthAgo;
      }
    }

    return matchesSearch && matchesType && matchesDate;
  });

  // --- EXPORTAR ---
  const exportMovements = () => {
    // Actualizamos cabeceras para incluir Lote
    const headers = ['Fecha', 'Producto', 'SKU', 'Lote', 'Vencimiento', 'Tipo', 'Cantidad', 'Stock Anterior', 'Stock Nuevo', 'Usuario', 'Ubicación'];
    
    const rows = filteredMovements.map(m => [
      new Date(m.timestamp).toLocaleString('es-CL'),
      m.productName,
      m.productSku,
      m.batchNumber || '-', // Campo Lote
      m.expirationDate ? new Date(m.expirationDate).toLocaleDateString('es-CL') : '-', // Campo Vencimiento
      m.type === 'in' ? 'Entrada' : m.type === 'out' ? 'Salida' : 'Ajuste',
      m.quantity,
      m.previousStock,
      m.newStock,
      m.userName,
      m.location
    ]);

    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `movimientos-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  // --- UI HELPERS ---
  const getBadgeClass = (type: string) => {
    switch (type) {
      case 'in': return 'bg-green-100 text-green-700 border-green-200';
      case 'out': return 'bg-orange-100 text-orange-700 border-orange-200';
      default: return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  const getIcon = (type: string) => {
    switch (type) {
        case 'in': return ArrowUpRight;
        case 'out': return ArrowDownRight;
        default: return RefreshCw;
    }
  };
</script>

<div class="space-y-6 animate-in fade-in duration-500 pb-10">
  
  <div class="flex items-center justify-between flex-wrap gap-4">
    <div>
      <h1 class="text-2xl font-semibold text-primary">Movimientos de Inventario</h1>
      <p class="text-muted-foreground">Historial auditable de todas las transacciones</p>
    </div>
    <button on:click={exportMovements} class="px-4 py-2 border border-border bg-card hover:bg-accent rounded-md flex items-center gap-2 text-sm font-medium transition-colors">
      <FileDown class="w-4 h-4" /> Exportar
    </button>
  </div>

  <div class="bg-card p-4 rounded-lg border border-border shadow-sm">
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
     
      <div class="relative">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <input 
          type="text" 
          bind:value={searchTerm}
          placeholder="Buscar producto, SKU, lote o usuario..." 
          class="w-full pl-10 pr-4 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </div>
  
      <div class="relative">
        <select 
          bind:value={typeFilter}
          class="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-ring appearance-none"
        >
          <option value="all">Todos los tipos</option>
          <option value="in">Entradas</option>
          <option value="out">Salidas</option>
          <option value="adjustment">Ajustes</option>
        </select>
        <Filter class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
      </div>

      <div class="relative">
        <select 
          bind:value={dateFilter}
          class="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-ring appearance-none"
        >
          <option value="all">Todo el historial</option>
          <option value="today">Hoy</option>
          <option value="week">Última semana</option>
          <option value="month">Último mes</option>
        </select>
        <Calendar class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
      </div>
    </div>
  </div>

  <div class="bg-card rounded-lg border border-border shadow-sm overflow-hidden">
    <div class="p-6 border-b border-border">
        <h3 class="flex items-center gap-2 font-semibold text-card-foreground">
            <History class="w-5 h-5" />
            Historial ({filteredMovements.length})
        </h3>
    </div>
    <div class="overflow-x-auto">
      <table class="w-full text-sm text-left">
        <thead class="bg-muted text-muted-foreground border-b border-border">
          <tr>
            <th class="px-6 py-3 font-medium">Fecha y Hora</th>
            <th class="px-6 py-3 font-medium">Producto</th>
            <th class="px-6 py-3 font-medium">Lote / Venc.</th> <th class="px-6 py-3 font-medium">Tipo</th>
            <th class="px-6 py-3 font-medium">Cantidad</th>
            <th class="px-6 py-3 font-medium">Stock</th>
            <th class="px-6 py-3 font-medium">Usuario</th>
            <th class="px-6 py-3 font-medium">Ubicación</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-border">
          {#each filteredMovements as movement (movement.id)}
            <tr transition:slide|local class="hover:bg-accent/50 transition-colors">
              
              <td class="px-6 py-4">
                <div class="flex items-center gap-2">
                    <Calendar class="w-4 h-4 text-muted-foreground" />
                    <div>
                        <p class="font-medium text-foreground">
                            {new Date(movement.timestamp).toLocaleDateString('es-CL')}
                        </p>
                        <p class="text-xs text-muted-foreground">
                            {new Date(movement.timestamp).toLocaleTimeString('es-CL', {hour: '2-digit', minute:'2-digit'})}
                        </p>
                    </div>
                </div>
              </td>

              <td class="px-6 py-4">
                <div>
                  <p class="font-medium text-foreground">{movement.productName}</p>
                  <p class="text-xs text-muted-foreground">{movement.productSku}</p>
                </div>
              </td>

              <td class="px-6 py-4">
                {#if movement.batchNumber}
                    <div class="flex flex-col items-start gap-1">
                        <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-100">
                            <Hash class="w-3 h-3" /> {movement.batchNumber}
                        </span>
                        {#if movement.expirationDate}
                            <span class="text-[10px] text-slate-500 flex items-center gap-1">
                                <Calendar class="w-3 h-3" /> 
                                {new Date(movement.expirationDate).toLocaleDateString('es-CL')}
                            </span>
                        {/if}
                    </div>
                {:else}
                    <span class="text-xs text-muted-foreground ml-2">-</span>
                {/if}
              </td>

              <td class="px-6 py-4">
                <span class={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${getBadgeClass(movement.type)}`}>
                    <svelte:component this={getIcon(movement.type)} class="w-3 h-3" />
                    {movement.type === 'in' ? 'Entrada' : movement.type === 'out' ? 'Salida' : 'Ajuste'}
                </span>
              </td>

              <td class="px-6 py-4">
                <span class={`font-bold ${movement.type === 'in' ? 'text-green-600' : movement.type === 'out' ? 'text-orange-600' : 'text-foreground'}`}>
                    {movement.type === 'in' ? '+' : movement.type === 'out' ? '-' : '±'}
                    {Math.abs(movement.quantity)}
                </span>
              </td>

              <td class="px-6 py-4">
                <div class="text-xs">
                    <span class="text-muted-foreground">{movement.previousStock}</span>
                    <span class="mx-1">→</span>
                    <span class="font-medium text-foreground">{movement.newStock}</span>
                </div>
              </td>

              <td class="px-6 py-4 text-foreground">{movement.userName}</td>

              <td class="px-6 py-4">
                <span class="px-2 py-1 rounded text-xs border border-border bg-background text-muted-foreground">
                    {movement.location}
                </span>
              </td>

            </tr>
          {:else}
            <tr>
              <td colspan="8" class="px-6 py-16 text-center text-muted-foreground"> <div class="flex flex-col items-center gap-2">
                    <History class="w-8 h-8 opacity-20" />
                    <p>No se encontraron movimientos con los filtros actuales</p>
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </div>
</div>