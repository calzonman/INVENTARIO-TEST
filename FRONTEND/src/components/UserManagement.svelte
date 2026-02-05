<script lang="ts">
  import { fade, slide } from 'svelte/transition';
  import { Users, UserPlus, Shield, Edit, Trash2, Mail, X, CheckCircle2, Lock, QrCode } from 'lucide-svelte';
  import QRCode from 'qrcode';
  
  import { 
    users, 
    currentUser, 
    currentTenant, 
    addUser, 
    deleteUser, 
    type User 
  } from '../stores/store';

  let isAddDialogOpen = false;
  let isEditDialogOpen = false;
  let isQrDialogOpen = false;
  let selectedUser: User | null = null;
  let qrCodeDataUrl = '';
  
  let formData = {
    name: '',
    email: '',
    password: '', 
    role: 'operator' as 'admin' | 'supervisor' | 'operator'
  };

  $: tenantUsers = $users.filter(u => u.tenantId === $currentTenant.id);

  const getRoleBadgeClass = (role: string) => {
      switch(role) {
          case 'admin': return 'bg-purple-100 text-purple-800 border-purple-200';
          case 'supervisor': return 'bg-blue-100 text-blue-800 border-blue-200';
          default: return 'bg-slate-100 text-slate-800 border-slate-200';
      }
  }; 
  const getRoleDescription = (role: string) => {
      switch(role) {
          case 'admin': return 'Control total del sistema, gestión de usuarios y configuración global.';
          case 'supervisor': return 'Puede gestionar productos, lotes y ver reportes avanzados.';
          default: return 'Acceso básico para registrar movimientos de entrada y salida.';
      }
  };

  function resetForm() {
    formData = { name: '', email: '', password: '', role: 'operator' };
  }

  async function handleAdd() {
    if (!formData.password || formData.password.length < 4) {
        alert("La contraseña es obligatoria y debe tener al menos 4 caracteres.");
        return;
    }

    try {
      await addUser({
          ...formData,
          tenantId: $currentTenant.id
      });
      isAddDialogOpen = false;
      resetForm();
    } catch (e: any) {
      alert("Error al crear usuario: " + e.message);
    }
  }

  function openEdit(user: User) {
    selectedUser = user;
    formData = { name: user.name, email: user.email, password: '', role: user.role };
    isEditDialogOpen = true;
  }

  async function handleEdit() {
    alert("Edición de usuario pendiente (Endpoint PUT no implementado en MVP)");
    isEditDialogOpen = false;
  }

  async function handleDelete(user: User) {
    if (user.id === $currentUser?.id) {
        alert("No puedes eliminar tu propio usuario.");
        return;
    }
    if (confirm(`¿Eliminar al usuario ${user.name}?`)) {
        try {
            await deleteUser(user.id);
        } catch (e) {
            alert("Error al eliminar");
        }
    }
  }

  // --- LÓGICA QR ---
  async function showQr(user: User) {
      if (!user.badgeToken) {
          alert("Este usuario no tiene Token QR generado.");
          return;
      }
      try {
          // Generar QR con el token
          qrCodeDataUrl = await QRCode.toDataURL(user.badgeToken, { width: 300 });
          selectedUser = user;
          isQrDialogOpen = true;
      } catch (err) {
          console.error(err);
          alert("Error generando QR");
      }
  }
</script>

