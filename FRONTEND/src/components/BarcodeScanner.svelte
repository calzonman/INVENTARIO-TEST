<script lang="ts">
  import { onDestroy } from 'svelte';
  import { Html5Qrcode } from 'html5-qrcode';
  import { 
    ScanBarcode, Plus, Minus, CheckCircle2, XCircle, Package, 
    AlertCircle, ArrowRight, Camera, Keyboard, StopCircle
  } from 'lucide-svelte';
  import { fade, scale, slide } from 'svelte/transition';
  import { 
    products, getProductByBarcode, addMovement, 
    createLot, loadLotsByProduct, 
    currentUser, currentTenant, type Lot,
    pendingBarcode, activeView 
  } from '../stores/store';
  import { lastScannedCode } from '../lib/hidScanner';

  // --- ESTADOS LOCALES ---
  let barcode = '';
  let scannedProduct: any = null;
  let quantity = 1;
  let scanResult: 'success' | 'error' | 'not_found' | null = null;
  
  // ESTADO DE MODO DE ESCANEO
  let scanMode: 'hid' | 'camera' = 'hid'; 
  let html5QrCode: Html5Qrcode | null = null; 

  // ESTADOS DE LOTE
  let activeLots: Lot[] = [];
  let selectedLotId = '';
  let isCreatingNewLot = false;
  let newLotNumber = '';
  let newLotExpiry = '';
  let isIncoming = true;

  // NUEVO: Bandera de bloqueo por QR
  let isLotLocked = false;

  // Reactividad
  $: requiresBatchInfo = scannedProduct?.trackBatches;

  // --- HID SCANNER (LISTENER GLOBAL) ---
  const unsubscribeHid = lastScannedCode.subscribe(code => {
    if (code) {
      if (scanMode === 'camera') stopCamera(); 
      scanMode = 'hid';
      barcode = code;
      handleScan();
      lastScannedCode.set('');
    }
  });

  onDestroy(() => {
    unsubscribeHid();
    stopCamera(); 
  });

  // --- LÓGICA CÁMARA (QR) ---
  async function startCamera() {
    console.log("Iniciando cámara...");
    scanMode = 'camera';
    
    setTimeout(async () => {
        if (html5QrCode) return; 

        try {
            html5QrCode = new Html5Qrcode("reader");
            const config = { fps: 10, qrbox: { width: 250, height: 250 } };
            
            await html5QrCode.start(
                { facingMode: "environment" }, 
                config,
                (decodedText) => {
                    console.log(`Código leído: ${decodedText}`);
                    barcode = decodedText;
                    stopCamera(); 
                    scanMode = 'hid'; 
                    handleScan(); 
                },
                (errorMessage) => { /* Ignorar errores por frame */ }
            );
        } catch (err) {
            console.error("Error iniciando cámara:", err);
            alert("No se pudo iniciar la cámara. Asegúrese de usar HTTPS o Localhost.");
            scanMode = 'hid';
        }
    }, 100);
  }

  async function stopCamera() {
    if (html5QrCode) {
        try {
            await html5QrCode.stop();
            html5QrCode.clear();
        } catch (e) { console.log("Cámara ya detenida"); }
        html5QrCode = null;
    }
  }

  function switchMode(mode: 'hid' | 'camera') {
      console.log("Cambiando modo a:", mode);
      if (mode === 'camera') {
          startCamera();
      } else {
          stopCamera();
          scanMode = 'hid';
      }
  }

  // --- LÓGICA DE PROCESAMIENTO ---
  async function handleScan() {
    let rawCode = barcode.trim();
    if (!rawCode) return;
    
    scanResult = null;
    isLotLocked = false; // Resetear bandera de bloqueo
    
    let searchCode = rawCode;
    let detectedLot = '';
    let detectedExpiry = '';

    // Detección QR Compuesto (SKU/LOTE/FECHA)
    if (rawCode.includes('/')) {
        const parts = rawCode.split('/');
        if (parts.length >= 1) searchCode = parts[0]; 
        if (parts.length >= 2) {
            detectedLot = parts[1];
            isLotLocked = true; // Activar bloqueo si viene lote en QR
        }
        if (parts.length >= 3) detectedExpiry = parts[2];
    }

    try {
        const product = await getProductByBarcode(searchCode);
        if (product) {
            scannedProduct = product;
            scanResult = 'success';
            quantity = 1;
            
            if (product.trackBatches) {
                activeLots = await loadLotsByProduct(product.id);
                selectedLotId = ''; 
                isCreatingNewLot = false;

                if (detectedLot) {
                    const existingLot = activeLots.find(l => l.number === detectedLot);
                    if (existingLot) {
                        selectedLotId = existingLot.id;
                    } else {
                        // Lote no existe, forzar creación para entrada
                        isIncoming = true;
                        isCreatingNewLot = true;
                        newLotNumber = detectedLot;
                        newLotExpiry = detectedExpiry;
                    }
                } else {
                    // Escaneo normal (sin lote en código)
                    // Si no es entrada y hay lotes, sugerir el primero (FEFO habitual)
                    if (!isIncoming && activeLots.length > 0) {
                        selectedLotId = activeLots[0].id;
                    }
                }
            }
        } else {
            barcode = searchCode;
            scannedProduct = null;
            scanResult = 'not_found';
        }
    } catch (error) {
        console.error("Error al escanear:", error);
        scanResult = 'error';
    } finally {
        if (scanResult === 'success') {
             setTimeout(() => { scanResult = null; barcode = ''; }, 1500);
        } else if (scanResult === 'error') {
             setTimeout(() => { scanResult = null; barcode = ''; }, 2000);
        }
    }
  }

  function handleCreateFromScan() {
      if (!barcode) return;
      pendingBarcode.set(barcode);
      activeView.set('products');
  }

  async function handleStockMovement(type: 'in' | 'out') {
      if (!scannedProduct) return;
      isIncoming = (type === 'in');
      let finalLotId = selectedLotId;

      if (scannedProduct.trackBatches) {
        if (type === 'in') {
            if (isCreatingNewLot) {
                if (!newLotNumber || !newLotExpiry) { 
                    alert("Complete los datos del nuevo lote");
                    return; 
                }
                try {
                    const created = await createLot({
                        productId: scannedProduct.id,
                        productSku: scannedProduct.sku,
                        number: newLotNumber,
                        quantity: 0,
                        expiryDate: newLotExpiry,
                        tenantId: $currentTenant.id
                    });
                    // @ts-ignore
                    finalLotId = created._id || created.id; 
                } catch (e) { 
                    alert("Error creando el lote"); return;
                }
            } else {
                if (!finalLotId) { 
                    alert("Seleccione un lote existente o cree uno nuevo");
                    return; 
                }
            }
        } else {
            if (!finalLotId) { 
                alert("Debe seleccionar un lote para descontar stock");
                return; 
            }
            const lot = activeLots.find(l => l.id === finalLotId);
            if (lot && lot.quantity < quantity) { 
                alert(`El lote ${lot.number} solo tiene ${lot.quantity} unidades.`); return;
            }
        }
      } else {
        if (type === 'out' && scannedProduct.currentStock < quantity) { 
            alert("Stock global insuficiente");
            return; 
        }
      }

      try {
        await addMovement({
            tenantId: $currentTenant.id,
            productId: scannedProduct.id,
            productName: scannedProduct.name,
            productSku: scannedProduct.sku,
            type: type,
            quantity: quantity,
            userId: $currentUser?.id || 'sys',
            userName: $currentUser?.name || 'Sistema',
            location: scannedProduct.location
        }, finalLotId);
        
        handleScan(); // Refrescar estado post-movimiento
        quantity = 1; newLotNumber = ''; newLotExpiry = ''; isCreatingNewLot = false;
      } catch (error) { 
          alert("Error al registrar: " + error);
      }
  }
