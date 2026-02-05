import { onMount, onDestroy } from 'svelte';
import { writable } from 'svelte/store';

// Store para notificar cuando se escanea algo exitosamente
export const lastScannedCode = writable('');

export function initHidListener() {
    let buffer = '';
    let lastKeyTime = 0;
    const SCAN_TIMEOUT = 50; // ms entre teclas (los escáneres son muy rápidos)

    function handleKeyDown(e: KeyboardEvent) {
        const currentTime = Date.now();
        const isTimeValid = (currentTime - lastKeyTime) < SCAN_TIMEOUT;
        
        // Si ha pasado mucho tiempo, reseteamos el buffer (asumimos que es tecleo manual lento)
        if (!isTimeValid && buffer.length > 0) {
            buffer = '';
        }

        lastKeyTime = currentTime;

        if (e.key === 'Enter') {
            if (buffer.length > 3) { // Mínimo de caracteres para considerar válido
                console.log("HID Scan detectado:", buffer);
                lastScannedCode.set(buffer);
                e.preventDefault(); // Prevenir submit de formularios si los hubiera
            }
            buffer = '';
        } else if (e.key.length === 1) { // Solo caracteres imprimibles
            buffer += e.key;
        }
    }

    if (typeof window !== 'undefined') {
        window.addEventListener('keydown', handleKeyDown);
    }

    return () => {
        if (typeof window !== 'undefined') {
            window.removeEventListener('keydown', handleKeyDown);
        }
    };
}