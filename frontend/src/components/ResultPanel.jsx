import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { ChevronDown, ChevronUp } from 'lucide-react';

// Renders a key-value pair row
const DataRow = ({ label, value }) => (
    <div className="flex items-start justify-between gap-4 py-2 border-b border-slate-800/60 last:border-0">
        <span className="text-sm text-slate-400 font-medium flex-shrink-0">{label}</span>
        <span className="text-sm text-slate-200 text-right">
            {value == null ? '—' : typeof value === 'object' ? JSON.stringify(value) : String(value)}
        </span>
    </div>
);

const formatFrequentErrors = (value) => {
    if (!value) return "—";
    if (typeof value === 'string') return value;

    if (Array.isArray(value)) {
        if (value.length === 0) return "—";
        return value.map((v, idx) => {
            if (typeof v === 'string') {
                return (
                    <div key={idx} className="mb-0.5 last:mb-0">
                        {v}
                    </div>
                );
            }
            if (typeof v === 'object' && v !== null && v.error) {
                return (
                    <div key={idx} className="mb-0.5 last:mb-0">
                        {v.error} ({v.count} occurrences)
                    </div>
                );
            }
            return null;
        });
    }

    if (typeof value === 'object' && value !== null && value.error) {
        return (
            <div>
                {value.error} ({value.count} occurrences)
            </div>
        );
    }

    // Object fallback (e.g. dictionary without error key)
    if (typeof value === 'object' && value !== null) {
        return Object.entries(value).map(([k, v], i) => (
            <div key={i} className="mb-0.5 last:mb-0">
                {k} ({v} occurrences)
            </div>
        ));
    }

    return String(value);
};

