import apiClient from './index'
import { PortfolioSummary, TradeRecord } from './portfolio'

export interface PerformanceMetrics {
  total_return: number
  annualized_return: number
  annualized_volatility: number
  sharpe_ratio: number
  max_drawdown: number
  win_rate: number
}

export interface BacktestConfig {
  start_date: string
  end_date: string
  initial_cash: number
  top_n: number
  cash_per_trade: number
  max_price: number
  max_premium: number
  min_amount: number
  max_amount: number
  rebalance_days: number
  random_seed: number
}

export interface BacktestResult {
  performance: PerformanceMetrics
  portfolio: PortfolioSummary
  trade_history: TradeRecord[]
  daily_nav: number[]
  dates: string[]
  start_date: string
  end_date: string
  trading_days: number
  run_time: string
}

export const runBacktest = async (config: BacktestConfig): Promise<BacktestResult> => {
  return await apiClient.post('/backtest/run', config)
}

