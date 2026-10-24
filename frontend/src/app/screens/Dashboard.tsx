import { useNavigate } from 'react-router';
import TopNavigation from '../components/TopNavigation';
import HealthCard from '../components/HealthCard';
import { Button } from '../components/ui/button';
import {
  Activity,
  AlertCircle,
  ArrowLeft,
  CheckCircle,
  Clock,
  Package,
  Pill,
  Plus,
  RefreshCw,
  Upload,
} from 'lucide-react';
import { motion } from 'motion/react';
import { useCallback, useEffect, useState } from 'react';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { apiJson, getPatientId, postJson, to12h } from '../../lib/api';

interface TodayDose {
  medicine_id: number;
  medicine_name: string;
  dosage?: string | null;
  instructions?: string | null;
  scheduled_time: string;
  taken: boolean;
  overdue: boolean;
}

interface Remaining {
  medicine_id: number;
  medicine_name: string;
  remaining_pills: number;
  remaining_days: number;
  refill_soon: boolean;
}

interface DayStat {
  date: string;
  day: string;
  expected: number;
  taken: number;
  missed: number;
  rate: number | null;
}

interface Score {
  score: number | null;
  taken: number;
  expected: number;
  has_data: boolean;
}

export default function Dashboard() {
  const navigate = useNavigate();
  const userId = getPatientId();

  const [doses, setDoses] = useState<TodayDose[]>([]);
  const [remaining, setRemaining] = useState<Remaining[]>([]);
  const [week, setWeek] = useState<DayStat[]>([]);
  const [score, setScore] = useState<Score | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const q = `user_id=${encodeURIComponent(userId)}`;
      const [d, r, w, s] = await Promise.all([
        apiJson<TodayDose[]>(`/medicines/today?${q}`),
        apiJson<Remaining[]>(`/medicines/remaining?${q}`),
        apiJson<DayStat[]>(`/adherence/weekly?${q}`),
        apiJson<Score>(`/adherence/score?${q}`),
      ]);
      setDoses(d);
      setRemaining(r);
      setWeek(w);
      setScore(s);
      setUpdatedAt(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load your data.');
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    load();
  }, [load]);

  const confirmDose = async (dose: TodayDose) => {
    try {
      await postJson('/medicines/confirm-dose', {
        user_id: userId,
        medicine_id: dose.medicine_id,
        scheduled_time: dose.scheduled_time,
      });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not record the dose.');
    }
  };

  const takenToday = doses.filter(d => d.taken).length;
  const overdue = doses.filter(d => d.overdue);
  const next = doses.find(d => !d.taken && !d.overdue);
  const refillSoon = remaining.filter(r => r.refill_soon);
  const hasMeds = remaining.length > 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-teal-50/20">
      <TopNavigation />

      <div className="max-w-7xl mx-auto px-4 py-8">
        <motion.div initial={{ y: -20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} className="mb-8">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 mb-2">Medication Dashboard</h1>
              <p className="text-lg text-gray-600">Patient code <span className="font-mono">{userId}</span></p>
            </div>
            <div className="flex items-center gap-3">
              {updatedAt && (
                <p className="text-sm text-gray-500">
                  Updated {updatedAt.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}
                </p>
              )}
              <Button variant="outline" size="sm" onClick={load} disabled={loading} className="gap-2">
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Refresh
              </Button>
            </div>
          </div>
        </motion.div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3 text-sm text-red-700">
            <AlertCircle className="w-5 h-5 shrink-0" /> {error}
          </div>
        )}

        {!loading && !hasMeds && !error && (
          <div className="mb-8 bg-white rounded-2xl p-10 shadow-lg border border-gray-100 text-center">
            <Pill className="w-12 h-12 text-blue-500 mx-auto mb-4" />
            <h2 className="text-2xl font-semibold text-gray-900 mb-2">No medicines yet</h2>
            <p className="text-gray-600 mb-6">Upload a prescription photo or add a medicine to start tracking.</p>
            <div className="flex justify-center gap-3">
              <Button onClick={() => navigate('/upload-prescription')} className="gap-2"><Upload className="w-4 h-4" /> Upload prescription</Button>
              <Button variant="outline" onClick={() => navigate('/add-medicine')} className="gap-2"><Plus className="w-4 h-4" /> Add manually</Button>
            </div>
          </div>
        )}

        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8"
        >
          <HealthCard
            icon={Activity}
            title="7-day adherence"
            value={score?.score == null ? '—' : `${Math.round(score.score)}%`}
            trend={score?.score == null ? undefined : score.score >= 80 ? 'up' : 'down'}
            color={score?.score == null ? 'blue' : score.score >= 80 ? 'green' : 'red'}
          />
          <HealthCard icon={CheckCircle} title="Doses taken today" value={`${takenToday} / ${doses.length}`} color="blue" />
          <HealthCard
            icon={Clock}
            title="Next dose"
            value={next ? `${to12h(next.scheduled_time)}` : doses.length ? 'Done for today' : '—'}
            color="purple"
          />
          <HealthCard
            icon={Package}
            title="Refills due"
            value={refillSoon.length ? `${refillSoon.length} medicine${refillSoon.length > 1 ? 's' : ''}` : 'None'}
            color={refillSoon.length ? 'red' : 'green'}
          />
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-6 mb-8">
          <motion.div
            initial={{ x: -20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100"
          >
            <h3 className="text-lg font-semibold text-gray-900">Last 7 days</h3>
            <p className="text-sm text-gray-500 mb-6">Doses taken vs missed, from your reminder and dashboard check-ins</p>
            {week.some(d => d.expected > 0) ? (
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={week}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="day" stroke="#9ca3af" style={{ fontSize: '12px' }} />
                  <YAxis allowDecimals={false} stroke="#9ca3af" style={{ fontSize: '12px' }} />
                  <Tooltip contentStyle={{ backgroundColor: 'white', border: '1px solid #e5e7eb', borderRadius: '8px' }} />
                  <Bar dataKey="taken" name="Taken" stackId="a" fill="#10B981" />
                  <Bar dataKey="missed" name="Missed" stackId="a" fill="#F87171" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-sm text-gray-500 py-16 text-center">Your history will appear here once doses are scheduled.</p>
            )}
          </motion.div>

          <motion.div
            initial={{ x: 20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100"
          >
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-900">Today's doses</h3>
              <Button variant="outline" size="sm" onClick={() => navigate('/add-medicine')}>
                <Plus className="w-4 h-4 mr-1" /> Add
              </Button>
            </div>
            <div className="space-y-3">
              {doses.length === 0 ? (
                <p className="text-gray-500 text-sm">No doses scheduled for today.</p>
              ) : (
                doses.map(dose => (
                  <div
                    key={`${dose.medicine_id}-${dose.scheduled_time}`}
                    className={`flex items-center gap-3 p-4 rounded-xl border ${
                      dose.taken ? 'bg-gray-50 border-gray-100' : dose.overdue ? 'bg-red-50 border-red-200' : 'bg-blue-50 border-blue-200'
                    }`}
                  >
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${dose.taken ? 'bg-gray-200' : dose.overdue ? 'bg-red-500' : 'bg-blue-600'}`}>
                      <Pill className={`w-5 h-5 ${dose.taken ? 'text-gray-600' : 'text-white'}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium text-gray-900 truncate">{dose.medicine_name}</h4>
                        {dose.taken && <CheckCircle className="w-4 h-4 text-green-600 shrink-0" />}
                      </div>
                      <p className="text-sm text-gray-600">
                        {to12h(dose.scheduled_time)}
                        {dose.dosage ? ` · ${dose.dosage}` : ''}
                        {dose.overdue ? ' · overdue' : ''}
                      </p>
                    </div>
                    {!dose.taken && (
                      <Button size="sm" onClick={() => confirmDose(dose)}>Taken</Button>
                    )}
                  </div>
                ))
              )}
            </div>
            {overdue.length > 0 && (
              <p className="mt-4 text-xs text-gray-500">
                Missed a dose? Take it when you remember unless the next one is close. Never double up. Ask your pharmacist if unsure.
              </p>
            )}
          </motion.div>
        </div>

        {hasMeds && (
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100 mb-8"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Stock & refills</h3>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
              {remaining.map(r => (
                <div key={r.medicine_id} className={`p-4 rounded-xl border ${r.refill_soon ? 'border-red-200 bg-red-50' : 'border-gray-100 bg-gray-50'}`}>
                  <p className="font-medium text-gray-900">{r.medicine_name}</p>
                  <p className="text-sm text-gray-600">
                    {r.remaining_pills} left · about {r.remaining_days} day{r.remaining_days === 1 ? '' : 's'}
                  </p>
                  {r.refill_soon && <p className="text-xs text-red-600 mt-1">Refill soon</p>}
                </div>
              ))}
            </div>
          </motion.div>
        )}

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
