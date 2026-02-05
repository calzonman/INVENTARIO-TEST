<script lang="ts">
  import { onMount } from 'svelte';
  import { fade, slide } from 'svelte/transition';
  import { Tags, Plus, Search, Calendar, AlertTriangle, PackageCheck } from 'lucide-svelte';
  import { 
    lots, products, currentTenant, 
    loadLotsByProduct, createLot, 
    type Product 
  } from '../stores/store'; // Asegúrate de tener loadLotsByProduct exportado en store

  // --- ESTADO LOCAL ---
  let searchTerm = '';
  let selectedProductFilter = 'all';
  let isCreateDialogOpen = false;
  
  // Estado para formulario de creación
  let newLot = {
    productId: '',
    number: '',
    quantity: 0,
    expiryDate: ''
  };

  // --- CARGA DE DATOS ---
  // Nota: Para este MVP cargamos lotes iterando productos o necesitaríamos un endpoint "loadAllLots".
  // Por simplicidad, filtraremos visualmente, asumiendo que el usuario busca por producto.
  
  let allLotsDisplay: any[] = [];

  // Función auxiliar para cargar lotes de todos los productos (Simulada para MVP)
  async function loadAllSystemLots() {
    // Si tu store tiene una función loadAllLots úsala, si no, iteramos productos cargados
    // Idealmente agregas "export const loadLots = ..." en store.ts que llame a /lots/?tenant_id=...
    // Aquí usaremos una lógica reactiva simple si ya tienes los lotes en el store $lots
    // Si $lots está vacío, disparar carga:
    
    // TRUCO PROVISIONAL: Vamos a buscar lotes de todos los productos en lista
    // (Lo ideal es agregar loadLots() global en store.ts, ver abajo)
  }

  // --- FILTROS ---
  $: filteredLots = $lots.filter(lot => {
    const matchSearch = lot.number.toLowerCase().includes(searchTerm.toLowerCase()) || 
                        lot.productSku.toLowerCase().includes(searchTerm.toLowerCase());
    const matchProduct = selectedProductFilter === 'all' || lot.productId === selectedProductFilter;
    return matchSearch && matchProduct;
  });

  // --- ACCIONES ---
  async function handleCreateLot() {
    if(!newLot.productId || !newLot.number || !newLot.expiryDate) {
        alert("Complete todos los campos"); return;
    }
    const selectedProd = $products.find(p => p.id === newLot.productId);
    
    try {
        await createLot({
            productId: newLot.productId,
            productSku: selectedProd?.sku || 'UNK',
            number: newLot.number,
            quantity: newLot.quantity,
            expiryDate: newLot.expiryDate,
            tenantId: $currentTenant.id
        });
        isCreateDialogOpen = false;
        // Reset form
        newLot = { productId: '', number: '', quantity: 0, expiryDate: '' };
    } catch(e) {
        alert("Error creando lote: " + e);
    }
  }

  // Helper para estado de fecha
  function getExpiryStatus(dateStr: string) {
    const today = new Date();
    const expiry = new Date(dateStr);
    const diffTime = expiry.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays < 0) return { color: 'text-red-600 bg-red-50', text: 'VENCIDO' };
    if (diffDays < 30) return { color: 'text-orange-600 bg-orange-50', text: 'POR VENCER' };
    return { color: 'text-green-600 bg-green-50', text: 'VIGENTE' };
  }
</script>

