import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    // 监听所有 IP (包括 IPv6)
    host: '::', 
    port: 48001,
    proxy: {
      // ✅ 修复点 1：专门处理健康检查接口
      '/api/health': {
        target: 'http://127.0.0.1:48000',
        changeOrigin: true,
        // 把 /api/health 重写为 /health
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      // ✅ 修复点 2：处理其他通用接口
      '/api': {
        target: 'http://127.0.0.1:48000',
        changeOrigin: true,
        // 其他接口保持原样，因为后端确实是在 /api 下面
      }
    }
  }
})
