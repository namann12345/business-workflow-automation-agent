import React from 'react';
import { Bot, Activity, Hexagon } from 'lucide-react';

const Header = () => {
    return (
        <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50">
            <div className="container mx-auto px-4 h-16 flex items-center justify-between max-w-5xl">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-900/20">
                        <Hexagon className="w-6 h-6 text-white" />
                    </div>
                    <div>
                        <h1 className="font-bold text-xl tracking-tight text-white flex items-center gap-2">
                            Workflow<span className="text-blue-400">Agent</span>
                        </h1>
                    </div>
                </div>

                <div className="flex items-center gap-4 text-sm text-slate-400">
                    <div className="flex items-center gap-2 bg-slate-800 px-3 py-1.5 rounded-full border border-slate-700">
                        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                        System Online
                    </div>
                </div>
            </div>
        </header>
    );
};

export default Header;
