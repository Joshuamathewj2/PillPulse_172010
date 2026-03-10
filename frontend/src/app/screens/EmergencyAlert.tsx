import { useNavigate } from 'react-router';
import TopNavigation from '../components/TopNavigation';
import { Button } from '../components/ui/button';
import {
  Phone,
  MapPin,
  Users,
  AlertTriangle,
  Navigation,
  Clock,
  ArrowLeft,
} from 'lucide-react';
import { motion } from 'motion/react';

const nearbyHospitals = [
  {
    name: 'City General Hospital',
    distance: '0.8 mi',
    time: '4 min',
    emergency: true,
  },
  {
    name: 'St. Mary Medical Center',
    distance: '1.2 mi',
    time: '7 min',
    emergency: true,
  },
  {
    name: 'Regional Health Clinic',
    distance: '2.1 mi',
    time: '12 min',
    emergency: false,
  },
];

export default function EmergencyAlert() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 via-rose-50 to-orange-50">
      <TopNavigation />

      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Emergency Warning Banner */}
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="mb-8"
        >
          <div className="bg-gradient-to-r from-red-600 to-rose-600 rounded-3xl p-8 text-white shadow-2xl border-4 border-red-700">
            <div className="flex items-start gap-4">
              <div className="w-16 h-16 bg-white rounded-2xl flex items-center justify-center shrink-0 animate-pulse">
                <AlertTriangle className="w-10 h-10 text-red-600" />
              </div>
              <div>
                <h1 className="text-3xl font-bold mb-2">⚠️ Possible Medical Emergency Detected</h1>
                <p className="text-red-100 text-lg">
                  Based on your symptoms, immediate medical attention may be required. Please take action now.
                </p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Critical Symptoms Detected */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-3xl shadow-xl border-2 border-red-200 p-8 mb-6"
        >
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Symptoms Flagged</h2>
          <div className="space-y-3">
            <div className="flex items-start gap-3 p-4 bg-red-50 rounded-xl">
              <div className="w-2 h-2 bg-red-500 rounded-full mt-2"></div>
              <div>
                <p className="font-medium text-gray-900">Chest Pain / Pressure</p>
                <p className="text-sm text-gray-600">Could indicate cardiac emergency</p>
              </div>
            </div>
            <div className="flex items-start gap-3 p-4 bg-red-50 rounded-xl">
              <div className="w-2 h-2 bg-red-500 rounded-full mt-2"></div>
              <div>
                <p className="font-medium text-gray-900">Difficulty Breathing</p>
                <p className="text-sm text-gray-600">Requires immediate assessment</p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Emergency Actions */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="grid md:grid-cols-3 gap-4 mb-8"
        >
          <motion.div
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="bg-gradient-to-br from-red-600 to-rose-600 rounded-2xl p-6 text-white shadow-xl cursor-pointer"
          >
            <div className="w-14 h-14 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center mb-4">
              <Phone className="w-8 h-8" />
            </div>
            <h3 className="text-xl font-bold mb-2">Call 911</h3>
            <p className="text-red-100 text-sm mb-4">Immediate emergency response</p>
            <Button className="w-full bg-white text-red-600 hover:bg-red-50">
              Call Now
            </Button>
          </motion.div>

          <motion.div
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="bg-white rounded-2xl p-6 shadow-lg border-2 border-red-200 cursor-pointer"
          >
            <div className="w-14 h-14 bg-red-100 rounded-xl flex items-center justify-center mb-4">
              <MapPin className="w-8 h-8 text-red-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Nearest Hospital</h3>
            <p className="text-gray-600 text-sm mb-4">Navigate to emergency room</p>
            <Button variant="outline" className="w-full border-red-300 text-red-600 hover:bg-red-50">
              Get Directions
            </Button>
          </motion.div>

          <motion.div
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="bg-white rounded-2xl p-6 shadow-lg border-2 border-red-200 cursor-pointer"
          >
            <div className="w-14 h-14 bg-red-100 rounded-xl flex items-center justify-center mb-4">
              <Users className="w-8 h-8 text-red-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Emergency Contact</h3>
            <p className="text-gray-600 text-sm mb-4">Notify your contact person</p>
            <Button variant="outline" className="w-full border-red-300 text-red-600 hover:bg-red-50">
              Send Alert
            </Button>
          </motion.div>
        </motion.div>

        {/* Nearby Hospitals Map Card */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="bg-white rounded-3xl shadow-xl border border-gray-200 overflow-hidden"
        >
          {/* Map Preview */}
          <div className="h-64 bg-gradient-to-br from-blue-100 to-teal-100 relative flex items-center justify-center">
            <div className="text-center">
              <MapPin className="w-16 h-16 text-blue-600 mx-auto mb-2" />
              <p className="text-gray-600">Interactive map would display here</p>
              <p className="text-sm text-gray-500">Showing nearby emergency facilities</p>
            </div>
            {/* Mock location markers */}
            <div className="absolute top-20 left-32 w-8 h-8 bg-red-500 rounded-full animate-pulse"></div>
            <div className="absolute top-32 right-24 w-8 h-8 bg-red-500 rounded-full animate-pulse"></div>
          </div>

          {/* Hospital List */}
          <div className="p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">Nearby Emergency Facilities</h3>
            <div className="space-y-3">
              {nearbyHospitals.map((hospital, idx) => (
                <motion.div
                  key={idx}
                  initial={{ x: -20, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: 0.4 + idx * 0.1 }}
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-xl hover:bg-blue-50 transition-colors cursor-pointer"
                >
                  <div className="flex items-start gap-3 flex-1">
                    <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center shrink-0">
                      <MapPin className="w-5 h-5 text-red-600" />
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900">{hospital.name}</h4>
                      <div className="flex items-center gap-3 mt-1">
                        <span className="text-sm text-gray-600 flex items-center gap-1">
                          <Navigation className="w-3 h-3" />
                          {hospital.distance}
                        </span>
                        <span className="text-sm text-gray-600 flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {hospital.time}
                        </span>
                        {hospital.emergency && (
                          <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full font-medium">
                            24/7 ER
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <Button size="sm" variant="outline" className="border-blue-300 text-blue-600 hover:bg-blue-50">
                    Navigate
                  </Button>
                </motion.div>
              ))}
            </div>
          </div>
        </motion.div>

        {/* Important Information */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="bg-amber-50 border-2 border-amber-200 rounded-2xl p-6 mt-6"
        >
          <h3 className="font-semibold text-gray-900 mb-3">While Waiting for Help</h3>
          <ul className="space-y-2">
            <li className="flex items-start gap-2 text-sm text-gray-700">
              <span className="text-amber-600 mt-0.5">•</span>
              Stay calm and sit or lie down in a comfortable position
            </li>
            <li className="flex items-start gap-2 text-sm text-gray-700">
              <span className="text-amber-600 mt-0.5">•</span>
              Do not drive yourself to the hospital
            </li>
            <li className="flex items-start gap-2 text-sm text-gray-700">
              <span className="text-amber-600 mt-0.5">•</span>
              If you have prescribed medication (e.g., nitroglycerin), take as directed
            </li>
            <li className="flex items-start gap-2 text-sm text-gray-700">
              <span className="text-amber-600 mt-0.5">•</span>
              Unlock your door so emergency responders can enter
            </li>
          </ul>
        </motion.div>

        {/* Back Button */}
        <div className="mt-8">
          <Button onClick={() => navigate('/')} variant="outline" className="gap-2">
            <ArrowLeft className="w-4 h-4" />
            Back to Chat
          </Button>
        </div>

        {/* Disclaimer */}
        <p className="text-center text-sm text-gray-500 mt-6">
          This is an AI assessment and not a substitute for professional medical judgment. If you believe you are experiencing a medical emergency, call 911 immediately.
        </p>
      </div>
    </div>
  );
}
