import { defineConfig } from 'vite';

export default defineConfig({
  base: './',
  build: { outDir: '../../docs/wvs/react', emptyOutDir: true },
});