</script>

<div class="space-y-6 animate-in fade-in duration-500">
  <div>
    <h1 class="text-2xl mb-1 font-semibold text-slate-900">Control de Inventario</h1>
    <p class="text-slate-600">Gestión de stock mediante Códigos de Barra o QR</p>
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    
    <div class="bg-white rounded-lg border border-slate-200 shadow-sm h-fit overflow-hidden">
      
      <div class="flex border-b border-slate-100 relative z-10">
          <button 
            type="button" 
            class="flex-1 py-4 flex items-center justify-center gap-2 font-medium transition-colors {scanMode === 'hid' ? 'bg-indigo-50 text-indigo-700 border-b-2 border-indigo-600' : 'text-slate-500 hover:bg-slate-50'}"
            on:click={() => switchMode('hid')}
          >
              <Keyboard class="w-5 h-5" /> Teclado / USB
          </button>
          <button 
             type="button" 
            class="flex-1 py-4 flex items-center justify-center gap-2 font-medium transition-colors {scanMode === 'camera' ? 'bg-indigo-50 text-indigo-700 border-b-2 border-indigo-600' : 'text-slate-500 hover:bg-slate-50'}"
            on:click={() => switchMode('camera')}
          >
              <Camera class="w-5 h-5" /> Cámara QR
          </button>
      </div>

      <div class="p-6 min-h-[300px] flex flex-col justify-center relative">
        
        {#if scanMode === 'hid'}
             <form on:submit|preventDefault={handleScan} in:fade>
                <div class="relative">
                    <input
                        type="text"
                        bind:value={barcode}
                        placeholder="Clic aquí y escanee..."
                        class="w-full pl-4 pr-12 py-3 border rounded-md text-lg focus:ring-2 focus:ring-indigo-500 outline-none shadow-sm"
                        autofocus
                    />
                    {#if scanResult}
                        <div class="absolute right-3 top-1/2 -translate-y-1/2" in:scale>
                            {#if scanResult === 'success'}
                                 <CheckCircle2 class="w-6 h-6 text-green-600" />
                            {:else if scanResult === 'error'}
                                 <XCircle class="w-6 h-6 text-red-600" />
                             {:else if scanResult === 'not_found'}
                                 <AlertCircle class="w-6 h-6 text-orange-500" />
                            {/if}
                        </div>
                    {/if}
                </div>
                <p class="text-xs text-slate-400 mt-2 text-center">
                    Use su lector de código de barras USB o escriba manualmente.
                </p>
            </form>
        {:else}
            <div in:fade class="flex flex-col items-center w-full">
                <div id="reader" class="w-full h-[250px] bg-black rounded-lg overflow-hidden relative border border-slate-300">
                    {#if !html5QrCode}
                         <div class="absolute inset-0 flex items-center justify-center text-slate-400">
                             <p class="text-xs">Iniciando cámara...</p>
                        </div>
                     {/if}
                 </div>
                
                <div class="mt-4 text-center space-y-2">
                    <p class="text-xs text-slate-500">
                        Apunte la cámara al código QR o de Barras.
                    </p>
                    <button 
                        type="button"
                        on:click={() => switchMode('hid')}
                        class="text-xs text-red-600 underline"
                     >
                        Cancelar / Detener Cámara
                    </button>
                </div>
            </div>
        {/if}

        {#if scanResult === 'not_found'}
            <div class="mt-4 p-4 bg-orange-50 border border-orange-100 rounded-lg animate-in slide-in-from-top-2">
                <div class="flex items-start gap-3">
                    <AlertCircle class="w-5 h-5 text-orange-600 mt-0.5" />
                    <div class="flex-1">
                         <h4 class="font-semibold text-orange-800 text-sm">Producto No Registrado</h4>
                        <p class="text-xs text-orange-600 mt-1">El código <strong>{barcode}</strong> no existe.</p>
                        <button 
                             type="button" 
                            on:click={handleCreateFromScan}
                            class="mt-3 w-full flex items-center justify-center gap-2 bg-orange-600 text-white py-2 rounded text-sm font-medium hover:bg-orange-700 transition"
                        >
                            Crear Producto con este Código <ArrowRight class="w-4 h-4" />
                        </button>
                    </div>
                </div>
             </div>
        {/if}

      </div>
    </div>

    <div class="bg-white rounded-lg border border-slate-200 shadow-sm min-h-[400px]">
      <div class="p-6 border-b border-slate-100">
        <h3 class="font-semibold text-lg">Detalle Operación</h3>
      </div>
      
      <div class="p-6">
        {#if !scannedProduct}
            <div class="text-center py-12 text-slate-500">
                <Package class="w-12 h-12 mx-auto mb-3 opacity-20" />
                <p>Esperando lectura...</p>
            </div>
        {:else}
             <div class="space-y-6" in:fade>
                <div class="flex justify-between items-start">
                     <div>
                        <h2 class="text-xl font-bold text-slate-900">{scannedProduct.name}</h2>
                        <p class="text-sm text-slate-500">{scannedProduct.sku}</p>
                    </div>
                    <div class="text-right">
                        <p class="text-xs text-slate-400 uppercase">Stock Global</p>
                        <p class="text-2xl font-bold text-slate-800">{scannedProduct.currentStock}</p>
                    </div>
                </div>

                <div class="flex items-center justify-center gap-4 bg-slate-50 p-3 rounded-lg">
                    <button type="button" class="p-2 hover:bg-white rounded shadow-sm" on:click={() => quantity = Math.max(1, quantity - 1)}>
                        <Minus class="w-5 h-5" />
                    </button>
                    <input type="number" bind:value={quantity} class="w-20 text-center text-xl font-bold bg-transparent border-none" />
                    <button type="button" class="p-2 hover:bg-white rounded shadow-sm" on:click={() => quantity++}>
                        <Plus class="w-5 h-5" />
                    </button>
                </div>

                {#if scannedProduct.trackBatches}
                    <div class="border border-indigo-100 rounded-lg overflow-hidden" transition:slide>
                        
                        <div class="bg-indigo-50 p-3 flex gap-4 text-sm font-medium">
                            <button type="button" class="flex-1 py-1 rounded {isIncoming ? 'bg-white shadow text-indigo-700' : 'text-slate-500'}" on:click={() => isIncoming = true}>Entrada</button>
                            <button type="button" class="flex-1 py-1 rounded {!isIncoming ? 'bg-white shadow text-indigo-700' : 'text-slate-500'}" on:click={() => isIncoming = false}>Salida</button>
                        </div>
                        
                        <div class="p-4 space-y-4">
                            
                            {#if isLotLocked}
                                <div class="bg-blue-50 border border-blue-200 rounded p-4 text-center">
                                    <p class="text-xs text-blue-600 font-bold uppercase tracking-wider mb-2">
                                        🔒 Lote Detectado (QR)
                                    </p>
                                    
                                    {#if isCreatingNewLot}
                                        <div class="mb-2">
                                            <span class="text-xl font-bold text-slate-800">{newLotNumber}</span>
                                            <span class="block text-xs text-slate-500 mt-1">Nuevo Lote (Se creará auto)</span>
                                        </div>
                                        <div class="text-sm text-slate-600 bg-white/60 p-2 rounded inline-block border border-blue-100">
                                            Vencimiento: <strong>{newLotExpiry || 'Sin fecha'}</strong>
                                        </div>
                                    {:else}
                                        {@const lockedLot = activeLots.find(l => l.id === selectedLotId)}
                                        <div class="mb-2">
                                            <span class="text-xl font-bold text-slate-800">{lockedLot?.number || 'Lote Desconocido'}</span>
                                        </div>
                                        <div class="flex justify-center gap-3 text-xs">
                                            <span class="bg-blue-100 text-blue-800 px-2 py-1 rounded border border-blue-200">
                                                Stock: {lockedLot?.quantity || 0}
                                            </span>
                                            <span class="bg-blue-100 text-blue-800 px-2 py-1 rounded border border-blue-200">
                                                Vence: {lockedLot?.expiryDate ? new Date(lockedLot.expiryDate).toLocaleDateString() : '-'}
                                            </span>
                                        </div>
                                    {/if}
                                </div>

                            {:else}
                                {#if isIncoming}
                                    <div class="flex items-center gap-2 mb-2">
                                        <input type="checkbox" id="newLot" bind:checked={isCreatingNewLot} class="rounded text-indigo-600" />
                                        <label for="newLot" class="text-sm font-medium">Crear Nuevo Lote</label>
                                    </div>
                                    {#if isCreatingNewLot}
                                        <div class="grid grid-cols-2 gap-3" transition:slide>
                                            <div>
                                                <label class="text-xs font-bold text-slate-500">Nro Lote</label>
                                                <input type="text" bind:value={newLotNumber} class="w-full text-sm border rounded p-1.5" placeholder="L-..." />
                                            </div>
                                            <div>
                                                <label class="text-xs font-bold text-slate-500">Vence</label>
                                                <input type="date" bind:value={newLotExpiry} class="w-full text-sm border rounded p-1.5" />
                                            </div>
                                        </div>
                                    {:else}
                                        <div>
                                            <label class="text-xs font-bold text-slate-500 mb-1 block">Sumar a Lote Existente</label>
                                            <select bind:value={selectedLotId} class="w-full text-sm border rounded p-2">
                                                <option value="">-- Seleccionar Lote --</option>
                                                {#each activeLots as lot}
                                                    <option value={lot.id}>{lot.number} (Vence: {new Date(lot.expiryDate).toLocaleDateString()})</option>
                                                {/each}
                                            </select>
                                        </div>
                                    {/if}
                                {:else}
                                    <div>
                                        <label class="text-xs font-bold text-slate-500 mb-1 block">Descontar de Lote (FEFO Sugerido)</label>
                                        <select bind:value={selectedLotId} class="w-full text-sm border rounded p-2 bg-orange-50 border-orange-200">
                                            {#each activeLots as lot}
                                                <option value={lot.id}>{lot.number} | Stock: {lot.quantity} | Vence: {new Date(lot.expiryDate).toLocaleDateString()}</option>
                                            {:else}
                                                <option value="">No hay lotes con stock</option>
                                            {/each}
                                        </select>
                                    </div>
                                {/if}
                            {/if}

                            {#if isIncoming}
                                <button type="button" class="w-full py-3 bg-green-600 text-white rounded font-bold hover:bg-green-700 mt-2" on:click={() => handleStockMovement('in')}>CONFIRMAR ENTRADA</button>
                            {:else}
                                <button type="button" class="w-full py-3 bg-orange-600 text-white rounded font-bold hover:bg-orange-700 mt-2" on:click={() => handleStockMovement('out')}>CONFIRMAR SALIDA</button>
                            {/if}
                        </div>
                    </div>
                {:else}
                    <div class="grid grid-cols-2 gap-3">
                         <button type="button" class="py-3 bg-green-600 text-white rounded font-bold hover:bg-green-700" on:click={() => handleStockMovement('in')}>ENTRADA</button>
                         <button type="button" class="py-3 bg-orange-600 text-white rounded font-bold hover:bg-orange-700" on:click={() => handleStockMovement('out')}>SALIDA</button>
                    </div>
                {/if}
            </div>
        {/if}
      </div>
    </div>
  </div>
</div>