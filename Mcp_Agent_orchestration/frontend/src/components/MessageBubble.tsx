import type { Message } from '../types'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

function normalizeMarkdown(text: string) {
  return text
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/\\([*_`\[\]()])/g, '$1')
}

export function MessageBubble({ message, streaming = false }: { message: Message; streaming?: boolean }) {
  const isUser = message.role === 'user'
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <article className={`max-w-[88%] border px-4 py-3 text-sm leading-6 ${isUser ? 'border-[#3d5273] bg-[#182333]' : 'border-[#2a2e37] bg-[#0f1115]'}`}>
        <p className="mono mb-1 text-[10px] uppercase text-[#8b909c]">{isUser ? 'You' : 'Agent'}</p>
        <div className="markdown-content">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              a: ({ children, href }) => (
                <a className="text-[#6fa8ff] underline underline-offset-2 hover:text-white" href={href} rel="noreferrer" target="_blank">
                  {children}
                </a>
              ),
              table: ({ children }) => <div className="my-3 overflow-x-auto"><table className="w-full border-collapse text-xs">{children}</table></div>,
              th: ({ children }) => <th className="border border-[#2a2e37] bg-[#171a20] px-2 py-1 text-left font-medium">{children}</th>,
              td: ({ children }) => <td className="border border-[#2a2e37] px-2 py-1 align-top">{children}</td>,
              ul: ({ children }) => <ul className="my-2 list-disc space-y-1 pl-5">{children}</ul>,
              ol: ({ children }) => <ol className="my-2 list-decimal space-y-1 pl-5">{children}</ol>,
              p: ({ children }) => <p className="my-2 first:mt-0 last:mb-0">{children}</p>,
            }}
          >
            {normalizeMarkdown(message.text)}
          </ReactMarkdown>
          {streaming && <span aria-label="Assistant is streaming" className="pulse ml-1 inline-block h-3 w-1.5 bg-[#6fa8ff] align-middle" />}
        </div>
        {!isUser && message.sources?.length ? (
          <div className="mt-3 border-t border-[#2a2e37] pt-2">
            <p className="mono text-[10px] text-[#8b909c]">TOOL-PROVIDED SOURCES</p>
            <ul className="mt-1 space-y-1">
              {message.sources.map((source) => (
                <li key={source.url}>
                  <a className="text-xs text-[#6fa8ff] underline underline-offset-2 hover:text-white" href={source.url} rel="noreferrer" target="_blank">
                    {source.title}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </article>
    </div>
  )
}
