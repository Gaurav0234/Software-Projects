export function Sidebar({ onNew }: { onNew: () => void }) {
  return (
    <aside className="hidden w-56 flex-col border-r border-[#2a2e37] p-4 lg:flex">
      <p className="mono text-xs">MCP AGENT</p>
      <p className="mt-1 text-[11px] text-[#8b909c]">LangGraph / 5 tools</p>
      <button className="mt-6 border border-[#2a2e37] px-3 py-2 text-left text-xs hover:border-[#6fa8ff]" onClick={onNew} type="button">
        + New conversation
      </button>
      <p className="mono mt-6 text-[10px] text-[#646a75]">THREADS</p>
      <div className="mt-2 border-l-2 border-[#6fa8ff] bg-[#171a20] p-3 text-xs">
        Assignment demo
        <p className="mt-1 text-[10px] text-[#8b909c]">Active now</p>
      </div>
      <p className="mt-auto text-[11px] text-[#646a75]">Mock backend ready</p>
    </aside>
  )
}
