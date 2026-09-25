import type { Example, Message } from '../types'
import { InputBar } from './InputBar'
import { MessageBubble } from './MessageBubble'

type Props = {
  messages: Message[]
  examples: Example[]
  running: boolean
  onSend: (prompt: string) => void
}

export function ChatPanel({ messages, examples, running, onSend }: Props) {
  return (
    <section className="flex min-h-[60vh] flex-col border border-[#2a2e37] bg-[#171a20]">
      <header className="flex justify-between border-b border-[#2a2e37] p-4">
        <div>
          <h1 className="text-sm font-medium">Agent conversation</h1>
          <p className="mt-1 text-xs text-[#8b909c]">Runtime tool selection enabled</p>
        </div>
        <span className="mono text-[10px] text-[#8b909c]">THREAD / DEMO-01</span>
      </header>
      <div className="flex-1 space-y-4 overflow-auto p-5" aria-live="polite">
        {messages.length ? messages.map((message, index) => (
          <MessageBubble
            key={message.id}
            message={message}
            streaming={running && message.role === 'assistant' && index === messages.length - 1}
          />
        )) : (
          <div className="mt-10 border-l-2 border-[#6fa8ff] pl-4">
            <p className="text-sm">Ask about files, weather, web info, or your documents.</p>
            <div className="mt-4 flex flex-wrap gap-2">
              {examples.map((example) => (
                <button className="border border-[#2a2e37] bg-[#0f1115] px-3 py-2 text-xs text-[#b7bcc6] hover:border-[#6fa8ff]" key={example.id} onClick={() => onSend(example.prompt)} type="button">
                  {example.label}
                </button>
              ))}
            </div>
          </div>
        )}
        {running && <p className="text-xs text-[#8b909c]"><i className="pulse mr-2 inline-block h-2 w-2 rounded-full bg-[#6fa8ff]" />Agent processing...</p>}
      </div>
      <InputBar disabled={running} onSend={onSend} />
    </section>
  )
}
