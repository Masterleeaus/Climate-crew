import React, { useState } from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import {
    LayoutDashboard,
    Globe,
    Microscope,
    FileCheck,
    ShoppingBag,
    DollarSign,
    MessageSquare,
    Menu,
    X,
    Siren
} from 'lucide-react';

const DashboardLayout: React.FC = () => {
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const location = useLocation();

    const navItems = [
        { path: '/app', label: 'Overview', icon: LayoutDashboard },
        { path: '/app/globe', label: 'Earth Observatory', icon: Globe },
        { path: '/app/research', label: 'Research', icon: Microscope },
        { path: '/app/audit', label: 'Environmental Analysis', icon: FileCheck },
        { path: '/app/retail', label: 'Applied Research', icon: ShoppingBag },
        { path: '/app/finance', label: 'Climate Finance', icon: DollarSign },
        { path: '/app/disaster', label: 'Hazards & Resilience', icon: Siren },
        { path: '/app/chat', label: 'Research Crew', icon: MessageSquare },
    ];

    return (
        <div className="flex h-screen w-screen bg-black overflow-hidden text-white font-sans selection:bg-neon-blue selection:text-black">
            <aside
                className={`fixed inset-y-0 left-0 z-50 w-64 bg-glass-900 border-r border-white/10 backdrop-blur-xl transition-transform duration-300 ease-in-out ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'} lg:relative lg:translate-x-0 flex flex-col`}
            >
                <div className="h-20 flex items-center px-6 border-b border-white/10">
                    <div>
                        <h1 className="text-xl font-black tracking-[0.12em]">
                            CLIMATE <span className="text-neon-blue">CREW</span>
                        </h1>
                        <p className="mt-1 text-[9px] uppercase tracking-[0.24em] text-gray-500">Climate Research Agent Team</p>
                    </div>
                </div>

                <nav className="flex-1 overflow-y-auto py-6 px-3 space-y-1 custom-scrollbar-hidden">
                    {navItems.map((item) => {
                        const isActive = location.pathname === item.path;
                        return (
                            <NavLink
                                key={item.path}
                                to={item.path}
                                onClick={() => setIsSidebarOpen(false)}
                                className={({ isActive }) => `flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group ${isActive ? 'bg-neon-blue/10 text-neon-blue shadow-[0_0_15px_rgba(0,243,255,0.1)] border border-neon-blue/20' : 'text-gray-400 hover:text-white hover:bg-white/5'}`}
                            >
                                <item.icon className={`w-5 h-5 ${isActive ? 'text-neon-blue' : 'group-hover:text-neon-blue'}`} />
                                <span className="font-medium tracking-wide">{item.label}</span>
                                {isActive && <div className="ml-auto w-1.5 h-1.5 rounded-full bg-neon-blue shadow-[0_0_8px_cyan]" />}
                            </NavLink>
                        );
                    })}
                </nav>

                <div className="p-4 border-t border-white/10">
                    <div className="flex items-center gap-3 p-3 rounded-lg bg-white/5 border border-white/5">
                        <div className="relative w-8 h-8 rounded-full bg-gradient-to-tr from-neon-purple to-neon-blue">
                            <span className="absolute right-0 bottom-0 w-2.5 h-2.5 rounded-full bg-green-400 border-2 border-black" />
                        </div>
                        <div>
                            <p className="text-xs font-bold text-white">Research Workspace</p>
                            <p className="text-[10px] text-gray-400">Agent team ready</p>
                        </div>
                    </div>
                </div>
            </aside>

            {isSidebarOpen && (
                <button
                    aria-label="Close navigation"
                    onClick={() => setIsSidebarOpen(false)}
                    className="fixed inset-0 z-40 bg-black/60 lg:hidden"
                />
            )}

            <main className="flex-1 relative overflow-hidden flex flex-col">
                <button
                    aria-label={isSidebarOpen ? 'Close navigation' : 'Open navigation'}
                    onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                    className="lg:hidden absolute top-4 left-4 z-[60] p-2 glass-card rounded-lg text-white"
                >
                    {isSidebarOpen ? <X size={20} /> : <Menu size={20} />}
                </button>

                <div className="flex-1 w-full h-full overflow-y-auto relative bg-grid-pattern">
                    <Outlet />
                </div>
            </main>
        </div>
    );
};

export default DashboardLayout;
