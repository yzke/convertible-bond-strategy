<template>
  <div class="home-container">
    <el-card class="welcome-card">
      <template #header>
        <div class="card-header">
          <h2>欢迎使用可转债双低策略系统</h2>
        </div>
      </template>
      
      <div class="welcome-content">
        <el-row :gutter="20">
          <el-col :span="8">
            <div class="feature-item">
              <el-icon class="feature-icon" color="#409eff"><TrendCharts /></el-icon>
              <h3>双低策略</h3>
              <p>基于价格和溢价率的量化筛选策略</p>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="feature-item">
              <el-icon class="feature-icon" color="#67c23a"><Wallet /></el-icon>
              <h3>投资组合</h3>
              <p>实时持仓管理和交易历史</p>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="feature-item">
              <el-icon class="feature-icon" color="#e6a23c"><DataAnalysis /></el-icon>
              <h3>历史回测</h3>
              <p>多维度性能指标分析</p>
            </div>
          </el-col>
        </el-row>
        
        <div class="quick-start">
          <h3>快速开始</h3>
          <el-button type="primary" size="large" @click="goToStrategy">
            <el-icon><Right /></el-icon>
            开始使用策略
          </el-button>
        </div>
      </div>
    </el-card>
    
    <el-card class="info-card">
      <template #header>
        <div class="card-header">
          <h3>系统信息</h3>
        </div>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="API状态">
          <el-tag :type="apiStatus.type">{{ apiStatus.text }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="版本">v1.0.0</el-descriptions-item>
        <el-descriptions-item label="数据源">Akshare</el-descriptions-item>
        <el-descriptions-item label="策略类型">双低策略</el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { TrendCharts, Wallet, DataAnalysis, Right } from '@element-plus/icons-vue'
import apiClient from '@/api/index' // 👈 核心修复：必须引入这个封装好的客户端

const router = useRouter()

const apiStatus = ref({
  type: 'info' as 'success' | 'danger' | 'info',
  text: '检查中...'
})

const checkApiStatus = async () => {
  try {
    // 👈 核心修复：使用 apiClient 而不是 axios
    // 这样请求会自动变成 /api/health，Vite 代理才能把它转发给后端
    await apiClient.get('/health')
    apiStatus.value = { type: 'success', text: '正常运行' }
  } catch (error) {
    console.error('API检查失败:', error)
    apiStatus.value = { type: 'danger', text: '连接失败' }
  }
}

const goToStrategy = () => {
  router.push('/strategy')
}

onMounted(() => {
  checkApiStatus()
})
</script>

<style scoped>
.home-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.welcome-card {
  background: white;
}

.card-header h2 {
  margin: 0;
  color: #333;
}

.card-header h3 {
  margin: 0;
  color: #666;
}

.welcome-content {
  padding: 20px 0;
}

.feature-item {
  text-align: center;
  padding: 30px;
  background: #f5f7fa;
  border-radius: 8px;
  transition: transform 0.3s;
}

.feature-item:hover {
  transform: translateY(-5px);
}

.feature-icon {
  font-size: 48px;
  margin-bottom: 15px;
}

.feature-item h3 {
  margin: 10px 0;
  color: #333;
}

.feature-item p {
  color: #666;
  margin: 0;
}

.quick-start {
  text-align: center;
  margin-top: 40px;
}

.quick-start h3 {
  margin-bottom: 20px;
  color: #333;
}

.info-card {
  background: white;
}
</style>
