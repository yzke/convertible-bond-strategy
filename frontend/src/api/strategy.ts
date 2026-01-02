import apiClient from './index'

export interface BondCandidate {
  code: string
  name: string
  price: number
  premium_rate: number
  remain_amount: number
  rating: string | null
  dual_low_score: number
}

export interface StrategyConfig {
  max_price: number
  max_premium: number
  min_amount: number
  max_amount: number
  min_rating: string
  top_n: number
}

export interface StrategyResult {
  candidates: BondCandidate[]
  total_count: number
  run_time: string
}

export const runStrategy = async (config: StrategyConfig): Promise<StrategyResult> => {
  return await apiClient.post('/strategy/run', config)
}

export const getCandidates = async (params: {
  max_price?: number
  max_premium?: number
  min_rating?: string
  top_n?: number
}): Promise<StrategyResult> => {
  return await apiClient.get('/strategy/candidates', { params })
}


