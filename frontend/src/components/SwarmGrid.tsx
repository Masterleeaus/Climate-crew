import React from 'react';
import InsightCard from './InsightCard';
import LocationStatusCard from './LocationStatusCard';
import { AgentResult } from '../hooks/useAgentSwarm';

interface SwarmGridProps {
    results: Record<string, AgentResult>;
    isVisible: boolean;
    location: { lat: number; lng: number } | null;
    onClose: () => void;
}

const SwarmGrid: React.FC<SwarmGridProps> = ({ results, isVisible, location, onClose }) => {
    if (!isVisible || !location) return null;

    return (
        <div className="absolute inset-0 z-20 pointer-events-none p-6 pt-24 pb-8">
            <div className="w-full h-full grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 grid-rows-3 gap-6">

                {/* 1. Location Status (Top-Left Fixed Slot) */}
                <div className="pointer-events-auto col-span-1 row-span-1">
                    <LocationStatusCard lat={location.lat} lng={location.lng} agentCount={Object.keys(results).length} onClose={onClose} />
                </div>

                {/* 2. Map Agents to Remaining Slots */}
                {Object.values(results).map((agent, index) => (
                    <div key={agent.agentId} className="pointer-events-auto min-h-[200px] flex flex-col">
                        <InsightCard
                            agentId={agent.agentId}
                            status={agent.status}
                            data={agent.data}
                            delay={0.1 + (index * 0.05)}
                        />
                    </div>
                ))}
            </div>
        </div>
    );
};

export default SwarmGrid;
