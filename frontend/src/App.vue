<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <div class="header-content">
        <h1 class="app-title">
          <el-icon><Document /></el-icon>
          可转债双低策略系统
        </h1>
        <nav class="nav-menu">
          <router-link to="/" class="nav-link">
            <el-icon><HomeFilled /></el-icon>
            首页
          </router-link>
          <router-link to="/strategy" class="nav-link">
            <el-icon><TrendCharts /></el-icon>
            策略
          </router-link>
          <router-link to="/portfolio" class="nav-link">
            <el-icon><Wallet /></el-icon>
            投资组合
          </router-link>
          <router-link to="/backtest" class="nav-link">
            <el-icon><DataAnalysis /></el-icon>
            回测
          </router-link>
        </nav>
      </div>
    </el-header>
    
    <el-main class="app-main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { Document, HomeFilled, TrendCharts, Wallet, DataAnalysis } from '@element-plus/icons-vue'
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.app-header {
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  padding: 0;
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 20px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.app-title {
  font-size: 20px;
  font-weight: 600;
  color: #333;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-menu {
  display: flex;
  gap: 20px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #666;
  text-decoration: none;
  padding: 8px 16px;
  border-radius: 4px;
  transition: all 0.3s;
}

.nav-link:hover {
  background: #f5f5f5;
  color: #409eff;
}

.nav-link.router-link-active {
  background: #409eff;
  color: white;
}

.app-main {
  max-width: 1400px;
  margin: 20px auto;
  padding: 20px;
}
</style>

