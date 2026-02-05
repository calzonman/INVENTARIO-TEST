<script lang="ts">
  import { Package, Lock, Mail, ArrowRight, AlertCircle, ScanBarcode } from 'lucide-svelte';
  import { fade, fly } from 'svelte/transition';
  import { loginUser, publicView } from '../stores/store'; // IMPORTANTE: publicView

  let email = '';
  let password = '';
  let isLoading = false;
  let errorMessage = '';

  async function handleLogin(e: Event) {
    e.preventDefault();
    isLoading = true;
    errorMessage = ''; 
    
    try {
        await loginUser(email, password);
    } catch (error: any) {
        console.error("Login fallido:", error);
        errorMessage = error.message || "Credenciales inválidas. Intente nuevamente.";
    } finally {
        isLoading = false;
    }
  }

  function switchToKiosk() {
      publicView.set('kiosk');
  }

  function fillDev(role: string) {
      if(role === 'admin') { email = 'admin@techretail.com'; password = 'admin'; }
  }
</script>

<div class="min-h-screen flex items-center justify-center bg-slate-50 p-4" in:fade>
  <div class="w-full max-w-md" in:fly={{ y: 20, duration: 800 }}>
    
    <div class="text-center mb-8">
      <div class="inline-flex items-center justify-center w-16 h-16 bg-primary rounded-2xl mb-4 shadow-lg shadow-primary/20">
        <Package class="w-8 h-8 text-white" />
      </div>
      <h1 class="text-3xl font-bold text-slate-900 tracking-tight">Sistema Inventario</h1>
      <p class="text-slate-600 mt-2">Gestión inteligente de stock y trazabilidad</p>
    </div>

    <div class="bg-white rounded-xl shadow-xl border border-slate-100 overflow-hidden relative">
      <div class="p-8 pb-6">
        <div class="mb-6">
            <h2 class="text-xl font-semibold text-slate-900">Iniciar Sesión</h2>
            <p class="text-sm text-slate-500">Ingrese sus credenciales para continuar</p>
        </div>

        {#if errorMessage}
            <div class="mb-4 p-3 bg-red-50 border border-red-100 rounded-lg flex items-center gap-2 text-red-600 text-sm animate-in slide-in-from-top-1">
                <AlertCircle class="w-4 h-4" />
                <span>{errorMessage}</span>
            </div>
        {/if}

        <form on:submit={handleLogin} class="space-y-5">
          <div class="space-y-2">
            <label class="text-sm font-medium text-slate-700">Correo Electrónico</label>
            <div class="relative">
              <Mail class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input 
                type="email" 
                bind:value={email}
                placeholder="usuario@empresa.com"
                required
                class="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
              />
            </div>
          </div>

          <div class="space-y-2">
            <div class="flex justify-between">
                <label class="text-sm font-medium text-slate-700">Contraseña</label>
            </div>
            <div class="relative">
              <Lock class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input 
                type="password" 
                bind:value={password}
                placeholder="••••••••"
                required
                class="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
              />
            </div>
          </div>

          <button 
            type="submit" 
            disabled={isLoading}
            class="w-full py-2.5 bg-primary text-white font-medium rounded-lg hover:bg-slate-800 focus:ring-4 focus:ring-slate-200 transition-all flex justify-center items-center gap-2 disabled:opacity-70"
          >
            {#if isLoading}
                <span class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                Iniciando...
            {:else}
                Ingresar al Sistema <ArrowRight class="w-4 h-4" />
            {/if}
          </button>
        </form>

        <div class="mt-6 pt-6 border-t border-slate-100">
             <button 
                type="button" 
                on:click={switchToKiosk}
                class="w-full py-3 bg-slate-100 text-slate-700 font-bold rounded-lg hover:bg-slate-200 transition-colors flex items-center justify-center gap-2 group"
             >
                <ScanBarcode class="w-5 h-5 text-slate-500 group-hover:text-slate-800 transition-colors" />
                Modo Inventario Automático
             </button>
        </div>

        <div class="mt-4 opacity-30 hover:opacity-100 transition-opacity text-center">
            <button on:click={() => fillDev('admin')} class="text-[10px] text-blue-500 underline">
                Rellenar Admin
            </button>
        </div>
      </div>
    </div>
    
    <p class="text-center text-xs text-slate-400 mt-6">
        © 2026 Sistema SaaS de Inventario v1.0
    </p>
  </div>
</div>