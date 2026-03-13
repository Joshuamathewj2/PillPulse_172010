import { useNavigate } from 'react-router';
import TopNavigation from '../components/TopNavigation';
import HealthCard from '../components/HealthCard';
import { Button } from '../components/ui/button';
import {
  Heart,
  Activity,
  Moon,
  Thermometer,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Pill,
  Calendar,
  ArrowLeft,
  Plus,
} from 'lucide-react';
import { motion } from 'motion/react';
import { useState, useEffect } from 'react';

const API_URL = (import.meta as any).env.VITE_API_URL || 'https://pillpulse-backend.onrender.com';

import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

// Mock data for charts
const heartRateData = [
  { time: '00:00', value: 62 },
  { time: '04:00', value: 58 },
  { time: '08:00', value: 72 },
  { time: '12:00', value: 78 },
  { time: '16:00', value: 75 },
  { time: '20:00', value: 68 },
  { time: '23:59', value: 65 },
];

const sleepData = [
  { day: 'Mon', hours: 7.2 },
  { day: 'Tue', hours: 6.5 },
  { day: 'Wed', hours: 8.1 },
  { day: 'Thu', hours: 7.8 },
  { day: 'Fri', hours: 6.9 },
  { day: 'Sat', hours: 8.5 },
  { day: 'Sun', hours: 7.6 },
];

const activityData = [
  { day: 'Mon', steps: 8234 },
  { day: 'Tue', steps: 6891 },
  { day: 'Wed', steps: 10234 },
  { day: 'Thu', steps: 7456 },
  { day: 'Fri', steps: 9123 },
  { day: 'Sat', steps: 12456 },
  { day: 'Sun', steps: 5678 },
];

