export type Status = 'analyzing' | 'pending' | 'success' | 'error' | 'no_tool'
export type Step = { id: string; title: string; status: Status; tool?: string; reason: string; args?: Record<string, unknown>; result?: unknown; error?: string; latency?: string }
export type Source = { title: string; url: string }
export type Message = { id: string; role: 'user' | 'assistant'; text: string; sources?: Source[] }
export type Example = { id: string; label: string; prompt: string }
