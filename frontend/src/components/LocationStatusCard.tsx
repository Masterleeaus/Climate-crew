import React from 'react';
import { motion } from 'framer-motion';
import { Activity, Globe, X } from 'lucide-react';

interface LocationStatusCardProps {
    lat: number;
    lng: number;
    agentCount: number;
    onClose: () => void;
}

const LocationStatusCard: React.FC<LocationStatusCardProps> = ({ lat, lng, agentCount, onClose }) => {
    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="col-span-1 md:col-span-2 lg:col-span-1 glass-card p-6 border-neon-blue/50 shadow-[0_0_20px_rgba(0,243,255,0.15)] relative overflow-hidden group"
        >
            {/* Animated Background Mesh */}
            <div className="absolute inset-0 bg-gradient-to-br from-neon-blue/10 to-transparent opacity-20 group-hover:opacity-30 transition-opacity" />

            {/* Close Button */}
            <button
                onClick={onClose}
                className="absolute top-3 right-3 p-1.5 rounded-full bg-white/5 hover:bg-white/20 text-gray-400 hover:text-white transition-all z-20"
                title="Clear Scan"
            >
                <X className="w-4 h-4" />
            </button>

            <div className="relative z-10">
                <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-lg bg-neon-blue/20 flex items-center justify-center border border-neon-blue/50">
                        <Globe className="w-6 h-6 text-neon-blue" />
                    </div>
                    <div>
                        <h2 className="text-sm font-bold text-neon-blue tracking-widest uppercase">Target Locked</h2>
                        <div className="flex items-center gap-2 text-xs text-gray-400">
                            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                            <span>Live Feed Active</span>
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-4 my-4">
                    <div className="bg-black/40 rounded p-3 border border-white/5">
                        <label className="text-[10px] text-gray-500 uppercase tracking-wider">Latitude</label>
                        <p className="text-xl font-mono text-white">{lat.toFixed(4)}° N</p>
                    </div>
                    <div className="bg-black/40 rounded p-3 border border-white/5">
                        <label className="text-[10px] text-gray-500 uppercase tracking-wider">Longitude</label>
                        <p className="text-xl font-mono text-white">{lng.toFixed(4)}° E</p>
                    </div>
                </div>

                <div className="flex items-center justify-between mt-4 text-xs font-mono text-gray-400 border-t border-white/10 pt-3">
                    <div className="flex items-center gap-2">
                        <Activity className="w-4 h-4 text-neon-purple" />
                        <span>Swarm Status:</span>
                    </div>
                    <span className="text-white bg-white/10 px-2 py-0.5 rounded">{agentCount} Agents Deployed</span>
                </div>
            </div>
        </motion.div>
    );
};

export default LocationStatusCard;