<div class="space-y-6 animate-in fade-in duration-500 pb-10">
  
  <div class="flex items-center justify-between">
    <div>
      <h1 class="text-2xl font-semibold text-primary">Gestión de Usuarios</h1>
      <p class="text-muted-foreground">Administre los accesos y roles del equipo</p>
    </div>
    <button on:click={() => { resetForm(); isAddDialogOpen = true; }} class="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:opacity-90 flex items-center gap-2 text-sm font-medium shadow-sm transition-all">
      <UserPlus class="w-4 h-4" /> Nuevo Usuario
    </button>
  </div>

  <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
    {#each ['admin', 'supervisor', 'operator'] as role}
        <div class="bg-card p-4 rounded-lg border border-border shadow-sm flex items-start gap-3">
            <div class={`p-2 rounded-lg ${role === 'admin' ? 'bg-purple-100 text-purple-600' : role === 'supervisor' ? 'bg-blue-100 text-blue-600' : 'bg-slate-100 text-slate-600'}`}>
                <Shield class="w-5 h-5" />
            </div>
            <div>
                <span class={`text-xs font-bold uppercase tracking-wider ${role === 'admin' ? 'text-purple-600' : role === 'supervisor' ? 'text-blue-600' : 'text-slate-600'}`}>
                    {role}
                </span>
                <p class="text-xs text-muted-foreground mt-1 leading-relaxed">
                    {getRoleDescription(role)}
                </p>
            </div>
        </div>
    {/each}
  </div>

  <div class="bg-card rounded-lg border border-border shadow-sm overflow-hidden">
    <div class="p-6 border-b border-border flex items-center gap-2">
        <Users class="w-5 h-5 text-muted-foreground" />
        <h3 class="font-semibold text-card-foreground">Usuarios Activos ({tenantUsers.length})</h3>
    </div>
    <div class="overflow-x-auto">
      <table class="w-full text-sm text-left">
        <thead class="bg-muted text-muted-foreground border-b border-border">
          <tr>
            <th class="px-6 py-3 font-medium">Usuario</th>
            <th class="px-6 py-3 font-medium">Rol</th>
            <th class="px-6 py-3 font-medium">Fecha Creación</th>
            <th class="px-6 py-3 font-medium text-right">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-border">
          {#each tenantUsers as user (user.id)}
            <tr transition:slide|local class="hover:bg-accent/50 transition-colors">
              <td class="px-6 py-4">
                <div class="flex items-center gap-3">
                  <div class="w-9 h-9 bg-secondary rounded-full flex items-center justify-center text-secondary-foreground">
                    <Mail class="w-4 h-4" />
                  </div>
                  <div>
                    <p class="font-medium text-foreground">{user.name}</p>
                    <p class="text-xs text-muted-foreground">{user.email}</p>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4">
                <span class={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getRoleBadgeClass(user.role)}`}>
                  {user.role === 'admin' ? 'Administrador' : user.role === 'supervisor' ? 'Supervisor' : 'Operador'}
                </span>
              </td>
              <td class="px-6 py-4 text-muted-foreground">
                {user.createdAt ? new Date(user.createdAt).toLocaleDateString('es-CL') : '-'}
              </td>
              <td class="px-6 py-4 text-right">
                <div class="flex justify-end gap-2">
                  <button on:click={() => showQr(user)} class="p-1.5 hover:bg-slate-100 rounded text-slate-500 hover:text-slate-800 transition-colors border border-transparent hover:border-slate-200" title="Ver QR de Acceso">
                    <QrCode class="w-4 h-4" />
                  </button>
                  <button on:click={() => openEdit(user)} class="p-1.5 hover:bg-accent rounded text-muted-foreground hover:text-foreground transition-colors">
                    <Edit class="w-4 h-4" />
                  </button>
                  <button 
                    on:click={() => handleDelete(user)} 
                    class={`p-1.5 rounded transition-colors ${user.id === $currentUser?.id ? 'opacity-30 cursor-not-allowed text-slate-400' : 'hover:bg-red-50 text-red-500 hover:text-red-600'}`}
                    disabled={user.id === $currentUser?.id}
                  >
                    <Trash2 class="w-4 h-4" />
                  </button>
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </div>

  {#if isAddDialogOpen || isEditDialogOpen}
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm" transition:fade={{ duration: 200 }}>
      <div class="bg-card border border-border rounded-lg shadow-xl w-full max-w-md overflow-hidden" transition:slide={{ duration: 200 }}>
        <div class="p-6 border-b border-border flex justify-between items-center">
            <h2 class="text-lg font-semibold text-foreground">
                {isAddDialogOpen ? 'Nuevo Usuario' : 'Editar Usuario'}
            </h2>
            <button on:click={() => { isAddDialogOpen = false; isEditDialogOpen = false; }} class="text-muted-foreground hover:text-foreground">
                <X class="w-5 h-5" />
            </button>
        </div>
        
        <div class="p-6 space-y-4">
            <div class="space-y-2">
                <label class="text-sm font-medium text-foreground">Nombre Completo</label>
                <input type="text" bind:value={formData.name} class="w-full px-3 py-2 bg-background border border-border rounded-md focus:ring-2 focus:ring-ring focus:outline-none" placeholder="Ej: Juan Pérez" />
            </div>
            
            <div class="space-y-2">
                <label class="text-sm font-medium text-foreground">Correo Electrónico</label>
                <input type="email" bind:value={formData.email} class="w-full px-3 py-2 bg-background border border-border rounded-md focus:ring-2 focus:ring-ring focus:outline-none" placeholder="ejemplo@empresa.com" />
            </div>

            {#if isAddDialogOpen}
                <div class="space-y-2">
                    <label class="text-sm font-medium text-foreground flex items-center gap-2">
                        <Lock class="w-3 h-3" /> Contraseña Inicial
                    </label>
                    <input 
                        type="password" 
                        bind:value={formData.password} 
                        class="w-full px-3 py-2 bg-background border border-border rounded-md focus:ring-2 focus:ring-ring focus:outline-none" 
                        placeholder="Mínimo 4 caracteres" 
                    />
                </div>
            {/if}

            <div class="space-y-2">
                <label class="text-sm font-medium text-foreground">Rol de Acceso</label>
                <div class="grid grid-cols-3 gap-2">
                    {#each ['operator', 'supervisor', 'admin'] as roleOption}
                        <button 
                            on:click={() => formData.role = roleOption}
                            class={`text-xs py-2 px-1 rounded border transition-all ${formData.role === roleOption ? 'bg-primary text-primary-foreground border-primary' : 'bg-background border-border text-muted-foreground hover:bg-accent'}`}
                        >
                            {roleOption === 'admin' ? 'Admin' : roleOption === 'supervisor' ? 'Supervisor' : 'Operador'}
                        </button>
                    {/each}
                </div>
            </div>
        </div>

        <div class="p-6 bg-muted/50 border-t border-border flex justify-end gap-3">
            <button on:click={() => { isAddDialogOpen = false; isEditDialogOpen = false; }} class="px-4 py-2 border border-border bg-background hover:bg-accent rounded-md text-sm font-medium">
                Cancelar
            </button>
            <button on:click={isAddDialogOpen ? handleAdd : handleEdit} class="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:opacity-90 text-sm font-medium">
                {isAddDialogOpen ? 'Crear Usuario' : 'Guardar Cambios'}
            </button>
        </div>
      </div>
    </div>
  {/if}

  {#if isQrDialogOpen}
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm" transition:fade={{ duration: 200 }}>
        <div class="bg-white rounded-xl shadow-2xl w-full max-w-sm overflow-hidden text-center p-8 relative" transition:slide={{ duration: 300 }}>
            <button on:click={() => isQrDialogOpen = false} class="absolute top-4 right-4 text-slate-400 hover:text-slate-600">
                <X class="w-6 h-6" />
            </button>
            
            <h3 class="text-xl font-bold text-slate-900 mb-1">{selectedUser?.name}</h3>
            <p class="text-sm text-slate-500 mb-6 uppercase tracking-wider">{selectedUser?.role}</p>
            
            <div class="flex justify-center mb-6">
                <img src={qrCodeDataUrl} alt="QR Acceso" class="border-4 border-slate-900 rounded-lg" />
            </div>
            
            <p class="text-xs text-slate-400 mb-6 px-4">
                Escanee este código en el "Modo Kiosco" para realizar retiros rápidos de inventario.
            </p>

            <button on:click={() => window.print()} class="w-full py-3 bg-slate-900 text-white font-bold rounded-lg hover:bg-slate-800 transition-colors">
                Imprimir Credencial
            </button>
        </div>
    </div>
  {/if}
</div>