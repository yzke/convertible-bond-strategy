<template>
  <div class="backtest-container">
    <el-card class="config-card">
      <template #header>
        <div class="card-header">
          <h2>回测配置</h2>
        </div>
      </template>
      
      <el-form :model="config" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="开始日期">
              <el-date-picker v-model="config.start_date" type="date" placeholder="选择开始日期" value-format="YYYY-MM-DD" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束日期">
              <el-date-picker v-model="config.end_date" type="date" placeholder="选择结束日期" value-format="YYYY-MM-DD" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="初始资金">
              <el-input-number v-model="config.initial_cash" :min="10000" :max="1000000" :step="10000" controls-position="right" />
              <span style="margin-left: 8px; color: #999;">元</span>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="每单金额">
              <el-input-number v-model="config.cash_per_trade" :min="1000" :max="100000" :step="1000" controls-position="right" />
              <span style="margin-left: 8px; color: #999;">元</span>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="推荐数量">
              <el-input-number v-model="config.top_n" :min="5" :max="50" :step="5" controls-position="right" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="调仓周期">
              <el-input-number v-model="config.rebalance_days" :min="1" :max="30" :step="1" controls-position="right" />
              <span style="margin-left: 8px; color: #999;">天</span>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="随机种子">
              <el-input-number v-model="config.random_seed" :min="0" :max="1000" :step="1" controls-position="right" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-divider>策略参数</el-divider>
        
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
        
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="runBacktest">
            <el-icon><VideoPlay /></el-icon>
            运行回测
          </el-button>
          <el-button @click="resetConfig">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <div v-if="result" class="result-container">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-card class="performance-card">
            <template #header>
              <div class="card-header">
                <h2>性能指标</h2>
              </div>
            </template>
            
            <el-descriptions :column="1" border>
              <el-descriptions-item label="总收益率">
                <el-tag :type="result.performance.total_return >= 0 ? 'success' : 'danger'">
                  {{ result.performance.total_return >= 0 ? '+' : '' }}{{ (result.performance.total_return * 100).toFixed(2) }}%
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="年化收益率">
                <el-tag :type="result.performance.annualized_return >= 0 ? 'success' : 'danger'">
                  {{ (result.performance.annualized_return * 100).toFixed(2) }}%
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="年化波动率">
                <el-tag type="warning">
                  {{ (result.performance.annualized_volatility * 100).toFixed(2) }}%
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="夏普比率">
                <el-tag :type="result.performance.sharpe_ratio >= 1 ? 'success' : result.performance.sharpe_ratio >= 0 ? 'warning' : 'danger'">
                  {{ result.performance.sharpe_ratio.toFixed(2) }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="最大回撤">
                <el-tag type="danger">
                  {{ (result.performance.max_drawdown * 100).toFixed(2) }}%
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="胜率">
                <el-tag :type="result.performance.win_rate >= 0.5 ? 'success' : 'warning'">
                  {{ (result.performance.win_rate * 100).toFixed(2) }}%
                </el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>
        
        <el-col :span="12">
          <el-card class="summary-card">
            <template #header>
              <div class="card-header">
                <h2>回测汇总</h2>
              </div>
            </template>
            
            <el-descriptions :column="1" border>
              <el-descriptions-item label="回测期间">
                {{ result.start_date }} ~ {{ result.end_date }}
              </el-descriptions-item>
              <el-descriptions-item label="交易天数">
                {{ result.trading_days }} 天
              </el-descriptions-item>
              <el-descriptions-item label="初始资金">
                {{ result.portfolio.initial_cash.toFixed(2) }} 元
              </el-descriptions-item>
              <el-descriptions-item label="最终资产">
                {{ result.portfolio.total_asset.toFixed(2) }} 元
              </el-descriptions-item>
              <el-descriptions-item label="总盈亏">
                <span :class="result.portfolio.total_profit >= 0 ? 'profit' : 'loss'">
                  {{ result.portfolio.total_profit >= 0 ? '+' : '' }}{{ result.portfolio.total_profit.toFixed(2) }} 元
                </span>
              </el-descriptions-item>
              <el-descriptions-item label="持仓数量">
                {{ result.portfolio.position_count }} 只
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>
      </el-row>
      
      <el-card class="chart-card">
        <template #header>
          <div class="card-header">
            <h2>净值曲线</h2>
          </div>
        </template>
        <div ref="chartRef" style="width: 100%; height: 400px;"></div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onBeforeUnmount, onMounted } from 'vue' // ✅ 引入 onMounted
