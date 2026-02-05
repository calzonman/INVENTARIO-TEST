<script lang="ts">
  import { fade } from 'svelte/transition';
  import { Settings as SettingsIcon, Building2, MapPin, Palette, Save, Plus, Trash2, Check } from 'lucide-svelte';
  
  // Importamos acciones reales
  import { 
    currentTenant, 
    locations, 
    addLocation, 
    deleteLocation 
  } from '../stores/store';

  // ... (Estados locales) ...
  let tenantForm = { ...$currentTenant };
  let newLocation = { code: '', name: '', description: '' };
  let isAddingLocation = false;
  let preferences = { defaultMinStock: 10, lowStockThreshold: 20, enableScanSound: true, autoFocusScanner: true };

  // --- ACCIONES ACTUALIZADAS ---
  function saveTenantSettings() {
    // En MVP esto sigue siendo local porque no hicimos endpoint PATCH /tenants
    currentTenant.set({ ...tenantForm });
    alert("Configuración de empresa guardada (Localmente)");
  }

  // AHORA ES ASYNC
  async function handleAddLocation() {
    if (!newLocation.code || !newLocation.name) return;
    try {
      await addLocation({
          ...newLocation,
          tenantId: $currentTenant.id
      });
      newLocation = { code: '', name: '', description: '' };
      isAddingLocation = false;
    } catch (e) {
      alert(e);
    }
  }

  async function handleDeleteLocation(id: string) {
      if(confirm('¿Eliminar ubicación?')) {
          await deleteLocation(id);
      }
  }
  
  // ... resto del script ...
</script>

