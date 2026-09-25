import { useState } from 'react'
import { AgentTracePanel } from './components/AgentTracePanel'
import { ChatPanel } from './components/ChatPanel'
import { Sidebar } from './components/Sidebar'
import type { Example, Message, Source, Step } from './types'

const examples: Example[] = [
  { id: 'filesystem', label: 'List documents', prompt: 'List files in ./data/documents' },
  { id: 'weather', label: 'Check weather', prompt: 'What is the weather in Bangalore?' },
  { id: 'search', label: 'Search the web', prompt: 'Search the web for LangGraph MCP integration' },
  { id: 'rag', label: 'Ask your documents', prompt: 'What is the annual leave policy?' },
  { id: 'scraper', label: 'Read a webpage', prompt: 'Read https://example.com and tell me the title' },
]

type ServerEvent = { event: string; data: Record<string, unknown> }
const MIN_TOKEN_PAINT_MS = 28

function parseSseFrame(frame: string): ServerEvent | undefined {
  const event = frame.match(/^event: (.+)$/m)?.[1]
  const json = frame.match(/^data: (.+)$/m)?.[1]
  if (!event || !json) return undefined
  try {
    return { event, data: JSON.parse(json) as Record<string, unknown> }
  } catch {
    return undefined
  }
}

function sourcesFrom(data: Record<string, unknown>): Source[] {
  const candidates = data.sources
  if (!Array.isArray(candidates)) return []
  return candidates.filter((item): item is Source => (
    typeof item === 'object' && item !== null
    && typeof (item as Source).title === 'string'
    && /^https?:\/\//.test((item as Source).url)
  ))
}

export default function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [steps, setSteps] = useState<Step[]>([])
  const [running, setRunning] = useState(false)

  function mergeStep(incoming: Step) {
    setSteps((current) => {
      const existing = current.find((step) => step.id === incoming.id)
      if (!existing) return [...current, incoming]
      return current.map((step) => step.id === incoming.id ? { ...step, ...incoming } : step)
    })
  }

  async function send(prompt: string) {
    if (running) return
    setRunning(true)
    setSteps([])
    setMessages((current) => [...current, { id: crypto.randomUUID(), role: 'user', text: prompt }])

    try {
      let streamingMessageId: string | undefined
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: prompt }),
      })
      if (!response.ok || !response.body) throw new Error(`API request failed (${response.status}).`)

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { value, done } = await reader.read()
        buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done })
        const frames = buffer.split('\n\n')
        buffer = frames.pop() ?? ''

        for (const frame of frames) {
          const event = parseSseFrame(frame)
          if (!event) continue
          if (event.event === 'trace') mergeStep(event.data as unknown as Step)
          if (event.event === 'assistant_delta') {
            const token = String(event.data.text ?? '')
            if (!token) continue
            // Brief pacing gives the browser a chance to paint each real SSE token.
            await new Promise((resolve) => window.setTimeout(resolve, MIN_TOKEN_PAINT_MS))
            if (!streamingMessageId) {
              streamingMessageId = crypto.randomUUID()
              const messageId = streamingMessageId
              setMessages((current) => [...current, { id: messageId, role: 'assistant', text: token }])
            } else {
              const messageId = streamingMessageId
              setMessages((current) => current.map((message) => (
                message.id === messageId ? { ...message, text: message.text + token } : message
              )))
            }
          }
          if (event.event === 'assistant') {
            setMessages((current) => [...current, {
              id: crypto.randomUUID(), role: 'assistant', text: String(event.data.text ?? ''), sources: sourcesFrom(event.data),
            }])
          }
          if (event.event === 'assistant_done' && streamingMessageId) {
            const messageId = streamingMessageId
            const sources = sourcesFrom(event.data)
            setMessages((current) => current.map((message) => (
              message.id === messageId ? { ...message, sources } : message
            )))
          }
        }
        if (done) break
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown connection error.'
      mergeStep({
        id: 'connection-error', title: 'Backend connection failed', status: 'error',
        reason: 'The React frontend could not reach the FastAPI server.', error: message,
      })
      setMessages((current) => [...current, {
        id: crypto.randomUUID(), role: 'assistant', text: `Could not contact the backend: ${message}`,
      }])
    } finally {
      setRunning(false)
    }
  }

  return (
    <main className="min-h-screen bg-[#0f1115] lg:flex">
      <Sidebar onNew={() => { setMessages([]); setSteps([]) }} />
      <div className="w-full">
        <header className="flex justify-between border-b border-[#2a2e37] px-5 py-4">
          <div>
            <p className="text-sm font-medium">Multi-tool agent console</p>
            <p className="mono mt-1 text-[10px] text-[#8b909c]">LIVE API / SSE TRACE</p>
          </div>
          <p className="mono text-[10px] text-[#8b909c]">LANGGRAPH / MCP / RAG</p>
        </header>
        <div className="mx-auto grid max-w-[1500px] gap-4 p-4 lg:grid-cols-[1.15fr_.85fr] lg:p-6">
          <ChatPanel examples={examples} messages={messages} onSend={send} running={running} />
          <AgentTracePanel steps={steps} running={running} />
        </div>
      </div>
    </main>
  )
}
