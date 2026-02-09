<script lang="ts">
  import { fade } from 'svelte/transition';
  import { onMount } from 'svelte';
  import { 
    Settings as SettingsIcon, 
    Building2, 
    MapPin, 
    Palette, 
    Save, 
    Plus, 
    Trash2, 
    Check, 
    Mail, 
    AlertTriangle 
  } from 'lucide-svelte';
  
  // Importamos acciones del Store
  import { 
    currentTenant, 
    locations, 
    addLocation, 
    deleteLocation,
    loadTenantSettings, // <--- Nueva función
    saveTenantEmails    // <--- Nueva función
  } from '../stores/store';

  // --- ESTADOS LOCALES ---
  let tenantForm = { ...$currentTenant };
  
  // Estado para Ubicaciones
  let newLocation = { code: '', name: '', description: '' };
  let isAddingLocation = false;

  // Estado para Preferencias Locales (Stock, Sonido, etc.)
  let preferences = { 
    defaultMinStock: 10, 
    lowStockThreshold: 20, 
    enableScanSound: true, 
    autoFocusScanner: true 
  };

  // --- ESTADO PARA CORREOS (NUEVO) ---
  let notificationEmails: string[] = [];
  let newEmail = "";
  let isLoadingSettings = false;

  // --- LIFECYCLE: Cargar correos al entrar ---
  onMount(async () => {
    isLoadingSettings = true;
    try {
        const settings = await loadTenantSettings();
        notificationEmails = settings.notification_emails || [];
    } catch (error) {
        console.error("Error cargando configuración:", error);
    } finally {
        isLoadingSettings = false;
    }
  });

  // --- LÓGICA DE CORREOS ---
  function addEmail() {
    // Validación simple de email y duplicados
    if (newEmail && newEmail.includes('@') && !notificationEmails.includes(newEmail)) {
        notificationEmails = [...notificationEmails, newEmail.trim()];
        newEmail = "";
    }
  }

  function removeEmail(email: string) {
    notificationEmails = notificationEmails.filter(e => e !== email);
  }

  // --- GUARDAR TODO (General + Correos) ---
  async function saveAllSettings() {
    try {
        // 1. Guardar cambios locales de Tenant (Nombre, etc) - (Simulado por ahora en frontend)
        currentTenant.set({ ...tenantForm });

        // 2. Guardar Correos en Backend (Real)
        await saveTenantEmails(notificationEmails);

        alert("✅ Configuración y correos guardados correctamente.");
    } catch (error) {
        console.error(error);
        alert("❌ Error al guardar en el servidor.");
    }
  }

  // --- LÓGICA DE UBICACIONES (EXISTENTE) ---
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
    if(confirm('¿Seguro de eliminar esta ubicación?')) {
        await deleteLocation(id);
    }
  }
</script>

