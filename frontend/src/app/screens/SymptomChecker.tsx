import { useState } from 'react';
import { useNavigate } from 'react-router';
import TopNavigation from '../components/TopNavigation';
import { Button } from '../components/ui/button';
import { Progress } from '../components/ui/progress';
import {
  Brain,
  Heart,
  Activity,
  User,
  AlertTriangle,
  Info,
  CheckCircle2,
  ArrowRight,
  ArrowLeft,
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

type BodyPart = 'head' | 'chest' | 'stomach' | 'limbs' | 'full-body';
type Severity = 'mild' | 'moderate' | 'severe';

export default function SymptomChecker() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [selectedBodyPart, setSelectedBodyPart] = useState<BodyPart | null>(null);
  const [severity, setSeverity] = useState<Severity | null>(null);
  const [duration, setDuration] = useState<string | null>(null);

  const totalSteps = 4;
  const progress = (step / totalSteps) * 100;

  const bodyParts: { id: BodyPart; label: string; icon: typeof Brain }[] = [
    { id: 'head', label: 'Head', icon: Brain },
    { id: 'chest', label: 'Chest', icon: Heart },
    { id: 'stomach', label: 'Stomach', icon: Activity },
    { id: 'limbs', label: 'Limbs', icon: User },
    { id: 'full-body', label: 'Full Body', icon: User },
  ];

  const severityLevels: { id: Severity; label: string; color: string }[] = [
    { id: 'mild', label: 'Mild', color: 'green' },
    { id: 'moderate', label: 'Moderate', color: 'yellow' },
    { id: 'severe', label: 'Severe', color: 'red' },
  ];

  const durations = [
    { id: 'hours', label: 'Few hours' },
    { id: '1-2days', label: '1-2 days' },
    { id: '3-7days', label: '3-7 days' },
    { id: 'week+', label: 'More than a week' },
  ];

  const handleNext = () => {
    if (step < totalSteps) {
      setStep(step + 1);
    } else {
      // Show results
      setStep(totalSteps + 1);
    }
  };

  const handleBack = () => {
    if (step > 1) {
      setStep(step - 1);
    } else {
      navigate('/');
    }
  };

  const renderStep = () => {
    switch (step) {
      case 1:
        return (
          <motion.div
            key="step1"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            <div className="text-center mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                Where are you experiencing symptoms?
              </h2>
              <p className="text-gray-600">Select the area of your body</p>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {bodyParts.map((part) => {
                const Icon = part.icon;
                const isSelected = selectedBodyPart === part.id;
                return (
                  <motion.button
                    key={part.id}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => setSelectedBodyPart(part.id)}
                    className={`p-6 rounded-2xl border-2 transition-all ${
                      isSelected
                        ? 'border-blue-500 bg-blue-50 shadow-lg'
                        : 'border-gray-200 bg-white hover:border-blue-300'
                    }`}
                  >
                    <div className={`w-16 h-16 mx-auto rounded-xl flex items-center justify-center mb-3 ${
                      isSelected ? 'bg-blue-100' : 'bg-gray-100'
                    }`}>
                      <Icon className={`w-8 h-8 ${isSelected ? 'text-blue-600' : 'text-gray-600'}`} />
                    </div>
                    <p className={`font-medium ${isSelected ? 'text-blue-900' : 'text-gray-700'}`}>
                      {part.label}
                    </p>
                  </motion.button>
                );
              })}
            </div>
          </motion.div>
        );

      case 2:
        return (
          <motion.div
            key="step2"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            <div className="text-center mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                How severe is the pain or discomfort?
              </h2>
              <p className="text-gray-600">Rate your symptom severity</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-3xl mx-auto">
              {severityLevels.map((level) => {
                const isSelected = severity === level.id;
                const colorClasses = {
                  green: 'border-green-500 bg-green-50',
                  yellow: 'border-yellow-500 bg-yellow-50',
                  red: 'border-red-500 bg-red-50',
                }[level.color];

                const iconColor = {
                  green: 'text-green-600',
                  yellow: 'text-yellow-600',
                  red: 'text-red-600',
                }[level.color];

                return (
                  <motion.button
                    key={level.id}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => setSeverity(level.id)}
                    className={`p-8 rounded-2xl border-2 transition-all ${
                      isSelected ? colorClasses + ' shadow-lg' : 'border-gray-200 bg-white hover:border-gray-300'
                    }`}
                  >
                    <div className={`w-16 h-16 mx-auto rounded-full flex items-center justify-center mb-4 ${
                      isSelected ? 'bg-white/80' : 'bg-gray-100'
                    }`}>
                      <Info className={`w-8 h-8 ${isSelected ? iconColor : 'text-gray-600'}`} />
                    </div>
                    <p className="text-xl font-semibold text-gray-900 mb-2">{level.label}</p>
                    <p className="text-sm text-gray-600">
                      {level.id === 'mild' && 'Noticeable but manageable'}
                      {level.id === 'moderate' && 'Affects daily activities'}
                      {level.id === 'severe' && 'Difficult to manage'}
                    </p>
                  </motion.button>
                );
              })}
            </div>
          </motion.div>
        );

      case 3:
        return (
          <motion.div
            key="step3"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            <div className="text-center mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                How long have you had these symptoms?
              </h2>
              <p className="text-gray-600">Duration helps us understand urgency</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto">
              {durations.map((dur) => {
                const isSelected = duration === dur.id;
                return (
                  <motion.button
                    key={dur.id}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => setDuration(dur.id)}
                    className={`p-6 rounded-2xl border-2 transition-all text-left ${
                      isSelected
                        ? 'border-blue-500 bg-blue-50 shadow-lg'
                        : 'border-gray-200 bg-white hover:border-blue-300'
                    }`}
                  >
                    <p className={`text-lg font-medium ${isSelected ? 'text-blue-900' : 'text-gray-900'}`}>
                      {dur.label}
                    </p>
                  </motion.button>
                );
              })}
            </div>
          </motion.div>
        );

      case 4:
        return (
          <motion.div
            key="step4"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            <div className="text-center mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                Any additional symptoms?
              </h2>
              <p className="text-gray-600">Select all that apply</p>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-3 max-w-3xl mx-auto">
              {['Fever', 'Nausea', 'Fatigue', 'Cough', 'Dizziness', 'Loss of appetite'].map((symptom) => (
                <motion.button
                  key={symptom}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="p-4 rounded-xl border-2 border-gray-200 bg-white hover:border-blue-300 transition-all"
                >
                  <p className="font-medium text-gray-700">{symptom}</p>
                </motion.button>
              ))}
            </div>
          </motion.div>
        );

      case 5:
        return (
          <motion.div
            key="results"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="space-y-6"
          >
            <div className="text-center mb-8">
              <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-teal-500 rounded-full mx-auto mb-4 flex items-center justify-center">
                <CheckCircle2 className="w-10 h-10 text-white" />
              </div>
              <h2 className="text-2xl font-semibold text-gray-900 mb-2">Assessment Complete</h2>
              <p className="text-gray-600">Here's what we found based on your symptoms</p>
            </div>

            {/* Results Cards */}
            <div className="space-y-4 max-w-2xl mx-auto">
              {/* Risk Level */}
              <div className="bg-yellow-50 border-2 border-yellow-200 rounded-2xl p-6">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 bg-yellow-100 rounded-xl flex items-center justify-center shrink-0">
                    <AlertTriangle className="w-6 h-6 text-yellow-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-2">Moderate Concern</h3>
                    <p className="text-sm text-gray-700">
                      Based on your symptoms, we recommend consulting with a healthcare provider within the next 24-48 hours.
                    </p>
                  </div>
                </div>
              </div>

              {/* Possible Conditions */}
              <div className="bg-white border-2 border-gray-200 rounded-2xl p-6">
                <h3 className="font-semibold text-gray-900 mb-4">Possible Conditions</h3>
                <ul className="space-y-3">
                  <li className="flex items-start gap-3">
                    <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2"></div>
                    <div>
                      <p className="font-medium text-gray-900">Viral Infection</p>
                      <p className="text-sm text-gray-600">Most likely - Common symptoms match</p>
                    </div>
                  </li>
                  <li className="flex items-start gap-3">
                    <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2"></div>
                    <div>
                      <p className="font-medium text-gray-900">Migraine</p>
                      <p className="text-sm text-gray-600">Possible - Consider if recurring</p>
                    </div>
                  </li>
                  <li className="flex items-start gap-3">
                    <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2"></div>
                    <div>
                      <p className="font-medium text-gray-900">Stress-related</p>
                      <p className="text-sm text-gray-600">Less likely - Monitor patterns</p>
                    </div>
                  </li>
                </ul>
              </div>

              {/* Recommended Actions */}
              <div className="bg-green-50 border-2 border-green-200 rounded-2xl p-6">
                <h3 className="font-semibold text-gray-900 mb-4">Recommended Next Steps</h3>
                <ul className="space-y-3">
                  <li className="flex items-start gap-3">
                    <CheckCircle2 className="w-5 h-5 text-green-600 shrink-0 mt-0.5" />
                    <p className="text-sm text-gray-700">Rest and maintain hydration</p>
                  </li>
                  <li className="flex items-start gap-3">
                    <CheckCircle2 className="w-5 h-5 text-green-600 shrink-0 mt-0.5" />
                    <p className="text-sm text-gray-700">Monitor temperature and symptoms</p>
                  </li>
                  <li className="flex items-start gap-3">
                    <CheckCircle2 className="w-5 h-5 text-green-600 shrink-0 mt-0.5" />
                    <p className="text-sm text-gray-700">Book a doctor's appointment for evaluation</p>
                  </li>
                </ul>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-3 max-w-2xl mx-auto pt-4">
              <Button onClick={() => navigate('/actions')} className="flex-1 gap-2" size="lg">
                Book Doctor Appointment
                <ArrowRight className="w-4 h-4" />
              </Button>
              <Button onClick={() => navigate('/actions')} variant="outline" className="flex-1" size="lg">
                Find Pharmacy
              </Button>
              <Button onClick={() => navigate('/')} variant="outline" className="flex-1" size="lg">
                Continue Chat
              </Button>
            </div>
          </motion.div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-teal-50/20">
      <TopNavigation />

      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Progress Header */}
        {step <= totalSteps && (
          <div className="mb-8">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600">Step {step} of {totalSteps}</span>
              <span className="text-sm font-medium text-blue-600">{Math.round(progress)}%</span>
            </div>
            <Progress value={progress} className="h-2" />
          </div>
        )}

        {/* Main Content Card */}
        <div className="bg-white rounded-3xl shadow-xl border border-gray-100 p-8 md:p-12 min-h-[500px]">
          <AnimatePresence mode="wait">{renderStep()}</AnimatePresence>
        </div>

        {/* Navigation Buttons */}
        {step <= totalSteps && (
          <div className="flex justify-between mt-6">
            <Button onClick={handleBack} variant="outline" className="gap-2">
              <ArrowLeft className="w-4 h-4" />
              Back
            </Button>
            <Button
              onClick={handleNext}
              disabled={
                (step === 1 && !selectedBodyPart) ||
                (step === 2 && !severity) ||
                (step === 3 && !duration)
              }
              className="gap-2"
            >
              {step === totalSteps ? 'View Results' : 'Continue'}
              <ArrowRight className="w-4 h-4" />
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