<div class="space-y-6 animate-in fade-in duration-500">
  <div class="flex items-center justify-between flex-wrap gap-4">
    <div>
      <h1 class="text-2xl font-semibold text-slate-900">Gestión de Lotes</h1>
      <p class="text-slate-600">Monitoreo de vencimientos y trazabilidad</p>
    </div>
    <button 
      on:click={() => isCreateDialogOpen = true}
      class="px-4 py-2 bg-slate-900 text-white rounded-md hover:bg-slate-800 flex items-center gap-2 text-sm font-medium"
    >
      <Plus class="w-4 h-4" /> Crear Lote Manual
    </button>
  </div>

  <div class="bg-white p-4 rounded-lg border border-slate-200 shadow-sm grid grid-cols-1 md:grid-cols-2 gap-4">
    <div class="relative">
      <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
      <input 
        type="text" 
        bind:value={searchTerm}
        placeholder="Buscar por Nro Lote o SKU..." 
        class="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-slate-900"
      />
    </div>
    <select bind:value={selectedProductFilter} class="border border-slate-200 rounded-md px-3 py-2 bg-white">
        <option value="all">Todos los productos</option>
        {#each $products.filter(p => p.trackBatches) as prod}
            <option value={prod.id}>{prod.name} ({prod.sku})</option>
        {/each}
    </select>
  </div>

  <div class="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
    <table class="w-full text-sm text-left">
        <thead class="bg-slate-50 text-slate-600 border-b">
            <tr>
                <th class="px-6 py-3 font-medium">Lote</th>
                <th class="px-6 py-3 font-medium">Producto</th>
                <th class="px-6 py-3 font-medium">Stock Lote</th>
                <th class="px-6 py-3 font-medium">Vencimiento</th>
                <th class="px-6 py-3 font-medium">Estado</th>
            </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
            {#each filteredLots as lot (lot.id)}
                {@const status = getExpiryStatus(lot.expiryDate)}
                <tr class="hover:bg-slate-50">
                    <td class="px-6 py-4 font-bold text-slate-700">{lot.number}</td>
                    <td class="px-6 py-4">
                        <p class="font-medium text-slate-900">
                            {$products.find(p => p.id === lot.productId)?.name || 'Producto Desconocido'}
                        </p>
                        <p class="text-xs text-slate-500">{lot.productSku}</p>
                    </td>
                    <td class="px-6 py-4">
                        <div class="flex items-center gap-2">
                            <PackageCheck class="w-4 h-4 text-slate-400" />
                            <span class="text-lg font-semibold">{lot.quantity}</span>
                        </div>
                    </td>
                    <td class="px-6 py-4">
                        <div class="flex items-center gap-2">
                            <Calendar class="w-4 h-4 text-slate-400" />
                            <span>{new Date(lot.expiryDate).toLocaleDateString()}</span>
                        </div>
                    </td>
                    <td class="px-6 py-4">
                        <span class={`px-2 py-1 rounded-full text-xs font-bold ${status.color}`}>
                            {status.text}
                        </span>
                    </td>
                </tr>
            {:else}
                <tr>
                    <td colspan="5" class="px-6 py-12 text-center text-slate-500">
                        No hay lotes registrados o activos.
                    </td>
                </tr>
            {/each}
        </tbody>
    </table>
  </div>

  {#if isCreateDialogOpen}
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm" transition:fade>
        <div class="bg-white rounded-lg shadow-xl w-full max-w-md p-6" transition:slide>
            <h2 class="text-xl font-bold mb-4">Registrar Nuevo Lote</h2>
            
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium mb-1">Producto</label>
                    <select bind:value={newLot.productId} class="w-full border rounded p-2">
                        <option value="">-- Seleccionar --</option>
                        {#each $products.filter(p => p.trackBatches) as prod}
                            <option value={prod.id}>{prod.name} ({prod.sku})</option>
                        {/each}
                    </select>
                </div>

                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium mb-1">Nro. Lote</label>
                        <input type="text" bind:value={newLot.number} class="w-full border rounded p-2" placeholder="Ej: L-001" />
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-1">Cantidad Inicial</label>
                        <input type="number" bind:value={newLot.quantity} class="w-full border rounded p-2" />
                    </div>
                </div>

                <div>
                    <label class="block text-sm font-medium mb-1">Fecha Vencimiento</label>
                    <input type="date" bind:value={newLot.expiryDate} class="w-full border rounded p-2" />
                </div>
            </div>

            <div class="mt-6 flex justify-end gap-3">
                <button on:click={() => isCreateDialogOpen = false} class="px-4 py-2 border rounded hover:bg-slate-50">Cancelar</button>
                <button on:click={handleCreateLot} class="px-4 py-2 bg-slate-900 text-white rounded hover:bg-slate-800">Guardar</button>
            </div>
        </div>
    </div>
  {/if}
</div>