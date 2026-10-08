import React from 'react';
import { Target, AlertTriangle, Bot, Cpu } from 'lucide-react';
import { motion } from 'framer-motion';

const WorkflowCard = ({ routing }) => {
    if (!routing) return null;

    const { workflow_id, confidence, reason, needs_clarification } = routing;

    const isLLMFallback = reason && reason.toLowerCase().includes('llm unavailable');
    const isLLMAI = !isLLMFallback && reason && !needs_clarification;

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`glass-panel p-6 ${needs_clarification ? 'border-amber-500/30' : 'border-blue-500/20'}`}
        >
            <div className="flex items-start gap-4">
                <div className={`p-3 rounded-xl ${needs_clarification ? 'bg-amber-500/10 text-amber-500' : 'bg-blue-500/10 text-blue-400'}`}>
                    {needs_clarification ? <AlertTriangle className="w-6 h-6" /> : <Target className="w-6 h-6" />}
                </div>
                <div className="flex-1">
                    <div className="flex items-center justify-between gap-2 flex-wrap">
                        <h3 className="text-lg font-semibold text-slate-100">
                            {workflow_id ? `Selected: ${workflow_id}` : 'Workflow Selection'}
                        </h3>
                        <div className="flex items-center gap-2">
                            {/* LLM / Fallback badge */}
                            {isLLMFallback && (
                                <span className="flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                                    <Cpu className="w-3 h-3" />
                                    Fallback Mode
                                </span>
                            )}
                            {isLLMAI && workflow_id && (
                                <span className="flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-300 border border-blue-500/20">
                                    <Bot className="w-3 h-3" />
                                    AI Router
                                </span>
                            )}
                            {/* Confidence badge */}
                            {confidence > 0 && (
                                <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${confidence > 0.8
                                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                        : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                                    }`}>
                                    {Math.round(confidence * 100)}% Match
                                </span>
                            )}
                        </div>
                    </div>
                    <p className="mt-2 text-slate-400 text-sm leading-relaxed">
                        {reason}
                    </p>
                </div>
            </div>
        </motion.div>
    );
};

export default WorkflowCard;
