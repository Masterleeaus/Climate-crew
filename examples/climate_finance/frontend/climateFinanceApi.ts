import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export interface PillarScores {
    physical_risk: number | null;
    transition_risk: number | null;
    financial_vulnerability: number | null;
    market_sentiment: number | null;
}

export interface FeatureContribution {
    feature: string;
    value: string;
    percentile: number | null;
    risk_impact: number | null;
    weight: number | null;
    correlation: number | null;
    direction: string;
}

export interface ScoreBreakdown {
    source: string;
    pillars: PillarScores;
    feature_contributions: FeatureContribution[];
}

export interface ClimateRisk {
    ticker: string;
    company: string;
    sector: string;
    industry?: string;
    risk_score: number;
    risk_level: string;
    key_risks: string[];
    score_breakdown?: ScoreBreakdown;
    historical_volatility?: number;
}

export interface PortfolioRisk {
    portfolio_size: number;
    analyzed: number;
    weighted_risk: number;
    risk_level: string;
    stocks: Array<{
        ticker: string;
        company: string;
        sector: string;
        risk_score: number;
        risk_level: string;
        market_cap: number;
    }>;
}

export interface CarbonPrice {
    id: string;
    name: string;
    type: string;
    price_usd: number;
    price_local: number;
    currency: string;
    jurisdiction: string;
    coverage: string;
    sectors: string[];
    trend: string;
    last_updated: string;
}

export interface CarbonPricesResponse {
    count: number;
    prices: CarbonPrice[];
    highest: CarbonPrice | null;
    average_usd: number;
    source: string;
}

export interface StockQuote {
    ticker: string;
    price: number | null;
    previous_close: number | null;
    open: number | null;
    day_high: number | null;
    day_low: number | null;
    volume: number | null;
    market_cap: number | null;
    currency: string;
    fifty_two_week_high: number | null;
    fifty_two_week_low: number | null;
    timestamp: string;
    source: string;
}

export interface ESGScore {
    ticker: string;
    total_score: number;
    environment_score: number;
    social_score: number;
    governance_score: number;
    [key: string]: any;
}

export const climateFinanceApi = {
    // Chat with Climate Finance Agent
    chat: async (message: string) => {
        const response = await axios.post(`${API_BASE_URL}/climate-finance/chat`, {
            query: message
        });
        return response.data;
    },

    // Get individual stock climate risk
    getStockRisk: async (ticker: string): Promise<ClimateRisk> => {
        const response = await axios.get(`${API_BASE_URL}/climate-finance/stock/${ticker}/climate-risk`);
        return response.data;
    },

    // Get portfolio risk analysis
    getPortfolioRisk: async (tickers: string[]): Promise<PortfolioRisk> => {
        const response = await axios.post(`${API_BASE_URL}/climate-finance/portfolio/climate-risk`, {
            tickers
        });
        return response.data;
    },

    // Get global carbon prices
    getCarbonPrices: async (): Promise<CarbonPricesResponse> => {
        const response = await axios.get(`${API_BASE_URL}/climate-finance/carbon-prices`);
        return response.data;
    },

    // Get regulatory risk for a country
    getCountryRisk: async (countryCode: string) => {
        const response = await axios.get(`${API_BASE_URL}/climate-finance/country/${countryCode}/regulatory-risk`);
        return response.data;
    },

    // Get ESG scores
    getESGScores: async (ticker: string): Promise<ESGScore> => {
        const response = await axios.get(`${API_BASE_URL}/climate-finance/stock/${ticker}/esg`);
        return response.data;
    },

    // Get stock quote / price
    getStockQuote: async (ticker: string): Promise<StockQuote> => {
        const response = await axios.get(`${API_BASE_URL}/climate-finance/stock/${ticker}/quote`);
        return response.data;
    }
};
