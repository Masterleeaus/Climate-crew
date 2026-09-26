import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export interface NewsArticle {
    id: string;
    title: string;
    summary?: string;
    source: string;
    url: string;
    published_at: string;
    image_url?: string;
    bucket: string;
    tags: string[];
    score?: number;
}

export interface ArticleChatRequest {
    message: string;
    article_id: string;
    deep_research?: boolean;
    conversation_id?: string;
}

export interface ArticleChatResponse {
    answer: string;
    citations: Array<{
        type: string;
        title: string;
        url: string;
        source: string;
    }>;
    related_articles: Array<{
        id: string;
        title: string;
        url: string;
        source: string;
    }>;
    conversation_id: string;
    deep_research_used: boolean;
}

export const newsApi = {
    // Search news articles
    searchNews: async (params?: {
        query?: string;
        bucket?: string[];
        limit?: number;
        offset?: number;
        use_vector_search?: boolean;
        recency_boost?: boolean;
    }) => {
        const response = await axios.get<NewsArticle[]>(`${API_BASE_URL}/news`, { params });
        return response.data;
    },

    // Get a specific article by ID
    getArticle: async (articleId: string) => {
        const response = await axios.get<NewsArticle>(`${API_BASE_URL}/news/${articleId}`);
        return response.data;
    },

    // Chat about a specific article
    chatAboutArticle: async (articleId: string, request: ArticleChatRequest) => {
        const response = await axios.post<ArticleChatResponse>(
            `${API_BASE_URL}/news/chat/article/${articleId}`,
            request
        );
        return response.data;
    },

    // Get related articles
    getRelatedArticles: async (articleId: string, limit: number = 5) => {
        const response = await axios.get(`${API_BASE_URL}/news/${articleId}/related`, {
            params: { limit }
        });
        return response.data;
    },

    // Get conversation history for an article
    getConversationHistory: async (articleId: string, conversationId: string) => {
        const response = await axios.get(`${API_BASE_URL}/news/chat/article/${articleId}/history`, {
            params: { conversation_id: conversationId }
        });
        return response.data;
    }
};
