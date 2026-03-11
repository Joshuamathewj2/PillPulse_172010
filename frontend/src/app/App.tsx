import { RouterProvider } from 'react-router';
import { router } from './routes';
import { Toaster } from './components/ui/sonner';
import { useState, useEffect } from 'react';
import CaregiverPortal from './screens/CaregiverPortal';
import CaregiverDashboard from './screens/CaregiverDashboard';
import Onboarding from './screens/Onboarding';
import DevModeWidget from './components/DevModeWidget';
import SplashScreen from './components/SplashScreen';

const isFirebaseConfigMissing = !import.meta.env.VITE_FIREBASE_API_KEY || 
  !import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || 
  !import.meta.env.VITE_FIREBASE_PROJECT_ID;

export default function App() {
  const [role, setRole] = useState<string | null>(localStorage.getItem('userRole'));
  const [showSplash, setShowSplash] = useState(() => {
    // Show splash only once per session
    return !sessionStorage.getItem('pillpulse_splash_shown');
  });

  useEffect(() => {
    if (!showSplash) {
      sessionStorage.setItem('pillpulse_splash_shown', 'true');
    }
  }, [showSplash]);

  if (showSplash) {
    return <SplashScreen onComplete={() => setShowSplash(false)} />;
  }

  // If URL contains ?caregiver=true, show CaregiverPortal directly
  const params = new URLSearchParams(window.location.search);
  const isCaregiverModeFromUrl = params.get('caregiver') === 'true' && params.get('patient');

  if (isCaregiverModeFromUrl) {
    return (
      <>
        {isFirebaseConfigMissing && (
          <div className="bg-red-600 text-white text-xs font-bold py-2 px-4 text-center sticky top-0 z-[9999] animate-pulse">
            ⚠️ Firebase config missing - check env variables
          </div>
        )}
        <CaregiverPortal />
        <DevModeWidget />
      </>
    );
  }

  if (!role) {
    return (
      <>
        {isFirebaseConfigMissing && (
          <div className="bg-red-600 text-white text-xs font-bold py-2 px-4 text-center sticky top-0 z-[9999] animate-pulse">
            ⚠️ Firebase config missing - check env variables
          </div>
        )}
        <Onboarding onComplete={() => setRole(localStorage.getItem('userRole'))} />
        <DevModeWidget />
      </>
    );
  }

  if (role === 'caregiver') {
    return (
      <>
        {isFirebaseConfigMissing && (
          <div className="bg-red-600 text-white text-xs font-bold py-2 px-4 text-center sticky top-0 z-[9999] animate-pulse">
            ⚠️ Firebase config missing - check env variables
          </div>
        )}
        <CaregiverDashboard />
        <Toaster />
        <DevModeWidget />
      </>
    );
  }

  return (
    <>
      {isFirebaseConfigMissing && (
        <div className="bg-red-600 text-white text-xs font-bold py-2 px-4 text-center sticky top-0 z-[9999] animate-pulse">
          ⚠️ Firebase config missing - check env variables
        </div>
      )}
      <RouterProvider router={router} />
      <Toaster />
      <DevModeWidget />
    </>
  );
}
