import type { Step } from '../types'
import { ToolStep } from './ToolStep'

export function AgentTracePanel({ steps, running }: { steps: Step[]; running: boolean }) {
  return (
    <aside className="border border-[#2a2e37] bg-[#171a20]" aria-label="Agent trace">
      <header className="flex justify-between border-b border-[#2a2e37] p-4">
        <div>
          <h2 className="text-sm font-medium">Agent trace</h2>
          <p className="mt-1 text-xs text-[#8b909c]">Current turn observability</p>
        </div>
        <span className={`mono border px-2 py-1 text-[10px] ${running ? 'border-[#fbbf24] text-[#fbbf24]' : 'border-[#2a2e37] text-[#8b909c]'}`}>
          {running ? 'LIVE' : 'IDLE'}
        </span>
      </header>
      <div className="min-h-80 p-5" aria-live="polite">
        {steps.length ? steps.map((step) => <ToolStep key={step.id} step={step} />) : (
          <p className="border-l border-[#2a2e37] pl-4 text-sm leading-6 text-[#8b909c]">
            Tool selection, arguments, execution state, errors, and raw results appear here.
          </p>
        )}
      </div>
    </aside>
  )
}
