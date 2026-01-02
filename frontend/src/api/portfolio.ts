import apiClient from './index'
import { StrategyConfig } from './strategy'

export interface Position {
  symbol: string
  quantity: number
  quantity_hands: number
  avg_price: number
  current_price: number
  market_value: number
  profit: number
  profit_rate: number
}

export interface TradeRecord {
  symbol: string
  action: string
  quantity: number
  price: number
  amount: number
  commission: number
  trade_time: string
}

export interface PortfolioSummary {
  positions: Position[]
  cash: number
  market_value: number
  total_asset: number
  total_profit: number
  profit_rate: number
  initial_cash: number
  position_count: number
}

export interface ExecuteTradeRequest {
  initial_cash: number
  cash_per_trade: number
  strategy_config: StrategyConfig
  is_backtest: boolean
}

export const executeTrade = async (request: ExecuteTradeRequest): Promise<PortfolioSummary> => {
  return await apiClient.post('/portfolio/execute', request)
}

export const getPortfolioSummary = async (): Promise<PortfolioSummary> => {
  return await apiClient.get('/portfolio/summary')
}

export const getTradeHistory = async (): Promise<TradeRecord[]> => {
  return await apiClient.get('/portfolio/history')
}

