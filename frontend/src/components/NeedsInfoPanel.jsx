import React from 'react';
import { motion } from 'framer-motion';
import { AlertCircle, ArrowRight } from 'lucide-react';

/**
 * NeedsInfoPanel — shown when a workflow needs more information from the user.
 * Rendered for execution status = "needs_clarification".
 */
const NeedsInfoPanel = ({ result }) => {
    if (!result) return null;

    const message = result.message || 'Additional information is required to proceed.';
    const missingFields = result.missing_fields || [];

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="glass-panel overflow-hidden border-amber-500/30 bg-gradient-to-b from-amber-900/10 to-slate-900/80"
        >
            {/* Header */}
            <div className="px-6 py-4 border-b border-white/5 bg-amber-500/5 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <AlertCircle className="w-5 h-5 text-amber-400" />
                    <h3 className="text-lg font-semibold text-amber-300">Needs Information</h3>
                </div>
                <div className="px-2.5 py-1 bg-amber-500/20 text-amber-300 text-xs font-semibold rounded-full border border-amber-500/30">
                    Awaiting Input
                </div>
            </div>

            <div className="p-6 space-y-4">
                {/* Message */}
                <div className="text-slate-300 leading-relaxed whitespace-pre-line">
                    {message}
                </div>

                {/* Missing fields as visual list */}
                {missingFields.length > 0 && (
                    <div className="space-y-2">
                        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                            Missing Information
                        </p>
                        {missingFields.map((field, i) => (
                            <div
                                key={field}
                                className="flex items-center gap-3 bg-amber-900/20 border border-amber-700/30 rounded-lg px-3 py-2"
                            >
                                <span className="w-5 h-5 rounded-full bg-amber-500/20 text-amber-400 text-xs font-bold flex items-center justify-center flex-shrink-0">
                                    {i + 1}
                                </span>
                                <span className="text-sm text-amber-200 font-medium">{field.replace(/_/g, ' ')}</span>
                            </div>
                        ))}
                    </div>
                )}

                {/* Next action hint */}
                <div className="flex items-center gap-2 text-sm text-slate-400 bg-slate-800/40 rounded-lg px-3 py-2 border border-slate-700/40">
                    <ArrowRight className="w-4 h-4 text-blue-400 flex-shrink-0" />
                    <span>Type your response in the input box above and click <strong className="text-slate-300">Run Workflow</strong> again.</span>
                </div>
            </div>
        </motion.div>
    );
};

export default NeedsInfoPanel;
