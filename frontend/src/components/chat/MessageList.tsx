import { ScrollArea } from '@/components/ui/scroll-area'
import { cn } from '@/lib/utils'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
}

interface MessageListProps {
  messages: Message[]
  className?: string
}

export function MessageList({ messages, className }: MessageListProps) {
  return (
    <ScrollArea className={cn('flex-1 px-4', className)}>
      <div className="py-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-muted-foreground py-12">
            <p className="text-lg font-medium">What do you want to create?</p>
            <p className="text-sm mt-1">Describe your page and I'll build it for you.</p>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                'animate-slide-up',
                message.role === 'user' ? 'flex justify-end' : ''
              )}
            >
              <div
                className={cn(
                  message.role === 'user'
                    ? 'bg-primary text-primary-foreground rounded-2xl rounded-br-md px-4 py-2.5 max-w-[85%]'
                    : 'text-foreground'
                )}
              >
                <p className="text-sm whitespace-pre-wrap">{message.content}</p>
              </div>
            </div>
          ))
        )}
      </div>
    </ScrollArea>
  )
}
