<template>
  <div class="strategy-container">
    <el-card class="config-card">
      <template #header>
        <div class="card-header">
          <h2>策略配置</h2>
        </div>
      </template>
      
      <el-form :model="config" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="最高价格">
              <el-input-number v-model="config.max_price" :min="80" :max="200" :step="5" controls-position="right" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最高溢价率">
              <el-input-number v-model="config.max_premium" :min="0" :max="100" :step="5" controls-position="right" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="最小规模">
              <el-input-number v-model="config.min_amount" :min="0.1" :max="10" :step="0.1" :precision="1" controls-position="right" />
              <span style="margin-left: 8px; color: #999;">亿元</span>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最大规模">
              <el-input-number v-model="config.max_amount" :min="1" :max="50" :step="1" controls-position="right" />
              <span style="margin-left: 8px; color: #999;">亿元</span>
            </el-form-item>
          </el-col>
        </el-row>
        
       <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="最低评级">
              <el-select v-model="config.min_rating" placeholder="选择最低评级">
                <el-option label="AAA" value="AAA" />
                <el-option label="AA+" value="AA+" />
                <el-option label="AA" value="AA" />
                <el-option label="AA-" value="AA-" />
                <el-option label="A+" value="A+" />
                <el-option label="A" value="A" />
                <el-option label="A-" value="A-" />
                <el-option label="BBB+" value="BBB+" />
                <el-option label="BBB" value="BBB" />
                <el-option label="BBB-" value="BBB-" />
                <el-option label="B" value="B" />
              </el-select>
            </el-form-item>
          </el-col>
          
          <el-col :span="12">
            <el-form-item label="目标持仓数 (Top N)">
              <el-input-number 
                v-model="config.top_n" 
                :min="1" 
                :max="50" 
                :step="1" 
                controls-position="right" 
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item>
          <el-button type="primary" :loading="loading" @click="runStrategy">
            <el-icon><Search /></el-icon>
            运行策略
          </el-button>
          <el-button @click="resetConfig">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <el-card v-if="result" class="result-card">
      <template #header>
        <div class="card-header">
          <h2>策略结果</h2>
          <el-tag type="success">共 {{ result.total_count }} 只转债</el-tag>
        </div>
      </template>
      
      <el-table :data="result.candidates" stripe border>
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="code" label="代码" width="100" />
        <el-table-column prop="name" label="名称" width="150" />
        <el-table-column prop="price" label="价格" width="100">
          <template #default="{ row }">
            <span :style="{ color: row.price < 100 ? '#67c23a' : '#f56c6c' }">
              {{ row.price.toFixed(2) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="premium_rate" label="溢价率" width="100">
          <template #default="{ row }">
            <span :style="{ color: row.premium_rate < 10 ? '#67c23a' : row.premium_rate > 20 ? '#f56c6c' : '#e6a23c' }">
              {{ row.premium_rate.toFixed(2) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="remain_amount" label="规模" width="100">
          <template #default="{ row }">
            {{ row.remain_amount.toFixed(2) }}亿
          </template>
        </el-table-column>
        <el-table-column prop="rating" label="评级" width="80" />
        <el-table-column prop="dual_low_score" label="双低值" width="100" sortable />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="buyBond(row)">
              购买
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus' // ✅ 引入 MessageBox
import { runStrategy as runStrategyApi, type StrategyConfig, type StrategyResult, type BondCandidate } from '@/api/strategy'
import { executeTrade, type ExecuteTradeRequest } from '@/api/portfolio'

const router = useRouter()
const loading = ref(false)
const config = ref<StrategyConfig>({
  max_price: 130,
  max_premium: 30,
  min_amount: 0.5,
  max_amount: 10,
  min_rating: 'A',
  top_n: 10
})

const result = ref<StrategyResult | null>(null)

const runStrategy = async () => {
  loading.value = true
  try {
    const data = await runStrategyApi(config.value)
    result.value = data
  } catch (error) {
    console.error(error) // ✅ 恢复错误打印
  } finally {
    loading.value = false
  }
}

const resetConfig = () => {
  config.value = {
    max_price: 130,
    max_premium: 30,
    min_amount: 0.5,
    max_amount: 10,
    min_rating: 'A',
    top_n: 10
  }
  result.value = null
}

const buyBond = (bond: BondCandidate) => {
  ElMessageBox.confirm(
    // ✅ 提示语现在是动态的了，会显示你设置的数量
    `确定要执行策略买入吗？\n系统将自动构建排名前 ${config.value.top_n} 的组合。`,
    '交易确认',
    {
      confirmButtonText: '确定下单',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      const request: ExecuteTradeRequest = {
        initial_cash: 100000,
        cash_per_trade: 10000,
        strategy_config: {
          ...config.value,
          // ✅ 关键修复：这里不再是 1，而是读取你界面上填写的数字
          top_n: config.value.top_n 
        },
        is_backtest: false
      }
      
      await executeTrade(request)
      ElMessage.success(`已发送买入 Top ${config.value.top_n} 指令`)
      router.push('/portfolio')
    } catch (error) {
      console.error(error) // ✅ 保留错误打印，方便排查
    }
  }).catch(() => {
    ElMessage.info('已取消交易')
  })
}

</script>

<style scoped>
.strategy-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.config-card,
.result-card {
  background: white;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
  color: #333;
}
</style>
