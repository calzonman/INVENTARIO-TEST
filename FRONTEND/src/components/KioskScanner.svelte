<script lang="ts">
  import { onDestroy, tick } from 'svelte';
  import { fade, fly } from 'svelte/transition'; // Agregamos fly para animación de alerta
  import { ScanBarcode, UserCheck, ArrowLeft, PackageCheck, AlertTriangle, Camera, X, AlertOctagon, Clock } from 'lucide-svelte';
  import { lastScannedCode } from '../lib/hidScanner';
  import { kioskCheckout, publicView } from '../stores/store';
  import { Html5Qrcode } from 'html5-qrcode';

  // ESTADOS DEL KIOSCO
  type KioskState = 'waiting_user' | 'active_session';
  let currentState: KioskState = 'waiting_user';

  // MODO DE ESCANEO
  let scanMode: 'hid' | 'camera' = 'hid';
  let html5QrCode: Html5Qrcode | null = null;

  // CONTROL DE LECTURA
  let isProcessing = false;

  // DATOS SESIÓN
  let activeUserToken = '';
  let sessionTimeout: any;
  let statusMessage = '';
  // Agregamos 'warning' al tipo
  let statusType: 'success' | 'error' | 'info' | 'warning' = 'info';
  
  // UI FEEDBACK
  let lastProductScanned = '';
  let lastLotUsed = '';
  let remainingStock = 0;
  
  // NUEVO: Datos de alerta de vencimiento
  let expiryAlert: { status: 'expired' | 'soon' | 'ok', date: string } | null = null;

  const unsubscribe = lastScannedCode.subscribe(code => {
      if (code && scanMode === 'hid') {
          handleGlobalScan(code);
          lastScannedCode.set('');
      }
  });

  onDestroy(() => {
      unsubscribe();
      clearTimeout(sessionTimeout);
      stopCamera();
  });

  // ... (Funciones startCamera, stopCamera, resetSession se mantienen igual) ...
  
  // REPETIMOS STARTCAMERA/STOPCAMERA/RESETSESSION PARA CONTEXTO, PERO PUEDES COPIAR LOS TUYOS
  async function startCamera() {
    scanMode = 'camera';
    await tick();
    setTimeout(async () => {
        try {
            if (!document.getElementById("kiosk-reader")) return;
            html5QrCode = new Html5Qrcode("kiosk-reader");
            await html5QrCode.start(
                { facingMode: "environment" }, 
                { fps: 5, qrbox: { width: 250, height: 250 } },
                (decodedText) => { handleGlobalScan(decodedText); },
                () => {} 
            );
        } catch (err) {
            console.error("Error cámara", err);
            alert("No se pudo iniciar la cámara.");
            scanMode = 'hid';
        }
    }, 100);
  }

  async function stopCamera() {
      if (html5QrCode) {
          try { await html5QrCode.stop(); html5QrCode.clear(); } catch(e) {}
          html5QrCode = null;
      }
      scanMode = 'hid';
  }

  function resetSession() {
      currentState = 'waiting_user';
      activeUserToken = '';
      statusMessage = '';
      lastProductScanned = '';
      expiryAlert = null; // Reset alerta
      clearTimeout(sessionTimeout);
  }

  function startSession(token: string) {
      activeUserToken = token;
      currentState = 'active_session';
      playSound('login');
      refreshTimeout();
      statusMessage = 'Usuario Identificado. Escanee productos.';
      statusType = 'info';
      expiryAlert = null;
  }

  function refreshTimeout() {
      clearTimeout(sessionTimeout);
      sessionTimeout = setTimeout(() => {
          resetSession();
      }, 15000);
  }

  async function handleGlobalScan(code: string) {
      if (isProcessing) return;
      if (currentState === 'active_session' && code === activeUserToken) return;

      console.log("Procesando código:", code);
      isProcessing = true;

      try {
        if (currentState === 'waiting_user') {
            if (code.length > 20) { 
                startSession(code);
            } else {
                showStatus('Código inválido. Escanee su QR de acceso.', 'error');
                playSound('error');
            }
        } else {
            refreshTimeout();
            playSound('beep');
            await processCheckout(code);
        }
      } finally {
          setTimeout(() => { isProcessing = false; }, 1500);
      }
  }

  async function processCheckout(productCode: string) {
      try {
          statusMessage = 'Procesando...';
          expiryAlert = null; // Limpiar alertas previas
          
          const res = await kioskCheckout(activeUserToken, productCode);
          
          lastProductScanned = res.product_name;
          remainingStock = res.remaining_stock;
          lastLotUsed = res.lot_used;

          // LÓGICA DE ALERTAS
          if (res.expiry_status === 'expired') {
              showStatus(`¡VENCIDO! ${res.product_name} retirado.`, 'error');
              playSound('error'); // Sonido fuerte
              expiryAlert = { status: 'expired', date: res.expiry_date };
          } 
          else if (res.expiry_status === 'soon') {
              showStatus(`⚠️ VENCE PRONTO: ${res.product_name}`, 'warning');
              playSound('warning'); // Nuevo sonido (implementar abajo)
              expiryAlert = { status: 'soon', date: res.expiry_date };
          } 
          else {
              showStatus(`✅ ${res.product_name} descontado. Stock: ${res.remaining_stock}`, 'success');
              playSound('success');
          }

      } catch (err: any) {
          const msg = err.message || "Error desconocido";
          showStatus(`❌ Error: ${msg}`, 'error');
          playSound('error');
      }
  }

  function showStatus(msg: string, type: 'success' | 'error' | 'info' | 'warning') {
      statusMessage = msg;
      statusType = type;
  }

  function playSound(type: 'success' | 'error' | 'login' | 'beep' | 'warning') {
      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      const oscillator = audioCtx.createOscillator();
      const gainNode = audioCtx.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioCtx.destination);
      
      if (type === 'success') {
          oscillator.type = 'sine';
          oscillator.frequency.setValueAtTime(1000, audioCtx.currentTime);
          oscillator.frequency.exponentialRampToValueAtTime(2000, audioCtx.currentTime + 0.1);
          gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime);
          oscillator.start();
          oscillator.stop(audioCtx.currentTime + 0.15);
      } else if (type === 'error') {
          oscillator.type = 'sawtooth';
          oscillator.frequency.setValueAtTime(200, audioCtx.currentTime);
          oscillator.frequency.linearRampToValueAtTime(100, audioCtx.currentTime + 0.3);
          gainNode.gain.setValueAtTime(0.2, audioCtx.currentTime);
          oscillator.start();
          oscillator.stop(audioCtx.currentTime + 0.4);
      } else if (type === 'warning') {
          // Sonido de alerta doble
          oscillator.type = 'square';
          oscillator.frequency.setValueAtTime(600, audioCtx.currentTime);
          gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime);
          oscillator.start();
          setTimeout(() => {
            const osc2 = audioCtx.createOscillator();
            const gain2 = audioCtx.createGain();
            osc2.type = 'square';
            osc2.connect(gain2);
            gain2.connect(audioCtx.destination);
            osc2.frequency.setValueAtTime(600, audioCtx.currentTime);
            gain2.gain.setValueAtTime(0.1, audioCtx.currentTime);
            osc2.start();
            osc2.stop(audioCtx.currentTime + 0.1);
          }, 150);
          oscillator.stop(audioCtx.currentTime + 0.1);
      } else if (type === 'beep') {
          oscillator.type = 'square';
          oscillator.frequency.setValueAtTime(800, audioCtx.currentTime);
          gainNode.gain.setValueAtTime(0.05, audioCtx.currentTime);
          oscillator.start();
          oscillator.stop(audioCtx.currentTime + 0.05);
      } else {
          oscillator.type = 'triangle';
          oscillator.frequency.setValueAtTime(400, audioCtx.currentTime);
          oscillator.frequency.linearRampToValueAtTime(600, audioCtx.currentTime + 0.2);
          gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime);
          oscillator.start();
          oscillator.stop(audioCtx.currentTime + 0.2);
      }
  }

  function exitKiosk() {
      stopCamera();
      publicView.set('login');
  }
  
  // Función auxiliar para formatear fecha
  const formatDate = (dateStr: string) => {
      if(!dateStr) return '';
      return new Date(dateStr).toLocaleDateString();
  }
