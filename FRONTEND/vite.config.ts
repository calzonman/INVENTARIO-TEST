import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	// Agrega esto:
	server: {
		host: true, // Esto habilita la escucha en la IP de red
        port: 5173  // (Opcional) Asegura que el puerto sea siempre este
	}
});
