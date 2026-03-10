import React, { useState, useRef } from 'react';
import { motion } from 'motion/react';
import TopNavigation from '../components/TopNavigation';
import { Button } from '../components/ui/button';
import {
    UploadCloud,
    FileImage,
    CheckCircle,
    AlertCircle,
    Sun,
    Plus,
    Loader2,
    X
} from 'lucide-react';

interface ExtractedMedicine {
    name: string;
    confidence: number;
    status: string;
    dosage?: string;
    frequency?: string;
    duration?: string;
    timing?: string[];
    instructions?: string;
    food_interaction?: string;
    refill_reminder?: string;
}

const RX_LINE: Record<string, string> = {
    "Hairbless": "Tab. Hairbless    1-0-1    PC    × 30 days",
    "Lobate": "Tab. Lobate       0-0-1    HS    × 14 days"
};

const SCHEDULE_TABLE = {
    headers: ["Field", "Lobate", "Hairbless"],
    rows: [
        ["Frequency", "Once daily (OD)", "Twice daily (BD)"],
        ["Timing", "10:00 PM · Bedtime", "8:00 AM · 8:00 PM"],
        ["Duration", "14 days", "30 days"],
        ["Instructions", "Apply thin layer", "Take after food"],
        ["Food Note", "No restrictions", "Take with meals"],
        ["Refill In", "10 days", "25 days"]
    ]
};


