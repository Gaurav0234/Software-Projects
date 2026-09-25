import { useState } from 'react'

type RagRow = { source: string; score: number; content: string }

export function ToolResultViewer({ result }: { result: unknown }) {
  const [open, setOpen] = useState(false)
  const rows = (result as { results?: RagRow[] })?.results

  return (
    <div className="mt-3 border-t border-[#2a2e37] pt-3">
      {rows?.[0]?.source && (
        <div className="mb-3 border border-[#2a2e37] p-2 text-xs">
          <p className="mono mb-1 text-[10px] text-[#8b909c]">RETRIEVED CHUNKS</p>
          {rows.map((row) => (
            <div className="grid grid-cols-[1fr_auto] gap-2 border-b border-[#2a2e37] py-2 last:border-0" key={row.source}>
              <div>
                <p className="mono text-[#b7d2ff]">{row.source}</p>
                <p className="mt-1 text-[#b7bcc6]">{row.content}</p>
              </div>
              <span className="mono text-[#4ade80]">{row.score.toFixed(2)}</span>
            </div>
          ))}
        </div>
      )}
      <button
        aria-expanded={open}
        className="mono text-[11px] text-[#8b909c] hover:text-white"
        onClick={() => setOpen(!open)}
        type="button"
      >
        {open ? '- Hide raw output' : '+ View raw output'}
      </button>
      {open && (
        <pre className="mono mt-2 max-h-48 overflow-auto border border-[#2a2e37] bg-[#0f1115] p-2 text-[10px] text-[#b7bcc6]">
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  )
}
