import type { Status, Step } from '../types'
import { ToolResultViewer } from './ToolResultViewer'

const statusDot: Record<Status, string> = {
  analyzing: 'bg-[#6fa8ff]',
  pending: 'bg-[#fbbf24] pulse',
  success: 'bg-[#4ade80]',
  error: 'bg-[#f87171]',
  no_tool: 'bg-[#8b909c]',
}

export function ToolStep({ step }: { step: Step }) {
  return (
    <article className="border-l border-[#2a2e37] py-3 pl-4 last:pb-0">
      <div className="flex items-center gap-2 text-sm">
        <span className={`h-2 w-2 rounded-full ${statusDot[step.status]}`} />
        <span className="font-medium text-[#e4e6eb]">{step.title}</span>
        {step.latency && <span className="mono ml-auto text-xs text-[#8b909c]">{step.latency}</span>}
      </div>

      {step.tool && (
        <span className="mono mt-2 inline-block rounded border border-[#6fa8ff]/50 bg-[#6fa8ff]/10 px-2 py-1 text-xs text-[#6fa8ff]">
          {step.tool}
        </span>
      )}

      <p className="mt-2 text-sm leading-5 text-[#8b909c]">{step.reason}</p>

      {step.args && (
        <dl className="mono mt-3 space-y-1 border-l border-[#2a2e37] pl-3 text-xs text-[#b9bfca]">
          {Object.entries(step.args).map(([key, value]) => (
            <div key={key} className="flex gap-2">
              <dt className="text-[#8b909c]">{key}:</dt>
              <dd className="break-all">{JSON.stringify(value)}</dd>
            </div>
          ))}
        </dl>
      )}

      {step.error && (
        <p className="mt-3 rounded border border-[#f87171]/35 bg-[#f87171]/10 p-2 text-sm text-[#f87171]">
          {step.error}
        </p>
      )}

      {step.result !== undefined && <ToolResultViewer result={step.result} />}
    </article>
  )
}
