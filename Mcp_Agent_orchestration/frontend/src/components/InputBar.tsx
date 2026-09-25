import { useState } from 'react'
import type { FormEvent } from 'react'

export function InputBar({ disabled, onSend }: { disabled: boolean; onSend: (value: string) => void }) {
  const [value, setValue] = useState('')

  function submit(event: FormEvent) {
    event.preventDefault()
    if (!value.trim()) return
    onSend(value)
    setValue('')
  }

  return (
    <form onSubmit={submit} className="border-t border-[#2a2e37] p-4">
      <div className="flex gap-2 border border-[#2a2e37] bg-[#0f1115] p-2 focus-within:border-[#6fa8ff]">
        <textarea
          aria-label="Message agent"
          className="min-h-12 flex-1 resize-none bg-transparent px-2 text-sm outline-none"
          disabled={disabled}
          placeholder="Message the agent..."
          value={value}
          onChange={(event) => setValue(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault()
              event.currentTarget.form?.requestSubmit()
            }
          }}
        />
        <button
          className="mono bg-[#6fa8ff] px-3 text-xs text-[#0f1115] disabled:bg-[#2a2e37]"
          disabled={disabled || !value.trim()}
          type="submit"
        >
          Send
        </button>
      </div>
      <p className="mt-2 text-[11px] text-[#646a75]">Enter to send / Shift + Enter for new line</p>
    </form>
  )
}
