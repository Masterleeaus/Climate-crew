import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface AgentMetadata {
    id: string;
    name: string;
    description: string;
    category: string;
    icon: string;
    color: string;
    capabilities: string[];
}

export interface ChatResponse {
    response: string;
}

export interface ChatRequest {
    query: string;
}

/**
 * Fetch metadata for all available agents
 */
export const fetchAgentMetadata = async (): Promise<AgentMetadata[]> => {
    try {
        const response = await axios.get(`${API_BASE_URL}/agents/metadata`);
        return response.data.agents;
    } catch (error) {
        console.error('Error fetching agent metadata:', error);
        throw error;
    }
};

/**
 * Fetch detailed information about a specific agent
 */
export const fetchAgentInfo = async (agentName: string): Promise<AgentMetadata> => {
    try {
        const response = await axios.get(`${API_BASE_URL}/agents/${agentName}/info`);
        return response.data;
    } catch (error) {
        console.error(`Error fetching info for agent ${agentName}:`, error);
        throw error;
    }
};

/**
 * Send a chat message to a specific agent
 */
export const chatWithAgent = async (
    agentName: string,
    query: string
): Promise<string> => {
    try {
        const response = await axios.post<ChatResponse>(
            `${API_BASE_URL}/agents/${agentName}/chat`,
            { query },
            {
                timeout: 60000, // 60 second timeout for agent responses
            }
        );
        return response.data.response;
    } catch (error) {
        console.error(`Error chatting with agent ${agentName}:`, error);
        throw error;
    }
};