<div class="space-y-6 pb-20" in:fade={{ duration: 300 }}>
  
  <header class="flex justify-between items-center mb-6">
    <div>
        <h2 class="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <SettingsIcon class="w-6 h-6 text-primary" />
            Configuración
        </h2>
        <p class="text-muted-foreground">Administra los parámetros generales de tu empresa.</p>
    </div>
  </header>

  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    
    <div class="bg-card rounded-lg border border-border shadow-sm p-6 space-y-6">
        
        <div>
            <h3 class="flex items-center gap-2 font-semibold text-card-foreground mb-4">
                <Palette class="w-5 h-5 text-muted-foreground" />
                Preferencias Generales
            </h3>
            
            <div class="space-y-4">
                <div class="grid grid-cols-2 gap-4">
                    <div class="space-y-2">
                        <label class="text-sm font-medium">Nombre Empresa</label>
                        <input type="text" bind:value={tenantForm.name} class="w-full px-3 py-2 bg-background border border-border rounded-md focus:ring-2 focus:ring-primary/20 outline-none" />
                    </div>
                    <div class="space-y-2">
                        <label class="text-sm font-medium">Stock Mínimo Default</label>
                        <input type="number" bind:value={preferences.defaultMinStock} class="w-full px-3 py-2 bg-background border border-border rounded-md outline-none" />
                    </div>
                </div>

                <div class="flex items-center justify-between p-3 bg-muted/30 rounded-lg border border-border">
                    <span class="text-sm">Sonido al Escanear</span>
                    <input type="checkbox" bind:checked={preferences.enableScanSound} class="accent-primary w-4 h-4" />
                </div>
            </div>
        </div>

        <hr class="border-border" />

        <div>
            <h3 class="flex items-center gap-2 font-semibold text-card-foreground mb-2">
                <Mail class="w-5 h-5 text-muted-foreground" />
                Alertas de Vencimiento
            </h3>
            <p class="text-xs text-muted-foreground mb-4">
                Los correos listados recibirán el reporte diario de lotes vencidos.
            </p>

            {#if isLoadingSettings}
                <p class="text-xs text-muted-foreground">Cargando correos...</p>
            {:else}
                <div class="flex gap-2 mb-3">
                    <div class="relative flex-1">
                        <Mail class="w-4 h-4 absolute left-3 top-2.5 text-muted-foreground" />
                        <input 
                            type="email" 
                            bind:value={newEmail} 
                            placeholder="nuevo@correo.com" 
                            class="w-full pl-9 pr-3 py-2 bg-background border border-border rounded-md text-sm outline-none focus:border-primary"
                            on:keydown={(e) => e.key === 'Enter' && addEmail()}
                        />
                    </div>
                    <button 
                        on:click={addEmail} 
                        class="px-3 py-2 bg-secondary hover:bg-secondary/80 text-secondary-foreground rounded-md transition-colors"
                        disabled={!newEmail}
                    >
                        <Plus class="w-4 h-4" />
                    </button>
                </div>

                <div class="flex flex-wrap gap-2 min-h-[40px] p-2 bg-muted/20 rounded-md border border-dashed border-border">
                    {#each notificationEmails as email}
                        <div class="flex items-center gap-1 bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300 px-2.5 py-1 rounded-full text-xs font-medium animate-in fade-in zoom-in duration-200">
                            <span>{email}</span>
                            <button on:click={() => removeEmail(email)} class="ml-1 hover:text-red-500 transition-colors">
                                <Trash2 class="w-3 h-3" />
                            </button>
                        </div>
                    {/each}
                    {#if notificationEmails.length === 0}
                        <div class="w-full flex items-center justify-center gap-2 text-muted-foreground text-xs py-2 opacity-60">
                            <AlertTriangle class="w-3 h-3" /> Sin correos configurados
                        </div>
                    {/if}
                </div>
            {/if}
        </div>

        <div class="pt-2">
            <button 
                on:click={saveAllSettings} 
                class="w-full py-2.5 bg-primary text-primary-foreground hover:bg-primary/90 rounded-md font-medium flex items-center justify-center gap-2 shadow-sm transition-all"
            >
                <Check class="w-4 h-4" /> Guardar Cambios
            </button>
        </div>
    </div>

    <div class="bg-card rounded-lg border border-border shadow-sm p-6 flex flex-col h-full">
        <div class="flex justify-between items-center mb-4">
            <h3 class="flex items-center gap-2 font-semibold text-card-foreground">
                <MapPin class="w-5 h-5 text-muted-foreground" />
                Ubicaciones
            </h3>
            <button 
                on:click={() => isAddingLocation = !isAddingLocation}
                class="text-xs bg-secondary hover:bg-secondary/80 px-2 py-1 rounded-md transition-colors"
            >
                {isAddingLocation ? 'Cancelar' : '+ Nueva'}
            </button>
        </div>

        {#if isAddingLocation}
            <div class="bg-muted/30 p-4 rounded-lg border border-border mb-4 space-y-3" transition:fade>
                <input bind:value={newLocation.code} placeholder="Código (ej: A-01)" class="w-full px-3 py-2 text-sm rounded-md border border-border" />
                <input bind:value={newLocation.name} placeholder="Nombre (ej: Pasillo A)" class="w-full px-3 py-2 text-sm rounded-md border border-border" />
                <button on:click={handleAddLocation} class="w-full py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium">
                    Confirmar
                </button>
            </div>
        {/if}

        <div class="flex-1 overflow-y-auto max-h-[400px] space-y-2 pr-1">
            {#each $locations as loc (loc.id)}
                <div class="flex items-center justify-between p-3 bg-background border border-border rounded-lg group hover:border-primary/50 transition-colors">
                    <div>
                        <p class="font-medium text-sm">{loc.name}</p>
                        <p class="text-xs text-muted-foreground font-mono">{loc.code}</p>
                    </div>
                    <button on:click={() => handleDeleteLocation(loc.id)} class="text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-opacity">
                        <Trash2 class="w-4 h-4" />
                    </button>
                </div>
            {:else}
                <div class="text-center py-10 text-muted-foreground text-sm">
                    No hay ubicaciones registradas.
                </div>
            {/each}
        </div>
    </div>
  </div>

  <div class="bg-card rounded-lg border border-border shadow-sm p-6 mt-6">
    <h3 class="flex items-center gap-2 font-semibold text-card-foreground mb-4">
        <Building2 class="w-5 h-5 text-muted-foreground" />
        Información del Sistema
    </h3>
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        <div>
            <p class="text-muted-foreground mb-1">Tenant ID</p>
            <p class="font-mono text-xs bg-muted p-1 rounded overflow-hidden text-ellipsis">{$currentTenant.id}</p>
        </div>
        <div>
            <p class="text-muted-foreground mb-1">Fecha Creación</p>
            <p class="font-medium">{new Date($currentTenant.createdAt).toLocaleDateString('es-CL')}</p>
        </div>
        <div>
            <p class="text-muted-foreground mb-1">Versión App</p>
            <p class="font-medium">MVP v1.0.0</p>
        </div>
    </div>
  </div>
</div>