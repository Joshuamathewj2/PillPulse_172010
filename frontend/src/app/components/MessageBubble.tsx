import { Bot, User } from 'lucide-react';
import { motion } from 'motion/react';
import { Avatar, AvatarFallback } from './ui/avatar';

interface MessageBubbleProps {
  type: 'user' | 'ai';
  message: string;
  children?: React.ReactNode;
}

export default function MessageBubble({ type, message, children }: MessageBubbleProps) {
  const isAI = type === 'ai';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex gap-3 ${isAI ? '' : 'flex-row-reverse'} mb-4`}
    >
      {/* Avatar */}
      <Avatar className={`w-10 h-10 shrink-0 ${isAI ? 'border-2 border-blue-100' : 'border-2 border-blue-600/20'}`}>
        <AvatarFallback className={isAI ? 'bg-gradient-to-br from-blue-500 to-teal-500 text-white' : 'bg-blue-600 text-white'}>
          {isAI ? <Bot className="w-5 h-5" /> : <User className="w-5 h-5" />}
        </AvatarFallback>
      </Avatar>

      {/* Message Content */}
      <div className={`flex-1 max-w-2xl ${isAI ? '' : 'flex justify-end'}`}>
        <div
          className={`rounded-2xl px-4 py-3 ${
            isAI
              ? 'bg-blue-50 text-gray-800 rounded-tl-sm'
              : 'bg-blue-600 text-white rounded-tr-sm'
          }`}
        >
          <p className="leading-relaxed whitespace-pre-wrap">{message}</p>
          {children && <div className="mt-3">{children}</div>}
        </div>
      </div>
    </motion.div>
  );
}
