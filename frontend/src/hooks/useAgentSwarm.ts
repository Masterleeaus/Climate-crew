import { useState, useCallback } from 'react';
import { queryAgent, AVAILABLE_AGENTS, getPromptForAgent } from '../services/api';

export interface AgentResult {
    agentId: string;
    status: 'pending' | 'success' | 'error';
    data?: string;
    error?: any;
    startTime: number;
    endTime?: number;
}

export const useAgentSwarm = () => {
    const [results, setResults] = useState<Record<string, AgentResult>>({});
    const [isSwarmRunning, setIsSwarmRunning] = useState(false);

    const triggerSwarm = useCallback(async (lat: number, lng: number) => {
        setIsSwarmRunning(true);
        const newResults: Record<string, AgentResult> = {};

        // 1. Initialize all agents as "pending" immediately (for UI skeletons)
        AVAILABLE_AGENTS.forEach(agentId => {
            newResults[agentId] = {
                agentId,
                status: 'pending',
                startTime: Date.now()
            };
        });
        setResults(newResults);

        // 2. Fire requests concurrently (Parallel Execution)
        const promises = AVAILABLE_AGENTS.map(async (agentId) => {
            const prompt = getPromptForAgent(agentId, lat, lng);

            // Artificial stagger for visual "pop-in" effect (optional, remove for pure speed)
            // await new Promise(r => setTimeout(r, Math.random() * 1000));

            const response = await queryAgent(agentId, prompt);

            setResults(prev => ({
                ...prev,
                [agentId]: {
                    ...prev[agentId],
                    status: response.status as 'success' | 'error',
                    data: response.data,
                    error: response.error,
                    endTime: Date.now()
                }
            }));
        });

        // 3. Wait for all to finish (just to update global loading state)
        await Promise.allSettled(promises);
        setIsSwarmRunning(false);
        console.log("All agents finished.");

    }, []);

    return { results, isSwarmRunning, triggerSwarm };
};
