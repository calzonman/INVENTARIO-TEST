<script lang="ts">
  import { 
    LayoutDashboard, ScanBarcode, Package, History, 
    Users, Settings, LogOut, Building2, Tags, UserCircle 
  } from 'lucide-svelte';
  
  // IMPORTAR LA ACCIÓN REAL DE LOGOUT
  import { activeView, currentUser, currentTenant, logoutUser } from '../stores/store';
  
  import { clsx } from 'clsx';
  import { twMerge } from 'tailwind-merge';

  function cn(...inputs: any[]) {
    return twMerge(clsx(inputs));
  }

  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, roles: ['admin', 'supervisor', 'operator'] },
    { id: 'scanner', label: 'Escáner', icon: ScanBarcode, roles: ['admin', 'supervisor', 'operator'] },
    { id: 'products', label: 'Productos', icon: Package, roles: ['admin', 'supervisor', 'operator'] },
    { id: 'lots', label: 'Lotes / Venc.', icon: Tags, roles: ['admin', 'supervisor'] },
    { id: 'movements', label: 'Movimientos', icon: History, roles: ['admin', 'supervisor', 'operator'] },
    { id: 'users', label: 'Usuarios', icon: Users, roles: ['admin', 'supervisor'] },
    { id: 'settings', label: 'Configuración', icon: Settings, roles: ['admin'] },
  ];

  // Filtramos items según rol (reactivo)
  $: filteredMenuItems = menuItems.filter(item => 
    $currentUser && item.roles.includes($currentUser.role)
  );

  // MANEJO DE CIERRE DE SESIÓN
  function handleLogout() {
      if (confirm("¿Seguro que desea cerrar sesión?")) {
          logoutUser();
          // Al limpiar el store 'currentUser', App.svelte mostrará automáticamente el Login
      }
  }
</script>

<aside class="w-64 bg-slate-900 text-slate-300 flex flex-col h-screen fixed left-0 top-0 z-40 border-r border-slate-800 shadow-xl">
  
  <div class="p-6">
    <div class="flex items-center gap-3 text-white">
      <div class="w-10 h-10 rounded-lg bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-900/50">
        <Building2 class="w-6 h-6 text-white" />
      </div>
      <div class="flex-1 min-w-0">
        <h2 class="text-sm truncate font-medium">{$currentTenant?.name}</h2>
        <p class="text-[10px] text-slate-400 uppercase tracking-wider">{$currentTenant?.industry}</p>
      </div>
    </div>
  </div>

  <div class="h-px bg-slate-800 mx-6 mb-4"></div>

  <nav class="flex-1 px-4 space-y-1 overflow-y-auto custom-scrollbar">
    {#each filteredMenuItems as item}
      <button
        on:click={() => activeView.set(item.id)}
        class={cn(
          'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group relative',
          $activeView === item.id
            ? 'bg-blue-600 text-white shadow-md shadow-blue-900/20'
            : 'hover:bg-slate-800 hover:text-white'
        )}
      >
        <svelte:component this={item.icon} class={cn("w-5 h-5 transition-transform group-hover:scale-110", $activeView === item.id ? "text-white" : "text-slate-400 group-hover:text-white")} />
        <span class="text-sm font-medium">{item.label}</span>
        
        {#if $activeView === item.id}
            <span class="absolute right-2 w-1.5 h-1.5 rounded-full bg-white/50"></span>
        {/if}
      </button>
    {/each}
  </nav>

  <div class="p-4 border-t border-slate-800 bg-slate-900/50">
    <div class="mb-3 px-2 flex items-center gap-3">
        <div class="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center border border-slate-600">
            <UserCircle class="w-5 h-5 text-slate-400" />
        </div>
        <div class="min-w-0">
            <p class="text-sm font-medium text-white truncate">{$currentUser?.name || 'Usuario'}</p>
            <p class="text-xs text-slate-500 truncate capitalize">{$currentUser?.role || 'Invitado'}</p>
        </div>
    </div>
    
    <button
      on:click={handleLogout}
      class="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-slate-400 hover:bg-red-500/10 hover:text-red-400 transition-colors border border-transparent hover:border-red-500/20"
    >
      <LogOut class="w-4 h-4" />
      <span class="text-sm font-medium">Cerrar Sesión</span>
    </button>
  </div>
</aside>

<style>
    /* Scrollbar fino para navegaciones largas */
    .custom-scrollbar::-webkit-scrollbar {
        width: 4px;
    }
    .custom-scrollbar::-webkit-scrollbar-track {
        background: transparent;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb {
        background: #334155;
        border-radius: 4px;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb:hover {
        background: #475569;
    }
</style>