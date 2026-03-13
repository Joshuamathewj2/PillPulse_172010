import { useState } from 'react';
import { useNavigate } from 'react-router';
import TopNavigation from '../components/TopNavigation';
import { Button } from '../components/ui/button';
import { ArrowLeft, Plus } from 'lucide-react';
import { motion } from 'motion/react';

const API_URL = (import.meta as any).env.VITE_API_URL || 'https://pillpulse-backend.onrender.com';

export default function AddMedicine() {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        medicine_name: '',
        dosage_per_day: 1,
        schedule_times: '',
        total_pills: 30,
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const res = await fetch(`${API_URL}/medicines/add`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: 1, // hardcoded user for MVP
                    ...formData,
                }),
            });
            if (res.ok) {
                navigate('/dashboard');
            } else {
                alert('Failed to add medicine');
            }
        } catch (err) {
            console.error(err);
            alert('Error adding medicine');
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-teal-50/20">
            <TopNavigation />

            <div className="max-w-2xl mx-auto px-4 py-8">
                <motion.div
                    initial={{ y: -20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    className="mb-8"
                >
                    <div className="flex items-center gap-4">
                        <Button variant="outline" size="icon" onClick={() => navigate(-1)}>
                            <ArrowLeft className="w-4 h-4" />
                        </Button>
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900">Add Medicine</h1>
                            <p className="text-gray-600">Enter medication details and schedule.</p>
                        </div>
                    </div>
                </motion.div>

                <motion.div
                    initial={{ y: 20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ delay: 0.1 }}
                    className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100"
                >
                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Medicine Name
                            </label>
                            <input
                                type="text"
                                required
                                className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                value={formData.medicine_name}
                                onChange={(e) => setFormData({ ...formData, medicine_name: e.target.value })}
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Dosage Per Day
                            </label>
                            <input
                                type="number"
                                min="1"
                                required
                                className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                value={formData.dosage_per_day}
                                onChange={(e) => setFormData({ ...formData, dosage_per_day: parseInt(e.target.value) })}
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Schedule Times (comma separated, e.g., 09:00, 21:00)
                            </label>
                            <input
                                type="text"
                                required
                                placeholder="09:00, 21:00"
                                className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                value={formData.schedule_times}
                                onChange={(e) => setFormData({ ...formData, schedule_times: e.target.value })}
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Total Pills
                            </label>
                            <input
                                type="number"
                                min="1"
                                required
                                className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                value={formData.total_pills}
                                onChange={(e) => setFormData({ ...formData, total_pills: parseInt(e.target.value) })}
                            />
                        </div>

                        <Button type="submit" className="w-full bg-blue-600 hover:bg-blue-700 gap-2">
                            <Plus className="w-4 h-4" />
                            Save Medicine
                        </Button>
                    </form>
                </motion.div>
            </div>
        </div>
    );
}