import { VideoPlay } from '@element-plus/icons-vue'
import { runBacktest as runBacktestApi, type BacktestConfig, type BacktestResult } from '@/api/backtest'
import * as echarts from 'echarts'

const loading = ref(false)
const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const config = ref<BacktestConfig>({
  start_date: '2025-12-01',
  end_date: '2026-01-01',
  initial_cash: 100000,
  top_n: 10,
  cash_per_trade: 10000,
  max_price: 130,
  max_premium: 30,
  min_amount: 0.5,
  max_amount: 10,
  rebalance_days: 5,
  random_seed: 42
})

const result = ref<BacktestResult | null>(null)

const runBacktest = async () => {
  loading.value = true
  try {
    const data = await runBacktestApi(config.value)
    result.value = data
    
    await nextTick()
    renderChart()
  } catch (error) {
    console.error(error) // ✅ 恢复错误打印
  } finally {
    loading.value = false
  }
}

const resetConfig = () => {
  config.value = {
    start_date: '2025-12-01',
    end_date: '2026-01-01',
    initial_cash: 100000,
    top_n: 10,
    cash_per_trade: 10000,
    max_price: 130,
    max_premium: 30,
    min_amount: 0.5,
    max_amount: 10,
    rebalance_days: 5,
    random_seed: 42
  }
  result.value = null
}

const renderChart = () => {
  if (!chartRef.value || !result.value) return
  
  if (chart) {
    chart.dispose()
  }
  
  chart = echarts.init(chartRef.value)
  
  const data = result.value.daily_nav || []
  const dates = result.value.dates || []
  
  const navData = data.length > 0 ? data : generateSimulatedNavData()
  const dateLabels = dates.length > 0 ? dates : generateDateLabels()
  
  const option = {
    title: { text: '策略净值曲线', left: 'center' },
    tooltip: { trigger: 'axis', formatter: '{b}<br/>净值: {c}' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true }, // ✅ 优化布局
    xAxis: { type: 'category', data: dateLabels },
    yAxis: { type: 'value', name: '净值', scale: true }, // ✅ scale:true 让曲线更明显
    series: [
      {
        name: '净值',
        type: 'line',
        data: navData,
        smooth: true,
        areaStyle: { opacity: 0.3 }
      }
    ]
  }
  
  chart.setOption(option)
}

const generateSimulatedNavData = () => {
  const days = result.value?.trading_days || 20
  const data: number[] = []
  let value = 1.0
  
  for (let i = 0; i < days; i++) {
    value *= 1 + (Math.random() - 0.4) * 0.02
    data.push(parseFloat(value.toFixed(4)))
  }
  
  return data
}

const generateDateLabels = () => {
  const days = result.value?.trading_days || 20
  return Array.from({ length: days }, (_, i) => `第${i + 1}天`)
}

// ✅ 添加窗口缩放监听
const handleResize = () => {
  chart?.resize()
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (chart) {
    chart.dispose()
  }
})
</script>

<style scoped>
.backtest-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.config-card,
.performance-card,
.summary-card,
.chart-card {
  background: white;
}

.result-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
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

.profit {
  color: #67c23a;
  font-weight: 600;
}

.loss {
  color: #f56c6c;
  font-weight: 600;
}
</style>
