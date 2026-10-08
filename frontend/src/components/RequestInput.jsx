import React, { useState } from 'react';
import { Send, Paperclip, Loader2, X, CheckCircle2, Database } from 'lucide-react';

const RequestInput = ({ onSubmit, isLoading }) => {
    const [request, setRequest] = useState('');
    const [file, setFile] = useState(null);
    const [error, setError] = useState(null);

    const handleSubmit = (e) => {
        e.preventDefault();
        setError(null);

        if (!request.trim()) {
            setError('Please enter what you want to automate.');
            return;
        }

        onSubmit(request, {}, file);
    };

    const handleFileChange = (e) => {
        if (e.target.files && e.target.files.length > 0) {
            setFile(e.target.files[0]);
        }
    };

    return (
        <div className="glass-panel p-6 border-t border-blue-500/30">
            {/* Workflow Configuration Banner */}
            <div className="mb-5 flex items-start gap-3 text-emerald-400 bg-emerald-400/10 px-4 py-3 rounded-xl border border-emerald-500/20 text-sm">
                <CheckCircle2 className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <div>
                    <span className="font-semibold">Workflow Configuration:</span>
                    <span className="ml-1 text-emerald-300">Loaded automatically</span>
                    <span className="mx-2 text-emerald-500/50">—</span>
                    <span className="font-mono text-xs bg-emerald-900/30 text-emerald-300 px-2 py-0.5 rounded border border-emerald-700/40">
                        AI_Agent_Workflow_Assessment.xlsx
                    </span>
                    <span className="ml-2 text-emerald-500/70">(10 workflows: WF001–WF010)</span>
                </div>
            </div>

            <h2 className="text-xl font-bold mb-4 text-white">What would you like to automate today?</h2>

            {error && (
                <div className="mb-4 text-red-400 text-sm font-medium bg-red-900/20 px-3 py-2 rounded border border-red-500/50">
                    {error}
                </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
                <div className="relative">
                    <textarea
                        value={request}
                        onChange={(e) => setRequest(e.target.value)}
                        placeholder="e.g. Which products need restocking? or Where is order ORD-1001? or Process this vendor spreadsheet."
                        className="w-full bg-slate-800/80 border border-slate-700 rounded-xl p-4 pr-12 text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all resize-none min-h-[100px]"
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                handleSubmit(e);
                            }
                        }}
                    />
                </div>

                {/* Runtime Input File Section */}
                <div className="rounded-xl border border-slate-700/60 bg-slate-800/30 px-4 py-3">
                    <div className="flex items-center gap-2 mb-2">
                        <Database className="w-3.5 h-3.5 text-slate-400" />
                        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Runtime Input File</span>
                        <span className="text-xs text-slate-600 italic">(optional — only required for workflows that process external data)</span>
                    </div>
                    <div className="flex items-center gap-3">
                        <label className="cursor-pointer group flex items-center gap-2 text-sm text-slate-400 hover:text-slate-200 transition-colors bg-slate-800/50 px-3 py-2 rounded-lg border border-slate-700 hover:border-slate-600">
                            <Paperclip className="w-4 h-4 group-hover:text-blue-400 transition-colors" />
                            <span>{file ? 'Change file' : 'Upload CSV / XLSX'}</span>
                            <input type="file" className="hidden" onChange={handleFileChange} accept=".csv,.xlsx,.xls" />
                        </label>

                        {file && (
                            <div className="flex items-center gap-2 text-sm bg-blue-900/30 text-blue-300 px-3 py-1.5 rounded-full border border-blue-800/50 animate-in zoom-in duration-300">
                                <CheckCircle2 className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" />
                                <span className="truncate max-w-[180px]">{file.name}</span>
                                <button type="button" onClick={() => setFile(null)} className="hover:bg-blue-800/50 rounded-full p-0.5 transition-colors ml-1">
                                    <X className="w-3 h-3" />
                                </button>
                            </div>
                        )}
                    </div>
                    {file && (
                        <p className="mt-1.5 text-xs text-slate-500">
                            Runtime file attached — will be passed to the selected workflow as input data.
                        </p>
                    )}
                </div>

                <div className="flex justify-end">
                    <button
                        type="submit"
                        disabled={isLoading}
                        className="bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-500 text-white px-6 py-2.5 rounded-lg flex items-center gap-2 font-medium transition-all shadow-lg shadow-blue-900/20 active:scale-95 disabled:active:scale-100"
                    >
                        {isLoading ? (
                            <>
                                <Loader2 className="w-4 h-4 animate-spin" />
                                Executing...
                            </>
                        ) : (
                            <>
                                <Send className="w-4 h-4" />
                                Run Workflow
                            </>
                        )}
                    </button>
                </div>
            </form>
        </div>
    );
};

export default RequestInput;