</script>

<div class="min-h-screen bg-slate-900 flex flex-col items-center justify-center p-4 text-white relative overflow-hidden">
  
  <div class="absolute inset-0 opacity-10 pointer-events-none">
      <div class="absolute top-0 left-0 w-96 h-96 bg-blue-500 rounded-full blur-[100px] transform -translate-x-1/2 -translate-y-1/2"></div>
      <div class="absolute bottom-0 right-0 w-96 h-96 bg-purple-500 rounded-full blur-[100px] transform translate-x-1/2 translate-y-1/2"></div>
  </div>

  <button on:click={exitKiosk} class="absolute top-6 left-6 flex items-center gap-2 text-slate-400 hover:text-white transition-colors z-50">
      <ArrowLeft class="w-5 h-5" /> Volver al Login
  </button>

  <div class="absolute top-6 right-6 z-50">
      {#if scanMode === 'hid'}
         <button on:click={startCamera} class="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-full border border-slate-600 transition-all text-sm font-medium">
            <Camera class="w-4 h-4" /> Activar Cámara
        </button>
      {:else}
        <button on:click={stopCamera} class="flex items-center gap-2 px-4 py-2 bg-red-900/50 hover:bg-red-900 rounded-full border border-red-700 transition-all text-sm font-medium text-red-100">
            <X class="w-4 h-4" /> Cerrar Cámara
        </button>
      {/if}
  </div>

  <div class="max-w-2xl w-full text-center z-10 space-y-6">
      
      <div>
          <h1 class="text-3xl font-bold tracking-tight mb-1">Inventario Automático</h1>
          <p class="text-slate-400 text-sm">Modo Kiosco</p>
      </div>

      <div class="bg-slate-800/50 border rounded-2xl p-6 backdrop-blur-sm shadow-2xl transition-all duration-300 relative overflow-hidden"
           class:border-green-500={statusType === 'success'}
           class:border-red-500={statusType === 'error'}
           class:border-slate-700={statusType === 'info'}
           class:border-yellow-500={statusType === 'warning'}
      >
          {#if scanMode === 'camera'}
            <div id="kiosk-reader" class="w-full h-[250px] bg-black rounded-lg overflow-hidden mb-4 border border-slate-600"></div>
          {/if}

          {#if currentState === 'waiting_user'}
                <div in:fade class="flex flex-col items-center gap-4 py-6">
                    <div class="w-20 h-20 bg-slate-700 rounded-full flex items-center justify-center animate-pulse">
                        <UserCheck class="w-8 h-8 text-slate-300" />
                    </div>
                    <div>
                        <h2 class="text-xl font-medium text-slate-200">Escanee Credencial</h2>
                        <p class="text-slate-500 text-xs mt-1">Esperando lectura...</p>
                    </div>
                </div>
          {:else if expiryAlert}
                <div in:fly={{ y: 20 }} class="flex flex-col items-center gap-4 py-4">
                    <div class="w-20 h-20 rounded-full flex items-center justify-center animate-bounce"
                         class:bg-red-500={expiryAlert.status === 'expired'}
                         class:bg-yellow-500={expiryAlert.status === 'soon'}
                    >
                        {#if expiryAlert.status === 'expired'}
                            <AlertOctagon class="w-10 h-10 text-white" />
                        {:else}
                            <Clock class="w-10 h-10 text-black" />
                        {/if}
                    </div>
                    <div>
                        <h2 class="text-2xl font-bold"
                            class:text-red-400={expiryAlert.status === 'expired'}
                            class:text-yellow-400={expiryAlert.status === 'soon'}
                        >
                            {expiryAlert.status === 'expired' ? 'PRODUCTO VENCIDO' : 'PRÓXIMO A VENCER'}
                        </h2>
                        <p class="text-slate-300 text-sm mt-1">
                            Vence el: {formatDate(expiryAlert.date)}
                        </p>
                    </div>
                 </div>

          {:else}
                <div in:fade class="flex flex-col items-center gap-4 py-4">
                    <div class="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center border border-green-500/50">
                        <ScanBarcode class="w-8 h-8 text-green-400" />
                    </div>
                    <div>
                        <h2 class="text-2xl font-bold text-white animate-pulse">Escanee Producto</h2>
                        <p class="text-slate-400 text-xs mt-1">Sesión activa ({15}s)</p>
                    </div>
                </div>
          {/if}

          {#if statusMessage}
              <div class="mt-4 p-3 rounded-lg flex items-center justify-center gap-3 text-base font-medium transition-all"
                   class:bg-green-500_20={statusType === 'success'}
                   class:text-green-400={statusType === 'success'}
                   class:bg-red-500_20={statusType === 'error'}
                   class:text-red-400={statusType === 'error'}
                   class:bg-blue-500_20={statusType === 'info'}
                   class:text-blue-400={statusType === 'info'}
                   class:bg-yellow-500_20={statusType === 'warning'}
                   class:text-yellow-400={statusType === 'warning'}
              >
                  {#if statusType === 'success'} <PackageCheck class="w-5 h-5" /> {/if}
                  {#if statusType === 'error'} <AlertTriangle class="w-5 h-5" /> {/if}
                  {#if statusType === 'warning'} <AlertTriangle class="w-5 h-5" /> {/if}
                  {statusMessage}
              </div>
          {/if}
      </div>

      {#if currentState === 'active_session' && lastProductScanned}
          <div class="grid grid-cols-2 gap-4 mt-6" in:fade>
              <div class="bg-slate-800 p-4 rounded-xl border border-slate-700">
                  <p class="text-[10px] text-slate-400 uppercase">Último Retiro</p>
                  <p class="text-lg font-bold text-white truncate">{lastProductScanned}</p>
              </div>
              <div class="bg-slate-800 p-4 rounded-xl border border-slate-700">
                  <p class="text-[10px] text-slate-400 uppercase">Lote</p>
                  <p class="text-lg font-mono"
                     class:text-blue-400={!expiryAlert}
                     class:text-red-400={expiryAlert?.status === 'expired'}
                     class:text-yellow-400={expiryAlert?.status === 'soon'}
                  >
                     {lastLotUsed || 'FEFO'}
                  </p>
              </div>
          </div>
      {/if}
  </div>
</div>

<style>
    .bg-green-500_20 { background-color: rgba(34, 197, 94, 0.2); }
    .bg-red-500_20 { background-color: rgba(239, 68, 68, 0.2); }
    .bg-blue-500_20 { background-color: rgba(59, 130, 246, 0.2); }
    .bg-yellow-500_20 { background-color: rgba(234, 179, 8, 0.2); }
</style>