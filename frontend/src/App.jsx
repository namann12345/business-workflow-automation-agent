import { useState } from 'react'
import { runAgent } from './services/api'
import Header from './components/Header'
import RequestInput from './components/RequestInput'
import WorkflowCard from './components/WorkflowCard'
import ExecutionTimeline from './components/ExecutionTimeline'
import ResultPanel from './components/ResultPanel'
import NeedsInfoPanel from './components/NeedsInfoPanel'

function App() {
  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState(null)
  const [error, setError] = useState(null)

  const handleSubmit = async (requestText, context, file) => {
    setLoading(true)
    setError(null)
    setResponse(null)
    try {
      const data = await runAgent(requestText, context, file)
      setResponse(data)
    } catch (err) {
      if (err.response?.status === 422 && Array.isArray(err.response?.data?.detail)) {
        const messages = err.response.data.detail.map(d => d.msg).join(', ')
        setError(`Request validation failed: ${messages}`)
      } else if (err.response?.status === 400) {
        // User-facing validation errors (e.g. missing runtime file)
        setError(err.response?.data?.detail || err.message || 'Validation error.')
      } else {
        setError(err.response?.data?.detail || err.message || 'An error occurred during execution.')
      }
    } finally {
      setLoading(false)
    }
  }

  // Determine render mode based on response
  const executionStatus = response?.execution?.status
  const isNeedsInfo = executionStatus === 'needs_clarification'
  const isSuccess = executionStatus === 'success'
  const isEscalation = executionStatus === 'escalation'
  const needsRouterClarification = response?.routing?.needs_clarification && !response?.execution

  return (
    <div className="min-h-screen flex flex-col bg-slate-900 text-slate-100 font-sans">
      <Header />

      <main className="flex-1 container mx-auto px-4 py-8 max-w-5xl">
        <RequestInput onSubmit={handleSubmit} isLoading={loading} />

        {/* HTTP / unexpected errors */}
        {error && (
          <div className="mt-6 p-4 bg-red-900/50 border border-red-500 rounded-lg text-red-200">
            <h3 className="font-semibold flex items-center gap-2">
              <span className="text-xl">⚠️</span> Error
            </h3>
            <p className="mt-1 opacity-90 whitespace-pre-wrap">{error}</p>
          </div>
        )}

        {response && (
          <div className="mt-8 space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">

            {/* Router needs clarification (no workflow matched) */}
            {needsRouterClarification && (
              <div className="glass-panel p-6 border-amber-500/30">
                <h3 className="text-lg font-semibold text-amber-300 mb-2 flex items-center gap-2">
                  <span>🔍</span> No Matching Workflow
                </h3>
                <p className="text-slate-400 leading-relaxed">
                  {response.routing.clarification_message || response.message}
                </p>
              </div>
            )}

            {/* Normal layout: routing card + timeline + result */}
            {!needsRouterClarification && (
              <div className="grid md:grid-cols-2 gap-6">
                <div className="space-y-6">
                  <WorkflowCard routing={response.routing} />
                  {response.execution && (
                    <ExecutionTimeline execution={response.execution} />
                  )}
                </div>

                <div className="space-y-6">
                  {/* Needs Information panel (WF004, WF007 etc.) */}
                  {isNeedsInfo && response.execution?.final_result && (
                    <NeedsInfoPanel result={response.execution.final_result} />
                  )}

                  {/* Successful / escalation result */}
                  {(isSuccess || isEscalation) && response.execution?.final_result && (
                    <ResultPanel result={response.execution.final_result} />
                  )}

                  {/* Router clarification message when no execution yet */}
                  {response.message && !response.execution?.final_result && !needsRouterClarification && (
                    <div className="glass-panel p-6">
                      <h3 className="text-xl font-semibold mb-4 text-slate-200">System Response</h3>
                      <p className="text-slate-300 leading-relaxed">{response.message}</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}

export default App
