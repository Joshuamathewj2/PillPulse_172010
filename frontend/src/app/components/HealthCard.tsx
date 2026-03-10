import { LucideIcon } from 'lucide-react';

interface HealthCardProps {
  icon: LucideIcon;
  title: string;
  value: string;
  trend?: 'up' | 'down' | 'stable';
  color?: string;
}

export default function HealthCard({
  icon: Icon,
  title,
  value,
  trend,
  color = 'blue',
}: HealthCardProps) {
  const colorClasses = {
    blue: 'from-blue-100 to-teal-50 text-blue-600',
    green: 'from-green-100 to-emerald-50 text-green-600',
    red: 'from-red-100 to-rose-50 text-red-600',
    purple: 'from-purple-100 to-indigo-50 text-purple-600',
  }[color];

  return (
    <div className="bg-white rounded-2xl p-6 shadow-md border border-gray-100 hover:shadow-lg transition-all">
      <div className="flex items-start justify-between mb-4">
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center bg-gradient-to-br ${colorClasses}`}>
          <Icon className="w-6 h-6" />
        </div>
        {trend && (
          <span className={`text-xs font-medium px-2 py-1 rounded-full ${
            trend === 'up' ? 'bg-green-100 text-green-700' :
            trend === 'down' ? 'bg-red-100 text-red-700' :
            'bg-gray-100 text-gray-700'
          }`}>
            {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'}
          </span>
        )}
      </div>
      <h3 className="text-sm text-gray-600 mb-1">{title}</h3>
      <p className="text-2xl font-semibold text-gray-900">{value}</p>
    </div>
  );
}
