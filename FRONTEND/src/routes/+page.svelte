<script lang="ts">
  import { onMount } from 'svelte';
  import Sidebar from '../components/Sidebar.svelte';
  import LoginScreen from '../components/LoginScreen.svelte';
  
  // NUEVO COMPONENTE: Debes crear el archivo KioskScanner.svelte
  import KioskScanner from '../components/KioskScanner.svelte';
  
  // Vistas
  import Dashboard from '../components/Dashboard.svelte';
  import BarcodeScanner from '../components/BarcodeScanner.svelte';
  import ProductManagement from '../components/ProductManagement.svelte';
  import InventoryMovements from '../components/InventoryMovements.svelte';
  import UserManagement from '../components/UserManagement.svelte';
  import Settings from '../components/Settings.svelte';
  import LotManagement from '../components/LotManagement.svelte'; 

  import { 
    activeView, 
    currentUser, 
    publicView, // <--- IMPORTANTE
    loadProducts, 
    loadMovements,
    loadUsers, 
    loadLocations, 
    loadAllLots 
  } from '../stores/store';
  
  import { initHidListener, lastScannedCode } from '../lib/hidScanner';

  // Reactividad: Cargar datos al iniciar sesión
  $: if ($currentUser) {
      console.log("Usuario detectado, cargando datos...");
      loadProducts();
      loadMovements();
      loadUsers();
      loadLocations();
      loadAllLots();
  }

  // Lógica de redirección automática por escáner
  $: if ($lastScannedCode && $activeView !== 'scanner' && $currentUser) {
      console.log("Escaneo global detectado, redirigiendo al escáner...");
      activeView.set('scanner');
  }

  onMount(() => {
    const cleanup = initHidListener();
    return cleanup;
  });
</script>

{#if !$currentUser}
  {#if $publicView === 'login'}
      <LoginScreen />
  {:else}
      <KioskScanner />
  {/if}
{:else}
  <div class="flex h-screen bg-background text-foreground font-sans overflow-hidden">
    
    <Sidebar />
    
    <main class="flex-1 ml-64 overflow-y-auto bg-slate-50/50 h-full">
      <div class="p-4 md:p-8 max-w-7xl mx-auto min-h-full">
        
        {#if $activeView === 'dashboard'}
           <Dashboard />
           
        {:else if $activeView === 'scanner'}
           <BarcodeScanner />
           
        {:else if $activeView === 'products'}
           <ProductManagement />

        {:else if $activeView === 'lots'} 
           <LotManagement />

        {:else if $activeView === 'movements'}
           <InventoryMovements />

        {:else if $activeView === 'users'}
           <UserManagement />

        {:else if $activeView === 'settings'}
           <Settings />
           
        {:else}
           <div class="flex items-center justify-center h-64 text-muted-foreground">
             Vista no encontrada: {$activeView}
           </div>
        {/if}

      </div>
    </main>
  </div>
{/if}