// Renders a list of record objects as a small table
const RecordTable = ({ records }) => {
    if (!records || records.length === 0) return <p className="text-sm text-slateald-500 italic">None</p>;
    const keys = Object.keys(records[0]);
    return (
        <div className="overflow-x-auto rounded-lg border border-slate-700/50">
            <table className="w-full text-xs">
                <thead>
                    <tr className="bg-slate-800/80">
                        {keys.map(k => (
                            <th key={k} className="px-3 py-2 text-left text-slate-400 font-semibold uppercase tracking-wider border-b border-slate-700">
                                {k}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {records.map((row, i) => (
                        <tr key={i} className={i % 2 === 0 ? 'bg-slate-900/40' : 'bg-slate-800/20'}>
                            {keys.map(k => (
                                <td key={k} className="px-3 py-2 text-slate-300 border-b border-slate-800/50">
                                    {row[k] == null
                                        ? '—'
                                        : k === 'frequent_errors'
                                            ? formatFrequentErrors(row[k])
                                            : typeof row[k] === 'object'
                                                ? JSON.stringify(row[k])
                                                : String(row[k])}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

const ResultPanel = ({ result }) => {
    const [showRaw, setShowRaw] = useState(false);
    if (!result) return null;

    // Extract the summary message
    const message = result.message;

    // Key numeric stats to render as prominent cards
    const statKeys = [
        { key: 'total_rows', label: 'Total Rows' },
        { key: 'valid_rows', label: 'Valid Rows' },
        { key: 'invalid_rows', label: 'Invalid Rows' },
        { key: 'restock_required', label: 'Restock Required' },
        { key: 'total_keywords', label: 'Total Keywords' },
        { key: 'total_pairs', label: 'Duplicate Pairs' },
        { key: 'exceptions', label: 'Price Exceptions' },
        { key: 'total_matched', label: 'Total Matched' },
        { key: 'total_executions', label: 'Total Executions' },
        { key: 'flagged_workflows', label: 'Flagged Workflows' },
        { key: 'threshold_pct', label: 'Threshold %' },
    ];

    // Key boolean / scalar non-list fields
    const scalarKeys = [
        { key: 'found', label: 'Found' },
        { key: 'assigned', label: 'Assigned' },
        { key: 'assigned_to', label: 'Assigned To' },
        { key: 'skill_score_pct', label: 'Skill Score %' },
        { key: 'capacity', label: 'Capacity Slots' },
        { key: 'order_id', label: 'Order ID' },
        { key: 'email', label: 'Email' },
    ];

    // Table data keys (arrays of objects)
    const tableKeys = [
        { key: 'products', label: 'Products' },
        { key: 'invalid_row_details', label: 'Invalid Rows' },
        { key: 'cleaned_data_preview', label: 'Cleaned Data Preview' },
        { key: 'classifications', label: 'Keyword Classifications' },
        { key: 'all_candidates', label: 'All Candidates' },
        { key: 'workflows', label: 'Workflow Performance' },
        { key: 'pairs', label: 'Duplicate Pairs' },
    ];

    const presentStats = statKeys.filter(s => result[s.key] != null);
    const presentScalars = scalarKeys.filter(s => result[s.key] != null);
    const presentTables = tableKeys.filter(t => Array.isArray(result[t.key]));

    // Order detail (WF005)
    const orderData = result.order;

    // Missing fields for clarification
    const missingFields = result.missing_fields;

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="glass-panel overflow-hidden border-indigo-500/20 bg-gradient-to-b from-indigo-900/10 to-slate-900/80"
        >
            <div className="px-6 py-4 border-b border-white/5 bg-white/5 flex items-center justify-between">
                <h3 className="text-lg font-semibold text-white">Final Output</h3>
                <div className="px-2.5 py-1 bg-indigo-500/20 text-indigo-300 text-xs font-semibold rounded-full border border-indigo-500/30">
                    Result Data
                </div>
            </div>

            <div className="p-6 space-y-5">
                {/* Message */}
                {message && (
                    <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-100 font-medium">
                        {message}
                    </div>
                )}

                {/* Missing fields clarification (WF007 etc.) */}
                {missingFields && missingFields.length > 0 && (
                    <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20">
                        <p className="text-amber-300 font-semibold mb-2">Missing Required Inputs</p>
                        <ul className="space-y-1">
                            {missingFields.map(f => (
                                <li key={f} className="text-sm text-amber-200 flex items-center gap-2">
                                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400 flex-shrink-0" />
                                    {f}
                                </li>
                            ))}
                        </ul>
                    </div>
                )}

                {/* Numeric Stats Cards */}
                {presentStats.length > 0 && (
                    <div className={`grid gap-3 ${presentStats.length === 1 ? 'grid-cols-1' : presentStats.length === 2 ? 'grid-cols-2' : 'grid-cols-3'}`}>
                        {presentStats.map(({ key, label }) => (
                            <div key={key} className="bg-slate-800/60 rounded-xl border border-slate-700/40 p-3 text-center">
                                <div className="text-2xl font-bold text-white">{result[key]}</div>
                                <div className="text-xs text-slate-400 mt-1">{label}</div>
                            </div>
                        ))}
                    </div>
                )}

                {/* Scalar Fields */}
                {presentScalars.length > 0 && (
                    <div className="bg-slate-900/40 rounded-xl border border-slate-800 px-4 py-2">
                        {presentScalars.map(({ key, label }) => (
                            <DataRow key={key} label={label} value={result[key]} />
                        ))}
                    </div>
                )}

                {/* Order detail (WF005) */}
                {orderData && typeof orderData === 'object' && !Array.isArray(orderData) && (
                    <div>
                        <p className="text-sm font-semibold text-slate-300 mb-2">Order Details</p>
                        <div className="bg-slate-900/40 rounded-xl border border-slate-800 px-4 py-2">
                            {Object.entries(orderData).map(([k, v]) => (
                                <DataRow key={k} label={k} value={v} />
                            ))}
                        </div>
                    </div>
                )}

                {/* Tables */}
                {presentTables.map(({ key, label }) => {
                    const rows = result[key];
                    if (!rows || rows.length === 0) return null;
                    return (
                        <div key={key}>
                            <p className="text-sm font-semibold text-slate-300 mb-2">
                                {label}
                                <span className="ml-2 text-xs font-normal text-slate-500">({rows.length} records)</span>
                            </p>
                            <RecordTable records={rows.slice(0, 20)} />
                            {rows.length > 20 && (
                                <p className="mt-1.5 text-xs text-slate-500 italic">Showing first 20 of {rows.length} records.</p>
                            )}
                        </div>
                    );
                })}

                {/* Column normalization report */}
                {result.column_normalization && Object.keys(result.column_normalization).length > 0 && (
                    <div>
                        <p className="text-sm font-semibold text-slate-300 mb-2">Column Normalization</p>
                        <div className="bg-slate-900/40 rounded-xl border border-slate-800 px-4 py-2">
                            {Object.entries(result.column_normalization).map(([old, nw]) => (
                                <DataRow key={old} label={old} value={`→ ${nw}`} />
                            ))}
                        </div>
                    </div>
                )}

                {/* LLM-generated text content (WF004, WF007 summary, WF009 summary) */}
                {result.title && (
                    <div>
                        <p className="text-sm font-semibold text-slate-300 mb-1">{result.title}</p>
                        {result.overview && <p className="text-sm text-slate-400">{result.overview}</p>}
                        {result.key_messages && (
                            <ul className="mt-2 space-y-1">
                                {(Array.isArray(result.key_messages) ? result.key_messages : [result.key_messages]).map((m, i) => (
                                    <li key={i} className="text-sm text-slate-300 flex items-start gap-2">
                                        <span className="text-blue-400 flex-shrink-0">•</span>{m}
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>
                )}

                {/* Product description (WF004 plain string) */}
                {typeof result.description === 'string' && (
                    <div className="bg-slate-800/40 rounded-xl border border-slate-700/40 p-4">
                        <p className="text-sm font-semibold text-slate-300 mb-2">Generated Description</p>
                        <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">{result.description}</p>
                    </div>
                )}

                {/* Raw JSON toggle */}
                <button
                    onClick={() => setShowRaw(v => !v)}
                    className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-400 transition-colors"
                >
                    {showRaw ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                    {showRaw ? 'Hide' : 'Show'} raw JSON
                </button>

                {showRaw && (
                    <div className="bg-slate-950/50 rounded-xl border border-slate-800 p-4 overflow-x-auto">
                        <pre className="text-xs font-mono text-emerald-300/90 whitespace-pre-wrap">
                            {JSON.stringify(result, null, 2)}
                        </pre>
                    </div>
                )}
            </div>
        </motion.div>
    );
};

export default ResultPanel;
