import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const AVAILABLE_AGENTS = [
    "air_quality",
    "wildfire",
    "flood",
    "earthquake",
    "deforestation",
    "carbon_emissions",
    "ocean",
    "biodiversity",
    "climate_anomaly",
    "satellite_fusion"
];

// Helper to construct a context-aware prompt for each agent
export const getPromptForAgent = (agentId: string, lat: number, lng: number) => {
    const coords = `(${lat.toFixed(4)}, ${lng.toFixed(4)})`;
    switch (agentId) {
        case 'wildfire': return `Analyze fire risk and active fires for location ${coords}. Be concise.`;
        case 'air_quality': return `Check current air quality (AQI) and pollutants at ${coords}.`;
        case 'flood': return `Assess flood risk and recent precipitation for ${coords}.`;
        case 'ocean': return `Report on ocean conditions, SST, and coral bleaching risk near ${coords}.`;
        case 'biodiversity': return `Identify key species and biodiversity hotpots near ${coords}.`;
        case 'earthquake': return `Check for recent seismic activity near ${coords}.`;
        default: return `Analyze environmental data for ${coords}. Return key insights.`;
    }
};

export const queryAgent = async (agentId: string, query: string) => {
    try {
        const response = await apiClient.post(`/agents/${agentId}/chat`, { query });
        return { agentId, status: 'success', data: response.data.response };
    } catch (error) {
        console.error(`Error querying ${agentId}:`, error);
        return { agentId, status: 'error', error: error };
    }
};