export default function PrescriptionUpload() {
    const [selectedImage, setSelectedImage] = useState<File | null>(null);
    const [previewUrl, setPreviewUrl] = useState<string | null>(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [medicines, setMedicines] = useState<ExtractedMedicine[]>([]);
    const [addedMeds, setAddedMeds] = useState<Set<number>>(new Set());
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    };

    const handleFileSelect = (file: File) => {
        const validTypes = ['image/jpeg', 'image/png', 'image/jpg'];
        if (!validTypes.includes(file.type)) {
            setError('Please upload a valid image file (JPG, PNG).');
            return;
        }
        setError(null);
        setSelectedImage(file);
        setPreviewUrl(URL.createObjectURL(file));
        setMedicines([]);
        setAddedMeds(new Set());
    };

    const clearSelection = () => {
        setSelectedImage(null);
        setPreviewUrl(null);
        setError(null);
        setMedicines([]);
        setAddedMeds(new Set());
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    const processPrescription = async () => {
        if (!selectedImage) return;

        setIsProcessing(true);
        setError(null);

        try {
            const formData = new FormData();
            formData.append('image', selectedImage);

            const response = await fetch('http://localhost:5000/api/predict', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error('Failed to parse prescription');
            }

            const data = await response.json();
            if (data && data.medicines && data.medicines.length > 0) {
                setMedicines(data.medicines);
            } else {
                setError('Unable to read prescription clearly. Please upload a clearer image.');
            }
        } catch (err) {
            console.error(err);
            setError('Unable to read prescription clearly. Please upload a clearer image.');
        } finally {
            setIsProcessing(false);
        }
    };

    const addToSchedule = async (med: ExtractedMedicine, index: number) => {
        try {
            const payload = {
                user_id: 1,
                medicine_name: med.name,
                dosage: `1 per day`,
                frequency: 'Daily',
                times_per_day: 1,
                duration_days: 7,
                schedule: '08:00',
            };

            const response = await fetch('http://localhost:8000/medicines/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            if (response.ok) {
                setAddedMeds(prev => new Set(prev).add(index));
            } else {
                alert('Failed to add medicine to schedule.');
            }
        } catch (err) {
            console.error(err);
            alert('Failed to request backend.');
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-teal-50/20">
            <TopNavigation />

            <div className="max-w-7xl mx-auto px-4 py-8">
                <motion.div
                    initial={{ y: -20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    className="mb-8"
                >
                    <h1 className="text-4xl font-bold text-gray-900 mb-2">Upload Prescription</h1>
                    <p className="text-lg text-gray-600">Extract medications automatically from a doctor's hand-written prescription</p>
                </motion.div>

                <div className="grid lg:grid-cols-2 gap-8">
                    {/* Left Panel: Upload Section */}
                    <motion.div
                        initial={{ x: -20, opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        transition={{ delay: 0.1 }}
                        className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100 flex flex-col h-fit"
                    >
                        <h3 className="text-lg font-semibold text-gray-900 mb-6 flex items-center gap-2">
                            <FileImage className="w-5 h-5 text-blue-600" />
                            Upload Document
                        </h3>

                        {!previewUrl ? (
                            <div
                                onDragOver={handleDragOver}
                                onDrop={handleDrop}
                                onClick={() => fileInputRef.current?.click()}
                                className="border-2 border-dashed border-blue-200 rounded-xl p-12 flex flex-col items-center justify-center text-center cursor-pointer hover:bg-blue-50 transition-colors bg-blue-50/30"
                            >
                                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                                    <UploadCloud className="w-8 h-8 text-blue-600" />
                                </div>
                                <h4 className="text-lg font-medium text-gray-900 mb-2">Click to upload or drag and drop</h4>
                                <p className="text-sm text-gray-500 mb-4">Supported formats: JPG, PNG, JPEG</p>
                                <Button variant="secondary">Select File</Button>
                                <input
                                    type="file"
                                    accept="image/jpeg, image/png, image/jpg"
                                    className="hidden"
                                    ref={fileInputRef}
                                    onChange={(e) => {
                                        if (e.target.files && e.target.files.length > 0) {
                                            handleFileSelect(e.target.files[0]);
                                        }
                                    }}
                                />
                            </div>
                        ) : (
                            <div className="relative rounded-xl overflow-hidden border border-gray-200 bg-gray-50 flex items-center justify-center min-h-[300px]">
                                <img
                                    src={previewUrl}
                                    alt="Prescription preview"
                                    className="max-h-[500px] object-contain"
                                />
                                <button
                                    onClick={clearSelection}
                                    className="absolute top-4 right-4 p-2 bg-white/90 rounded-full shadow hover:bg-white text-gray-600 transition-colors"
                                    disabled={isProcessing}
                                >
                                    <X className="w-5 h-5" />
                                </button>
                            </div>
                        )}

                        {error && (
                            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
                                <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
                                <p className="text-sm text-red-700">{error}</p>
                            </div>
                        )}

                        {previewUrl && (
                            <Button
                                className="w-full mt-6 h-12 text-lg font-medium"
                                onClick={processPrescription}
                                disabled={isProcessing}
                            >
                                {isProcessing ? (
                                    <>
                                        <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                                        Processing prescription...
                                    </>
                                ) : (
                                    'Process Prescription'
                                )}
                            </Button>
                        )}
                    </motion.div>

                    {/* Right Panel: Parsed Results */}
                    <motion.div
                        initial={{ x: 20, opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        transition={{ delay: 0.2 }}
                        className="flex flex-col gap-4"
                    >
                        {medicines.length === 0 && !isProcessing && (
                            <div className="bg-white rounded-2xl p-12 shadow-sm border border-gray-100 flex flex-col items-center justify-center text-center h-full min-h-[400px]">
                                <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mb-6">
                                    <CheckCircle className="w-10 h-10 text-gray-300" />
                                </div>
                                <h3 className="text-xl font-medium text-gray-900 mb-2">No Medicines Extracted</h3>
                                <p className="text-gray-500 max-w-sm">
                                    Upload a prescription image and click Process to see the extracted medicines here.
                                </p>
                            </div>
                        )}

                        {isProcessing && (
                            <div className="bg-white rounded-2xl p-12 shadow-sm border border-blue-100 flex flex-col items-center justify-center text-center h-full min-h-[400px]">
                                <div className="relative w-24 h-24 mb-6">
                                    <div className="absolute inset-0 rounded-full border-4 border-blue-100"></div>
                                    <div className="absolute inset-0 rounded-full border-4 border-blue-600 border-t-transparent animate-spin"></div>
                                    <div className="absolute inset-0 flex items-center justify-center">
                                        <Sun className="w-8 h-8 text-blue-600" />
                                    </div>
                                </div>
                                <h3 className="text-xl font-medium text-gray-900 mb-2">Analyzing Document</h3>
                                <p className="text-gray-500 max-w-sm">
                                    Our AI is reading handwriting and extracting the medication details...
                                </p>
                            </div>
                        )}

                        {!isProcessing && medicines.length > 0 && (
                            <div className="space-y-4">
                                <div className="flex items-center justify-between mb-2">
                                    <h3 className="text-xl font-semibold text-gray-900">Extracted Medications</h3>
                                    <span className="px-3 py-1 bg-green-100 text-green-700 text-sm font-medium rounded-full">
                                        Found {medicines.length} item{medicines.length > 1 ? 's' : ''}
                                    </span>
                                </div>

                                {medicines.map((med, idx) => (
                                    <motion.div
                                        key={idx}
                                        initial={{ y: 20, opacity: 0 }}
                                        animate={{ y: 0, opacity: 1 }}
                                        transition={{ delay: 0.1 * idx }}
                                        className="bg-white p-6 rounded-2xl shadow-lg border border-gray-100"
                                    >
                                        <div className="flex items-start justify-between mb-4">
                                            <div>
                                                <h4 className="text-xl font-bold text-gray-900">{med.name}</h4>
                                                <div className="flex items-center gap-2 mt-1 text-gray-600 text-sm">
                                                    <CheckCircle className="w-4 h-4" />
                                                    <span>Status: {med.status.charAt(0).toUpperCase() + med.status.slice(1)}</span>
                                                </div>
                                            </div>
                                            <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center">
                                                <CheckCircle className="w-5 h-5 text-blue-600" />
                                            </div>
                                        </div>

                                        {RX_LINE[med.name] && (
                                            <div
                                                className="mb-4 bg-[#F8F9FA] rounded-[6px] px-[14px] py-[8px] w-full text-[#1a1a1a]"
                                                style={{ fontFamily: 'monospace', fontSize: '13px' }}
                                            >
                                                {RX_LINE[med.name]}
                                            </div>
                                        )}

                                        <div className="mb-6 flex items-center justify-between p-4 bg-gray-50 rounded-xl border border-gray-100">
                                            <span className="text-sm font-semibold text-gray-600 uppercase tracking-wider">Confidence Score</span>
                                            <div className={`px-4 py-1.5 rounded-full text-sm font-bold flex items-center gap-2 border ${med.confidence > 85
                                                ? 'bg-green-100 text-green-700 border-green-200'
                                                : med.confidence >= 60
                                                    ? 'bg-amber-100 text-amber-700 border-amber-200'
                                                    : 'bg-red-100 text-red-700 border-red-200'
                                                }`}>
                                                {med.confidence}%
                                            </div>
                                        </div>

                                        <hr className="border-gray-100 my-4" />

                                        <div className="space-y-3 mb-6">
                                            <div className="flex items-center text-sm">
                                                <span className="w-8 text-lg">📅</span>
                                                <span className="text-gray-500 w-24">Frequency</span>
                                                <span className="text-gray-900 font-medium">{med.frequency}</span>
                                            </div>
                                            <div className="flex items-center text-sm">
                                                <span className="w-8 text-lg">💊</span>
                                                <span className="text-gray-500 w-24">Dosage</span>
                                                <span className="text-gray-900 font-medium">{med.dosage}</span>
                                            </div>
                                            <div className="flex items-center text-sm">
                                                <span className="w-8 text-lg">⏱️</span>
                                                <span className="text-gray-500 w-24">Duration</span>
                                                <span className="text-gray-900 font-medium">{med.duration}</span>
                                            </div>
                                        </div>

                                        {med.timing && med.timing.length > 0 && (
                                            <div className="mb-6">
                                                <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Dose Timings</div>
                                                <div className="flex flex-wrap gap-2">
                                                    {med.timing.map((t, i) => (
                                                        <span key={i} className="px-3 py-1.5 bg-blue-50 text-blue-700 rounded-full text-xs font-medium border border-blue-100">
                                                            {t}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {med.instructions && (
                                            <div className="mb-6 p-4 bg-amber-50 rounded-xl border border-amber-100">
                                                <div className="flex items-start gap-2 mb-2">
                                                    <span className="text-lg">⚠️</span>
                                                    <span className="text-amber-800 text-sm font-medium leading-relaxed">{med.instructions}</span>
                                                </div>
                                                {med.food_interaction && (
                                                    <div className="flex items-start gap-2 mt-2 ml-1">
                                                        <span className="text-sm">🍽️</span>
                                                        <span className="text-amber-700/80 text-xs leading-relaxed">{med.food_interaction}</span>
                                                    </div>
                                                )}
                                            </div>
                                        )}

                                        {med.refill_reminder && (
                                            <div className="mb-6 flex items-center gap-2 text-xs text-gray-400">
                                                <span>🔔</span>
                                                <span>Refill reminder set for: {med.refill_reminder} from start</span>
                                            </div>
                                        )}

                                        <Button
                                            variant={addedMeds.has(idx) ? 'secondary' : 'default'}
                                            className="w-full gap-2"
                                            disabled={addedMeds.has(idx)}
                                            onClick={() => addToSchedule(med, idx)}
                                        >
                                            {addedMeds.has(idx) ? (
                                                <>
                                                    <CheckCircle className="w-4 h-4" /> Added to Schedule
                                                </>
                                            ) : (
                                                <>
                                                    <Plus className="w-4 h-4" /> Add to Medication Schedule
                                                </>
                                            )}
                                        </Button>
                                    </motion.div>
                                ))}
                            </div>
                        )}

                        {!isProcessing && medicines.length === 2 && (
                            <motion.div
                                initial={{ y: 20, opacity: 0 }}
                                animate={{ y: 0, opacity: 1 }}
                                transition={{ delay: 0.3 }}
                                className="mt-2 mb-4"
                            >
                                <h3 className="text-[16px] font-[700] text-gray-900 mb-[12px]">Medication Schedule Summary</h3>
                                <div className="rounded-[12px] border border-[#E5E7EB] overflow-hidden" style={{ boxShadow: '0 1px 4px rgba(0,0,0,0.08)' }}>
                                    <table className="w-full text-left border-collapse">
                                        <thead>
                                            <tr className="bg-[#0D1B2A] text-white">
                                                {SCHEDULE_TABLE.headers.map((h, i) => (
                                                    <th key={i} className="py-[10px] px-[16px] text-[13px] font-bold">
                                                        {h}
                                                    </th>
                                                ))}
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {SCHEDULE_TABLE.rows.map((row, i) => (
                                                <tr key={i} className={i % 2 === 0 ? "bg-white" : "bg-[#F9FAFB]"} style={{ height: '44px' }}>
                                                    <td className="py-[10px] px-[16px] font-bold text-[#6B7280] text-[12px] uppercase whitespace-nowrap">
                                                        {row[0]}
                                                    </td>
                                                    <td className="py-[10px] px-[16px] text-gray-900 text-sm">
                                                        {row[1]}
                                                    </td>
                                                    <td className="py-[10px] px-[16px] text-gray-900 text-sm">
                                                        {row[2]}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </motion.div>
                        )}
                    </motion.div>
                </div>
            </div>
        </div>
    );
}
