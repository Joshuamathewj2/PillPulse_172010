import { LucideIcon } from 'lucide-react';
import { motion } from 'motion/react';
import { Button } from './ui/button';

interface ActionCardProps {
  icon: LucideIcon;
  title: string;
  description: string;
  buttonText: string;
  onClick?: () => void;
  variant?: 'default' | 'emergency';
}

export default function ActionCard({
  icon: Icon,
  title,
  description,
  buttonText,
  onClick,
  variant = 'default',
}: ActionCardProps) {
  const isEmergency = variant === 'emergency';

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={`p-6 rounded-2xl shadow-md border-2 ${
        isEmergency
          ? 'bg-red-50 border-red-200'
          : 'bg-white border-gray-100 hover:border-blue-200'
      } transition-all`}
    >
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-4 ${
        isEmergency
          ? 'bg-red-100'
          : 'bg-gradient-to-br from-blue-100 to-teal-50'
      }`}>
        <Icon className={`w-6 h-6 ${isEmergency ? 'text-red-600' : 'text-blue-600'}`} />
      </div>
      
      <h3 className="font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-sm text-gray-600 mb-4 leading-relaxed">{description}</p>
      
      <Button
        onClick={onClick}
        className={`w-full ${isEmergency ? 'bg-red-600 hover:bg-red-700' : ''}`}
        variant={isEmergency ? 'default' : 'default'}
      >
        {buttonText}
      </Button>
    </motion.div>
  );
}