export default function Dashboard() {
  const navigate = useNavigate();

  const [meds, setMeds] = useState<any[]>([]);
  const [adherenceScore, setAdherenceScore] = useState<number>(100);
  const [remainingPillsData, setRemainingPills] = useState<any[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [medsRes, scoreRes, remainingRes] = await Promise.all([
          fetch(`${API_URL}/medicines/today?user_id=1`),
          fetch(`${API_URL}/adherence/score?user_id=1`),
          fetch(`${API_URL}/medicines/remaining?user_id=1`)
        ]);
        if (medsRes.ok) {
          const m = await medsRes.json();
          setMeds(m);
        }
        if (scoreRes.ok) {
          const s = await scoreRes.json();
          setAdherenceScore(s.score);
        }
        if (remainingRes.ok) {
          const r = await remainingRes.json();
          setRemainingPills(r);
        }
      } catch (err) {
        console.error(err);
      }
    };
    fetchData();
  }, []);

  const handleConfirmDose = async (medicine_id: number, scheduled_time: string) => {
    try {
      const res = await fetch(`${API_URL}/medicines/confirm-dose`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 1,
          medicine_id,
          scheduled_time
        })
      });
      if (res.ok) {
        // optimistically update UI
        setMeds(meds.map(m =>
          (m.medicine_id === medicine_id && m.scheduled_time === scheduled_time)
            ? { ...m, taken: true } : m
        ));
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-teal-50/20">
      <TopNavigation />

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <motion.div
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="mb-8"
        >
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 mb-2">Health Dashboard</h1>
              <p className="text-lg text-gray-600">Your personalized health insights</p>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-500">Last updated</p>
              <p className="text-sm font-medium text-gray-900">Today, 2:34 PM</p>
            </div>
          </div>
        </motion.div>

        {/* Health Summary Cards */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8"
        >
          <HealthCard
            icon={Pill}
            title="Adherence Score"
            value={`${Math.round(adherenceScore)}%`}
            trend={adherenceScore >= 80 ? "up" : "down"}
            color={adherenceScore >= 80 ? "green" : "red"}
          />
          <HealthCard
            icon={Activity}
            title="Total Meds"
            value={remainingPillsData.length.toString()}
            trend="stable"
            color="blue"
          />
          <HealthCard
            icon={Moon}
            title="Avg Remaining Days"
            value={remainingPillsData.length ? Math.round(remainingPillsData.reduce((acc, curr) => acc + curr.remaining_days, 0) / remainingPillsData.length).toString() : "0"}
            trend="up"
            color="purple"
          />
          <HealthCard
            icon={Thermometer}
            title="Temperature"
            value="98.6°F"
            trend="stable"
            color="blue"
          />
        </motion.div>

        {/* Charts Section */}
        <div className="grid lg:grid-cols-2 gap-6 mb-8">
          {/* Heart Rate Trend */}
          <motion.div
            initial={{ x: -20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100"
          >
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Heart Rate Trend</h3>
                <p className="text-sm text-gray-500">Last 24 hours</p>
              </div>
              <div className="w-10 h-10 rounded-xl bg-red-100 flex items-center justify-center">
                <Heart className="w-5 h-5 text-red-600" />
              </div>
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={heartRateData}>
                <defs>
                  <linearGradient id="heartGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#EF4444" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#EF4444" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="time" stroke="#9ca3af" style={{ fontSize: '12px' }} />
                <YAxis stroke="#9ca3af" style={{ fontSize: '12px' }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke="#EF4444"
                  strokeWidth={2}
                  fill="url(#heartGradient)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </motion.div>

          {/* Sleep Pattern */}
          <motion.div
            initial={{ x: 20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100"
          >
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Sleep Pattern</h3>
                <p className="text-sm text-gray-500">Last 7 days</p>
              </div>
              <div className="w-10 h-10 rounded-xl bg-purple-100 flex items-center justify-center">
                <Moon className="w-5 h-5 text-purple-600" />
              </div>
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={sleepData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="day" stroke="#9ca3af" style={{ fontSize: '12px' }} />
                <YAxis stroke="#9ca3af" style={{ fontSize: '12px' }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                  }}
                />
                <Bar dataKey="hours" fill="#A855F7" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </motion.div>

          {/* Activity Level */}
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100"
          >
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Activity Level</h3>
                <p className="text-sm text-gray-500">Daily steps</p>
              </div>
              <div className="w-10 h-10 rounded-xl bg-green-100 flex items-center justify-center">
                <Activity className="w-5 h-5 text-green-600" />
              </div>
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={activityData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="day" stroke="#9ca3af" style={{ fontSize: '12px' }} />
                <YAxis stroke="#9ca3af" style={{ fontSize: '12px' }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="steps"
                  stroke="#10B981"
                  strokeWidth={3}
                  dot={{ fill: '#10B981', r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </motion.div>

          {/* AI Risk Assessment */}
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl p-6 shadow-lg border-2 border-green-200"
          >
            <div className="flex items-start gap-4 mb-6">
              <div className="w-12 h-12 rounded-xl bg-green-100 flex items-center justify-center shrink-0">
                <CheckCircle className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">AI Health Assessment</h3>
                <p className="text-sm text-gray-600 mt-1">Overall health status</p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Cardiovascular</span>
                  <span className="text-sm font-semibold text-green-600">Good</span>
                </div>
                <div className="h-2 bg-green-100 rounded-full overflow-hidden">
                  <div className="h-full bg-green-500 rounded-full" style={{ width: '85%' }}></div>
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Sleep Quality</span>
                  <span className="text-sm font-semibold text-blue-600">Improving</span>
                </div>
                <div className="h-2 bg-blue-100 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-500 rounded-full" style={{ width: '72%' }}></div>
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Activity Level</span>
                  <span className="text-sm font-semibold text-green-600">Excellent</span>
                </div>
                <div className="h-2 bg-green-100 rounded-full overflow-hidden">
                  <div className="h-full bg-green-500 rounded-full" style={{ width: '92%' }}></div>
                </div>
              </div>
            </div>

            <Button className="w-full mt-6 bg-green-600 hover:bg-green-700">
              <TrendingUp className="w-4 h-4 mr-2" />
              View Detailed Analysis
            </Button>
          </motion.div>
        </div>

        {/* Recent Symptoms & Medication */}
        <div className="grid lg:grid-cols-2 gap-6 mb-8">
          {/* Recent Symptoms */}
          <motion.div
            initial={{ x: -20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100"
          >
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-900">Recent Symptoms</h3>
              <Button variant="outline" size="sm" onClick={() => navigate('/symptom-checker')}>
                Add New
              </Button>
            </div>

            <div className="space-y-3">
              <div className="flex items-start gap-3 p-4 bg-yellow-50 rounded-xl border border-yellow-100">
                <div className="w-10 h-10 rounded-lg bg-yellow-100 flex items-center justify-center shrink-0">
                  <AlertCircle className="w-5 h-5 text-yellow-600" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <h4 className="font-medium text-gray-900">Headache</h4>
                    <span className="text-xs text-gray-500">2 days ago</span>
                  </div>
                  <p className="text-sm text-gray-600">Severity: Moderate</p>
                  <p className="text-xs text-gray-500 mt-1">Duration: 3 hours</p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-4 bg-blue-50 rounded-xl border border-blue-100">
                <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center shrink-0">
                  <AlertCircle className="w-5 h-5 text-blue-600" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <h4 className="font-medium text-gray-900">Fatigue</h4>
                    <span className="text-xs text-gray-500">5 days ago</span>
                  </div>
                  <p className="text-sm text-gray-600">Severity: Mild</p>
                  <p className="text-xs text-gray-500 mt-1">Duration: All day</p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-4 bg-gray-50 rounded-xl border border-gray-100">
                <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center shrink-0">
                  <CheckCircle className="w-5 h-5 text-gray-400" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <h4 className="font-medium text-gray-900">Sore Throat</h4>
                    <span className="text-xs text-gray-500">1 week ago</span>
                  </div>
                  <p className="text-sm text-gray-600">Resolved</p>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Medication Reminders */}
          <motion.div
            initial={{ x: 20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100"
          >
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-900">Medication Reminders</h3>
              <Button variant="outline" size="sm" onClick={() => navigate('/add-medicine')}>
                <Plus className="w-4 h-4 mr-1" /> Add
              </Button>
            </div>

            <div className="space-y-3">
              {meds.length === 0 ? (
                <p className="text-gray-500 text-sm">No medications scheduled for today.</p>
              ) : (
                meds.map((med, idx) => (
                  <div key={idx} className={`flex items-center gap-3 p-4 rounded-xl border ${med.taken ? 'bg-gray-50 border-gray-100' : 'bg-blue-50 border-blue-200'}`}>
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${med.taken ? 'bg-gray-200' : 'bg-blue-600'}`}>
                      <Pill className={`w-5 h-5 ${med.taken ? 'text-gray-600' : 'text-white'}`} />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium text-gray-900">{med.medicine_name}</h4>
                        {med.taken && <CheckCircle className="w-4 h-4 text-green-600" />}
                      </div>
                      <p className="text-sm text-gray-600">Time: {med.scheduled_time}</p>
                    </div>
                    {!med.taken && (
                      <Button size="sm" onClick={() => handleConfirmDose(med.medicine_id, med.scheduled_time)}>
                        I took this medicine
                      </Button>
                    )}
                  </div>
                ))
              )}
            </div>

            <Button variant="outline" className="w-full mt-4">
              <Calendar className="w-4 h-4 mr-2" />
              View Full Schedule
            </Button>
          </motion.div>
        </div>

        {/* Health Tips */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="bg-gradient-to-br from-teal-50 to-blue-50 rounded-2xl p-8 border-2 border-teal-100"
        >
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Personalized Health Tips</h3>
          <div className="grid md:grid-cols-3 gap-4">
            <div className="bg-white rounded-xl p-4">
              <h4 className="font-medium text-gray-900 mb-2">💧 Hydration</h4>
              <p className="text-sm text-gray-600">
                You've met 6 out of 8 glasses today. Keep up the good work!
              </p>
            </div>
            <div className="bg-white rounded-xl p-4">
              <h4 className="font-medium text-gray-900 mb-2">🏃 Activity</h4>
              <p className="text-sm text-gray-600">
                Great job! You've exceeded your daily step goal for 3 days in a row.
              </p>
            </div>
            <div className="bg-white rounded-xl p-4">
              <h4 className="font-medium text-gray-900 mb-2">😴 Sleep</h4>
              <p className="text-sm text-gray-600">
                Consider going to bed 30 minutes earlier for optimal rest.
              </p>
            </div>
          </div>
        </motion.div>

        {/* Back Button */}
        <div className="mt-8">
          <Button onClick={() => navigate('/')} variant="outline" className="gap-2">
            <ArrowLeft className="w-4 h-4" />
            Back to Chat
          </Button>
        </div>
      </div>
    </div>
  );
}
