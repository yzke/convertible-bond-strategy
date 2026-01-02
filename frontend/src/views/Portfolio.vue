<template>
  <div class="portfolio-container">
    <el-row :gutter="20">
      <el-col :span="16">
        <el-card class="positions-card">
          <template #header>
            <div class="card-header">
              <h2>持仓明细</h2>
              <el-tag type="info">共 {{ portfolio?.position_count || 0 }} 只</el-tag>
            </div>
          </template>
          
          <el-table :data="portfolio?.positions || []" stripe border>
            <el-table-column type="index" label="序号" width="60" />
            <el-table-column prop="symbol" label="代码" width="100" />
            <el-table-column prop="quantity" label="数量" width="100" />
            <el-table-column prop="quantity_hands" label="手数" width="80" />
            <el-table-column prop="avg_price" label="成本价" width="100">
              <template #default="{ row }">
                {{ row.avg_price.toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column prop="current_price" label="现价" width="100">
              <template #default="{ row }">
                {{ row.current_price.toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column prop="market_value" label="市值" width="120">
              <template #default="{ row }">
                {{ row.market_value.toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column prop="profit" label="盈亏" width="120">
              <template #default="{ row }">
                <span :style="{ color: row.profit >= 0 ? '#67c23a' : '#f56c6c' }">
                  {{ row.profit >= 0 ? '+' : '' }}{{ row.profit.toFixed(2) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="profit_rate" label="盈亏率" width="120">
              <template #default="{ row }">
                <el-tag :type="row.profit_rate >= 0 ? 'success' : 'danger'">
                  {{ row.profit_rate >= 0 ? '+' : '' }}{{ row.profit_rate.toFixed(2) }}%
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card class="summary-card">
          <template #header>
            <div class="card-header">
              <h2>账户汇总</h2>
            </div>
          </template>
          
          <el-descriptions :column="1" border>
            <el-descriptions-item label="总资产">
              <span class="amount">{{ portfolio?.total_asset?.toFixed(2) || '0.00' }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="可用资金">
              <span class="amount">{{ portfolio?.cash?.toFixed(2) || '0.00' }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="持仓市值">
              <span class="amount">{{ portfolio?.market_value?.toFixed(2) || '0.00' }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="总盈亏">
              <span :class="['amount', (portfolio?.total_profit || 0) >= 0 ? 'profit' : 'loss']">
                {{ (portfolio?.total_profit || 0) >= 0 ? '+' : '' }}{{ portfolio?.total_profit?.toFixed(2) || '0.00' }}
              </span>
            </el-descriptions-item>
            <el-descriptions-item label="盈亏率">
              <el-tag :type="(portfolio?.profit_rate || 0) >= 0 ? 'success' : 'danger'">
                {{ (portfolio?.profit_rate || 0) >= 0 ? '+' : '' }}{{ portfolio?.profit_rate?.toFixed(2) || '0.00' }}%
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
    
    <el-card class="history-card">
      <template #header>
        <div class="card-header">
          <h2>交易历史</h2>
          <el-button type="primary" size="small" @click="refreshHistory">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>
      
      <el-table :data="tradeHistory" stripe border>
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="trade_time" label="时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.trade_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="symbol" label="代码" width="100" />
        <el-table-column prop="action" label="操作" width="80">
          <template #default="{ row }">
            <el-tag :type="row.action === 'buy' ? 'success' : 'danger'">
              {{ row.action === 'buy' ? '买入' : '卖出' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="quantity" label="数量" width="100" />
        <el-table-column prop="price" label="价格" width="100">
          <template #default="{ row }">
            {{ row.price.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="金额" width="120">
          <template #default="{ row }">
            {{ row.amount.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="commission" label="手续费" width="100">
          <template #default="{ row }">
            {{ row.commission.toFixed(2) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { getPortfolioSummary, getTradeHistory, type PortfolioSummary, type TradeRecord } from '@/api/portfolio'

const portfolio = ref<PortfolioSummary | null>(null)
const tradeHistory = ref<TradeRecord[]>([])

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const refreshHistory = async () => {
  await loadPortfolio()
  await loadTradeHistory()
}

const loadPortfolio = async () => {
  try {
    const data = await getPortfolioSummary()
    portfolio.value = data
  } catch (error) {
    console.error('加载持仓失败:', error)
  }
}

const loadTradeHistory = async () => {
  try {
    const data = await getTradeHistory()
    tradeHistory.value = data
  } catch (error) {
    console.error('加载交易历史失败:', error)
  }
}

onMounted(() => {
  loadPortfolio()
  loadTradeHistory()
})
</script>

<style scoped>
.portfolio-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.positions-card,
.summary-card,
.history-card {
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

.amount {
  font-size: 18px;
  font-weight: 600;
}

.amount.profit {
  color: #67c23a;
}

.amount.loss {
  color: #f56c6c;
}
</style>
