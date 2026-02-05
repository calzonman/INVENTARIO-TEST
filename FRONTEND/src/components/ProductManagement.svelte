<script lang="ts">
  import { fade, slide, scale } from 'svelte/transition';
  import { Plus, Search, Edit, Trash2, FileDown, AlertTriangle, X, PackageCheck, QrCode, Download, Printer, CheckCircle2 } from 'lucide-svelte'; // Añadí iconos
  import QRCode from 'qrcode'; // <--- IMPORTANTE: Librería QR
  import { 
    products, 
    lots, 
    currentTenant, 
    addProduct,     
    deleteProduct,
    createLot,
    pendingBarcode,
    type Product 
  } from '../stores/store';

  // --- ESTADOS LOCALES ---
  let searchTerm = '';
  let categoryFilter = 'all';
  
  // Control de Modales
  let isAddDialogOpen = false;
  let isEditDialogOpen = false;
  let isQrModalOpen = false; // <--- NUEVO: Modal de QR generado
  
  let selectedProduct: Product | null = null;
  let isSubmitting = false;

  // Datos para el QR generado
  let generatedQrUrl = '';
  let generatedQrLabel = '';

  // Lógica de Lotes en Formulario
  let hasInitialLot = false; 
  let lotMode: 'new' | 'existing' = 'new'; 
  
  let formData = {
    sku: '', barcode: '', name: '', description: '', category: '',
    location: '', currentStock: 0, minStock: 5, unitPrice: 0,
    lotNumber: '', lotExpiry: ''
  };

  // --- AUTO-APERTURA SI VIENE DEL ESCÁNER ---
  $: if ($pendingBarcode) {
      resetForm();
      formData.barcode = $pendingBarcode;
      formData.sku = $pendingBarcode; 
      isAddDialogOpen = true;
      pendingBarcode.set(null); 
  }

  // --- COMPUTADOS ---
  $: uniqueExistingLots = Array.from(new Set($lots.map(l => l.number))).map(num => {
      const lot = $lots.find(l => l.number === num);
      return { number: num, expiry: lot?.expiryDate || '' };
  });

  $: categories = Array.from(new Set($products.map(p => p.category)));
  
  $: filteredProducts = $products.filter(product => {
    if (product.tenantId !== $currentTenant.id) return false;
    const matchesSearch = 
      product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      product.sku.toLowerCase().includes(searchTerm.toLowerCase()) ||
      product.barcode.includes(searchTerm);
    const matchesCategory = categoryFilter === 'all' || product.category === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  // --- ACCIONES ---
  function resetForm() {
    formData = {
      sku: '', barcode: '', name: '', description: '', category: '',
      location: '', currentStock: 0, minStock: 5, unitPrice: 0,
      lotNumber: '', lotExpiry: ''
    };
    hasInitialLot = false;
    lotMode = 'new';
  }

  function handleExistingLotSelect(e: any) {
      const selectedNum = e.target.value;
      const found = uniqueExistingLots.find(l => l.number === selectedNum);
      if (found) {
          formData.lotNumber = found.number;
          formData.lotExpiry = found.expiry; 
      }
  }

  // --- NUEVA FUNCIÓN: GENERAR QR ---
  async function generateProductQR(barcode: string, lot: string, date: string) {
      try {
          // Formato solicitado: "codigo/lote/fecha"
          // Si no hay lote, solo usamos el código
          const qrData = (lot && date) 
            ? `${barcode}/${lot}/${date}` 
            : barcode;
            
          generatedQrLabel = (lot && date) 
            ? `LOTE: ${lot} | VENCE: ${date}` 
            : `SKU: ${barcode}`;

          // Generar Data URL (imagen en base64)
          generatedQrUrl = await QRCode.toDataURL(qrData, {
              width: 300,
              margin: 2,
              color: {
                  dark: '#000000',
                  light: '#ffffff'
              }
          });
          isQrModalOpen = true; // Abrir modal de éxito
      } catch (err) {
          console.error(err);
      }
  }

  async function handleAddProduct() {
    if (isSubmitting) return;
    isSubmitting = true;

    // Guardamos valores temporales para el QR antes de resetear
    const tempBarcode = formData.barcode;
    const tempLot = hasInitialLot ? formData.lotNumber : '';
    const tempExpiry = hasInitialLot ? formData.lotExpiry : '';

    try {
        const createdProduct = await addProduct({
            sku: formData.sku,
            barcode: formData.barcode,
            name: formData.name,
            description: formData.description,
            category: formData.category,
            currentStock: formData.currentStock,
            minStock: formData.minStock,
            unitPrice: formData.unitPrice,
            location: formData.location,
            tenantId: $currentTenant.id,
            trackBatches: true 
        });

        if (hasInitialLot && formData.lotNumber && formData.lotExpiry) {
             await createLot({
                productId: createdProduct.id,
                productSku: createdProduct.sku,
                number: formData.lotNumber,
                quantity: formData.currentStock,
                expiryDate: formData.lotExpiry,
                tenantId: $currentTenant.id
             });
        }
        
        isAddDialogOpen = false;
        
        // --- AQUÍ LA MAGIA: Generar QR al finalizar ---
        await generateProductQR(tempBarcode, tempLot, tempExpiry);

        resetForm();
    } catch (error) {
        alert("Error: " + error);
    } finally {
        isSubmitting = false;
    }
  }

  async function handleDeleteProduct(id: string) {
    await deleteProduct(id);
  }

  function openEdit(product: Product) {
    selectedProduct = product;
    formData = { ...product, lotNumber: '', lotExpiry: '' };
    isEditDialogOpen = true;
  }
  
  function handleEditProduct() {
     alert("Edición de producto pendiente...");
     isEditDialogOpen = false;
  }

  function downloadQR() {
      const link = document.createElement('a');
      link.download = `QR-${formData.sku || 'producto'}.png`;
      link.href = generatedQrUrl;
      link.click();
  }

  function exportProducts() {
    /* ... (lógica existente de exportación) ... */
    const headers = ['SKU', 'Código', 'Nombre', 'Categoría', 'Stock', 'Ubicación', 'Precio'];
    const rows = filteredProducts.map(p => [ p.sku, p.barcode, p.name, p.category, p.currentStock, p.location, p.unitPrice ]);
    const csvContent = [headers, ...rows].map(e => e.join(",")).join("\n");
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `productos.csv`;
    link.click();
  }
</script>

<div class="space-y-6 animate-in fade-in duration-500">
  <div class="flex items-center justify-between flex-wrap gap-4">
    <div>
      <h1 class="text-2xl font-semibold text-slate-900">Gestión de Productos</h1>
      <p class="text-slate-600">Administre el catálogo de productos</p>
    </div>
    <div class="flex gap-2">
      <button on:click={exportProducts} class="px-4 py-2 border border-slate-300 rounded-md hover:bg-slate-50 flex items-center gap-2 text-sm font-medium">
        <FileDown class="w-4 h-4" /> Exportar
      </button>
      <button on:click={() => { resetForm(); isAddDialogOpen = true; }} class="px-4 py-2 bg-slate-900 text-white rounded-md hover:bg-slate-800 flex items-center gap-2 text-sm font-medium">
        <Plus class="w-4 h-4" /> Nuevo Producto
      </button>
    </div>
  </div>

  <div class="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
       <div class="relative">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <input type="text" bind:value={searchTerm} placeholder="Buscar por nombre, SKU o código..." class="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-slate-900" />
      </div>
      <select bind:value={categoryFilter} class="w-full px-3 py-2 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-slate-900 bg-white">
         <option value="all">Todas las categorías</option>
        {#each categories as cat} <option value={cat}>{cat}</option> {/each}
      </select>
    </div>
  </div>

  <div class="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
     <table class="w-full text-sm text-left">
        <thead class="bg-slate-50 text-slate-600 border-b border-slate-200">
          <tr>
             <th class="px-6 py-3 font-medium">SKU</th>
             <th class="px-6 py-3 font-medium">Producto</th>
             <th class="px-6 py-3 font-medium">Categoría</th>
             <th class="px-6 py-3 font-medium">Stock Total</th>
             <th class="px-6 py-3 font-medium">Ubicación</th>
             <th class="px-6 py-3 font-medium">Precio</th>
             <th class="px-6 py-3 font-medium text-right">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          {#each filteredProducts as product (product.id)}
            <tr class="hover:bg-slate-50">
              <td class="px-6 py-4 font-medium text-slate-900">{product.sku}</td>
              <td class="px-6 py-4">
                  <div>
                      <p class="font-medium text-slate-900">{product.name}</p>
                      <p class="text-xs text-slate-500">{product.barcode}</p>
                  </div>
              </td>
              <td class="px-6 py-4"><span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-800 border border-slate-200">{product.category}</span></td>
              <td class="px-6 py-4">
                <div class="flex items-center gap-2">
                  <span class={product.currentStock < product.minStock ? 'text-red-600 font-bold' : ''}>{product.currentStock}</span>
                  {#if product.currentStock < product.minStock} <AlertTriangle class="w-4 h-4 text-red-600" /> {/if}
                </div>
              </td>
              <td class="px-6 py-4">{product.location}</td>
              <td class="px-6 py-4">${product.unitPrice}</td>
              <td class="px-6 py-4 text-right">
                <div class="flex justify-end gap-2">
                    <button on:click={() => openEdit(product)} class="p-1 hover:bg-slate-200 rounded text-slate-500"><Edit class="w-4 h-4"/></button>
                    <button on:click={() => handleDeleteProduct(product.id)} class="p-1 hover:bg-red-50 rounded text-red-600"><Trash2 class="w-4 h-4"/></button>
                </div>
              </td>
            </tr>
          {:else}
            <tr><td colspan="7" class="px-6 py-12 text-center text-slate-500">No se encontraron productos</td></tr>
          {/each}
        </tbody>
     </table>
  </div>

  {#if isAddDialogOpen || isEditDialogOpen}
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm" transition:fade>
      <div class="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto" transition:slide>
        <div class="flex items-center justify-between p-6 border-b">
          <h2 class="text-xl font-semibold">{isAddDialogOpen ? 'Nuevo Producto' : 'Editar Producto'}</h2>
          <button on:click={() => { isAddDialogOpen = false; isEditDialogOpen = false; }} class="p-2 hover:bg-slate-100 rounded-full"><X class="w-5 h-5" /></button>
        </div>
        
        <div class="p-6 space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-2">
              <label class="text-sm font-medium">SKU *</label>
              <input type="text" bind:value={formData.sku} class="w-full border rounded-md p-2" placeholder="Ej: PROD-001" />
            </div>
            <div class="space-y-2">
              <label class="text-sm font-medium">Código Barras *</label>
              <input type="text" bind:value={formData.barcode} class="w-full border rounded-md p-2" />
            </div>
          </div>
          
          <div class="space-y-2">
            <label class="text-sm font-medium">Nombre *</label>
            <input type="text" bind:value={formData.name} class="w-full border rounded-md p-2" />
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-2">
              <label class="text-sm font-medium">Categoría *</label>
              <input type="text" bind:value={formData.category} class="w-full border rounded-md p-2" />
            </div>
            <div class="space-y-2">
              <label class="text-sm font-medium">Ubicación *</label>
              <input type="text" bind:value={formData.location} class="w-full border rounded-md p-2" />
            </div>
          </div>

          <div class="grid grid-cols-3 gap-4">
            <div class="space-y-2">
              <label class="text-sm font-medium">Stock Inicial</label>
              <input type="number" bind:value={formData.currentStock} class="w-full border rounded-md p-2" />
            </div>
            <div class="space-y-2">
              <label class="text-sm font-medium">Stock Mínimo</label>
              <input type="number" bind:value={formData.minStock} class="w-full border rounded-md p-2" />
            </div>
            <div class="space-y-2">
              <label class="text-sm font-medium">Precio Unit.</label>
              <input type="number" bind:value={formData.unitPrice} class="w-full border rounded-md p-2" />
            </div>
          </div>

          {#if isAddDialogOpen}
              <div class="border-t border-slate-200 pt-4 mt-2">
                  <div class="flex items-center justify-between mb-3">
                      <div class="flex items-center gap-2">
                          <input type="checkbox" id="initLot" bind:checked={hasInitialLot} class="rounded text-indigo-600 focus:ring-indigo-500 w-4 h-4" />
                          <label for="initLot" class="text-sm font-semibold text-slate-900 cursor-pointer">Asignar Lote Inicial</label>
                      </div>
                      
                      {#if hasInitialLot}
                          <div class="flex bg-slate-100 rounded-lg p-1 text-xs font-medium">
                              <button 
                                  class="px-3 py-1 rounded {lotMode === 'new' ? 'bg-white shadow text-indigo-700' : 'text-slate-500'}"
                                  on:click={() => lotMode = 'new'}
                              >Nuevo Lote</button>
                              <button 
                                  class="px-3 py-1 rounded {lotMode === 'existing' ? 'bg-white shadow text-indigo-700' : 'text-slate-500'}"
                                  on:click={() => lotMode = 'existing'}
                              >Usar Existente</button>
                          </div>
                      {/if}
                  </div>

                  {#if hasInitialLot}
                    <div class="bg-indigo-50/50 border border-indigo-100 p-4 rounded-md space-y-4" transition:slide>
                        {#if lotMode === 'new'}
                            <div class="grid grid-cols-2 gap-4">
                                <div class="space-y-2">
                                    <label class="text-xs font-medium text-indigo-900">Nro. Nuevo Lote</label>
                                    <input type="text" bind:value={formData.lotNumber} class="w-full border border-indigo-200 rounded p-2 text-sm focus:ring-indigo-500" placeholder="Ej: L-2026-X" />
                                </div>
                                <div class="space-y-2">
                                    <label class="text-xs font-medium text-indigo-900">Vencimiento</label>
                                    <input type="date" bind:value={formData.lotExpiry} class="w-full border border-indigo-200 rounded p-2 text-sm focus:ring-indigo-500" />
                                </div>
                            </div>
                        {:else}
                            <div class="grid grid-cols-2 gap-4">
                                <div class="space-y-2">
                                    <label class="text-xs font-medium text-indigo-900">Seleccionar Lote</label>
                                    <select 
                                        class="w-full border border-indigo-200 rounded p-2 text-sm focus:ring-indigo-500 bg-white"
                                        on:change={handleExistingLotSelect}
                                    >
                                        <option value="">-- Buscar Lote --</option>
                                        {#each uniqueExistingLots as lot}
                                            <option value={lot.number}>{lot.number} (Vence: {new Date(lot.expiry).toLocaleDateString()})</option>
                                        {/each}
                                    </select>
                                </div>
                                <div class="space-y-2">
                                    <label class="text-xs font-medium text-indigo-900">Vencimiento (Auto)</label>
                                    <input type="date" value={formData.lotExpiry ? new Date(formData.lotExpiry).toISOString().split('T')[0] : ''} disabled class="w-full border border-slate-200 bg-slate-100 text-slate-500 rounded p-2 text-sm cursor-not-allowed" />
                                </div>
                            </div>
                        {/if}
                        
                        <div class="flex items-start gap-2 text-indigo-600">
                             <PackageCheck class="w-4 h-4 mt-0.5" />
                             <p class="text-xs">
                                Se asignarán las <strong>{formData.currentStock}</strong> unidades del stock inicial a este lote {lotMode === 'new' ? 'nuevo' : 'existente'}.
                             </p>
                        </div>
                    </div>
                  {/if}
              </div>
          {/if}
        </div>

        <div class="p-6 border-t bg-slate-50 flex justify-end gap-3">
          <button on:click={() => { isAddDialogOpen = false; isEditDialogOpen = false; }} class="px-4 py-2 border rounded-md hover:bg-white">Cancelar</button>
          <button on:click={isAddDialogOpen ? handleAddProduct : handleEditProduct} class="px-4 py-2 bg-slate-900 text-white rounded-md hover:bg-slate-800">
            {isAddDialogOpen ? 'Guardar Producto' : 'Guardar Cambios'}
          </button>
        </div>
      </div>
    </div>
  {/if}

  {#if isQrModalOpen}
    <div class="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm" transition:fade>
        <div class="bg-white rounded-lg shadow-2xl w-full max-w-sm overflow-hidden" transition:scale>
            <div class="bg-green-600 p-4 text-white flex justify-between items-center">
                <h3 class="font-bold flex items-center gap-2"><CheckCircle2 class="w-5 h-5" /> Producto Creado</h3>
                <button on:click={() => isQrModalOpen = false} class="hover:bg-green-700 p-1 rounded-full"><X class="w-5 h-5"/></button>
            </div>
            
            <div class="p-6 flex flex-col items-center text-center">
                <p class="text-slate-600 text-sm mb-4">La etiqueta QR ha sido generada con el formato de trazabilidad.</p>
                
                <div class="bg-white border-2 border-slate-900 p-2 rounded-lg mb-2">
                    <img src={generatedQrUrl} alt="QR Code" class="w-48 h-48" />
                </div>
                
                <p class="font-mono text-xs text-slate-500 bg-slate-100 px-2 py-1 rounded mb-6 break-all">
                    {generatedQrLabel}
                </p>

                <div class="grid grid-cols-2 gap-3 w-full">
                    <button on:click={downloadQR} class="flex items-center justify-center gap-2 bg-slate-900 text-white py-2 rounded hover:bg-slate-800 text-sm font-medium">
                        <Download class="w-4 h-4" /> Descargar
                    </button>
                    <button on:click={() => window.print()} class="flex items-center justify-center gap-2 border border-slate-300 text-slate-700 py-2 rounded hover:bg-slate-50 text-sm font-medium">
                        <Printer class="w-4 h-4" /> Imprimir
                    </button>
                </div>
            </div>
        </div>
    </div>
  {/if}
</div>