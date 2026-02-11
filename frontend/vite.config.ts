import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      // All API calls go through /api prefix, which gets stripped when proxying to backend
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/overview': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'antd-vendor': ['antd', '@ant-design/icons'],
          'graph-vendor': ['cytoscape', 'cytoscape-react', 'cytoscape-cose-bilkent'],
          'chart-vendor': ['chart.js', 'react-chartjs-2'],
          'query-vendor': ['@tanstack/react-query', 'axios', 'zustand'],
        },
      },
    },
  },
})
