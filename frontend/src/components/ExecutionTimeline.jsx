import React from 'react';
import { CheckCircle2, XCircle, Clock, ChevronRight } from 'lucide-react';
import { motion } from 'framer-motion';

const ExecutionTimeline = ({ execution }) => {
    if (!execution || !execution.steps) return null;

    return (
        <div className="glass-panel p-6">
            <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                <ActivityIcon /> Execution Trace
            </h3>

            <div className="space-y-4">
                {execution.steps.map((step, idx) => (
                    <motion.div
                        key={idx}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: idx * 0.1 }}
                        className="flex items-start gap-4 group"
                    >
                        <div className="mt-1 relative">
                            <div className="absolute top-6 bottom-0 left-1/2 -ml-px w-0.5 bg-slate-700/50 group-last:hidden" />
                            {step.status === 'success' ? (
                                <div className="w-5 h-5 rounded-full bg-emerald-500/20 flex items-center justify-center border border-emerald-500/30">
                                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                                </div>
                            ) : (
                                <div className="w-5 h-5 rounded-full bg-red-500/20 flex items-center justify-center border border-red-500/30">
                                    <XCircle className="w-3.5 h-3.5 text-red-400" />
                                </div>
                            )}
                        </div>

                        <div className="flex-1 pb-4">
                            <div className="flex items-center justify-between">
                                <p className="font-medium text-slate-200">{step.name}</p>
                                <div className="flex items-center gap-1.5 text-xs text-slate-400 bg-slate-800/50 px-2 py-1 rounded-md border border-slate-700/50">
                                    <Clock className="w-3 h-3" />
                                    {step.duration_ms} ms
                                </div>
                            </div>

                            {step.error && (
                                <p className="mt-2 text-sm text-red-400 bg-red-900/20 p-2.5 rounded-lg border border-red-900/50">
                                    {step.error}
                                </p>
                            )}
                        </div>
                    </motion.div>
                ))}
            </div>
        </div>
    );
};

const ActivityIcon = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-blue-400">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
    </svg>
);

export default ExecutionTimeline;