<div class="space-y-8 animate-in fade-in duration-500 pb-10">
  
  <div>
    <h1 class="text-2xl font-semibold text-primary">Configuración</h1>
    <p class="text-muted-foreground">Administre la identidad y reglas de su empresa</p>
  </div>

  <div class="bg-card rounded-lg border border-border shadow-sm overflow-hidden">
    <div class="p-6 border-b border-border">
        <h3 class="flex items-center gap-2 font-semibold text-card-foreground">
            <Palette class="w-5 h-5 text-muted-foreground" />
            Marca e Identidad
        </h3>
        <p class="text-sm text-muted-foreground mt-1">Configure cómo se ve su empresa en el sistema</p>
    </div>
    <div class="p-6 space-y-4 max-w-2xl">
        <div class="space-y-2">
            <label class="text-sm font-medium">Nombre de la Empresa</label>
            <input type="text" bind:value={tenantForm.name} class="w-full px-3 py-2 bg-background border border-border rounded-md focus:ring-2 focus:ring-primary focus:outline-none" />
        </div>
        
        <div class="space-y-2">
            <label class="text-sm font-medium">Industria / Rubro</label>
            <input type="text" bind:value={tenantForm.industry} class="w-full px-3 py-2 bg-background border border-border rounded-md focus:ring-2 focus:ring-primary focus:outline-none" />
        </div>

        <div class="space-y-2">
            <label class="text-sm font-medium">Color Principal</label>
            <div class="flex items-center gap-3">
                <input type="color" bind:value={tenantForm.primaryColor} class="h-10 w-20 p-1 bg-background border border-border rounded cursor-pointer" />
                <input type="text" bind:value={tenantForm.primaryColor} class="flex-1 px-3 py-2 bg-background border border-border rounded-md uppercase font-mono" />
            </div>
            <p class="text-xs text-muted-foreground">Este color se usará en el menú lateral y botones principales.</p>
        </div>

        <button on:click={saveTenantSettings} class="mt-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:opacity-90 text-sm font-medium flex items-center gap-2">
            <Save class="w-4 h-4" /> Guardar Identidad
        </button>
    </div>
  </div>

  <div class="bg-card rounded-lg border border-border shadow-sm overflow-hidden">
    <div class="p-6 border-b border-border flex justify-between items-center">
        <div>
            <h3 class="flex items-center gap-2 font-semibold text-card-foreground">
                <MapPin class="w-5 h-5 text-muted-foreground" />
                Bodegas y Ubicaciones
            </h3>
            <p class="text-sm text-muted-foreground mt-1">Gestione dónde se almacena su inventario</p>
        </div>
        <button on:click={() => isAddingLocation = !isAddingLocation} class="px-3 py-1.5 border border-border bg-background hover:bg-accent rounded-md text-sm font-medium flex items-center gap-2">
            <Plus class="w-4 h-4" /> {isAddingLocation ? 'Cancelar' : 'Nueva Ubicación'}
        </button>
    </div>
    
    {#if isAddingLocation}
        <div class="p-4 bg-muted/30 border-b border-border grid grid-cols-1 md:grid-cols-4 gap-3 items-end" transition:fade>
            <div class="space-y-1">
                <label class="text-xs font-medium">Código</label>
                <input type="text" bind:value={newLocation.code} placeholder="Ej: BOD-01" class="w-full px-3 py-2 bg-background border border-border rounded-md text-sm" />
            </div>
            <div class="space-y-1 md:col-span-1">
                <label class="text-xs font-medium">Nombre</label>
                <input type="text" bind:value={newLocation.name} placeholder="Ej: Bodega Central" class="w-full px-3 py-2 bg-background border border-border rounded-md text-sm" />
            </div>
            <div class="space-y-1 md:col-span-1">
                <label class="text-xs font-medium">Descripción</label>
                <input type="text" bind:value={newLocation.description} placeholder="Opcional" class="w-full px-3 py-2 bg-background border border-border rounded-md text-sm" />
            </div>
            <button on:click={handleAddLocation} class="px-3 py-2 bg-green-600 text-white rounded-md text-sm font-medium hover:bg-green-700">
                Guardar
            </button>
        </div>
    {/if}

    <div class="overflow-x-auto">
        <table class="w-full text-sm text-left">
            <thead class="bg-muted text-muted-foreground">
                <tr>
                    <th class="px-6 py-3 font-medium">Código</th>
                    <th class="px-6 py-3 font-medium">Nombre</th>
                    <th class="px-6 py-3 font-medium">Descripción</th>
                    <th class="px-6 py-3 font-medium text-right">Acciones</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-border">
                {#each $locations.filter(l => l.tenantId === $currentTenant.id) as loc}
                    <tr class="hover:bg-accent/50">
                        <td class="px-6 py-3 font-mono text-xs">{loc.code}</td>
                        <td class="px-6 py-3 font-medium">{loc.name}</td>
                        <td class="px-6 py-3 text-muted-foreground">{loc.description}</td>
                        <td class="px-6 py-3 text-right">
                            <button on:click={() => deleteLocation(loc.id)} class="text-muted-foreground hover:text-red-600 transition-colors">
                                <Trash2 class="w-4 h-4" />
                            </button>
                        </td>
                    </tr>
                {/each}
            </tbody>
        </table>
    </div>
  </div>

  <div class="bg-card rounded-lg border border-border shadow-sm overflow-hidden">
    <div class="p-6 border-b border-border">
        <h3 class="flex items-center gap-2 font-semibold text-card-foreground">
            <SettingsIcon class="w-5 h-5 text-muted-foreground" />
            Reglas de Inventario
        </h3>
    </div>
    <div class="p-6 space-y-6 max-w-2xl">
        <div class="grid grid-cols-2 gap-6">
            <div class="space-y-2">
                <label class="text-sm font-medium">Stock Mínimo por Defecto</label>
                <input type="number" bind:value={preferences.defaultMinStock} class="w-full px-3 py-2 bg-background border border-border rounded-md" />
                <p class="text-xs text-muted-foreground">Valor predeterminado al crear productos nuevos.</p>
            </div>
            <div class="space-y-2">
                <label class="text-sm font-medium">Umbral de Alerta (%)</label>
                <input type="number" bind:value={preferences.lowStockThreshold} class="w-full px-3 py-2 bg-background border border-border rounded-md" />
                <p class="text-xs text-muted-foreground">Avisar cuando el stock baje de este % del mínimo.</p>
            </div>
        </div>

        <div class="space-y-3 pt-2">
            <label class="flex items-center gap-3 p-3 border border-border rounded-lg cursor-pointer hover:bg-accent/50 transition-colors">
                <input type="checkbox" bind:checked={preferences.enableScanSound} class="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary" />
                <span class="text-sm font-medium">Habilitar sonido al escanear</span>
            </label>

            <label class="flex items-center gap-3 p-3 border border-border rounded-lg cursor-pointer hover:bg-accent/50 transition-colors">
                <input type="checkbox" bind:checked={preferences.autoFocusScanner} class="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary" />
                <span class="text-sm font-medium">Mantener foco automático en campo de escaneo</span>
            </label>
        </div>

        <button on:click={savePreferences} class="px-4 py-2 border border-border bg-background hover:bg-accent rounded-md text-sm font-medium flex items-center gap-2">
            <Check class="w-4 h-4" /> Guardar Preferencias
        </button>
    </div>
  </div>

  <div class="bg-card rounded-lg border border-border shadow-sm p-6">
    <h3 class="flex items-center gap-2 font-semibold text-card-foreground mb-4">
        <Building2 class="w-5 h-5 text-muted-foreground" />
        Información del Sistema
    </h3>
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        <div>
            <p class="text-muted-foreground mb-1">Tenant ID</p>
            <p class="font-mono text-xs bg-muted p-1 rounded">{$currentTenant.id}</p>
        </div>
        <div>
            <p class="text-muted-foreground mb-1">Fecha Creación</p>
            <p class="font-medium">{new Date($currentTenant.createdAt).toLocaleDateString('es-CL')}</p>
        </div>
        <div>
            <p class="text-muted-foreground mb-1">Versión App</p>
            <p class="font-medium">MVP v1.0.0</p>
        </div>
        <div>
            <p class="text-muted-foreground mb-1">Licencia</p>
            <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                PRO
            </span>
        </div>
    </div>
  </div>

</div>