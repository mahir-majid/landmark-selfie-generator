'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import Earth from './components/Earth';
import LoadingSpinner from './components/LoadingSpinner';

const Home = () => {
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    document.title = 'Landmark Selfie Generator';
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 2000);

    return () => clearTimeout(timer);
  }, []);

  const handleLocationSelect = (landmark) => {
    // Navigate to selfie page with location data
    router.push(`/selfie?location=${encodeURIComponent(JSON.stringify(landmark))}`);
  };

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="min-h-screen">
      {/* Blue Background */}
      <div 
        className="fixed inset-0"
        style={{
          backgroundColor: '#3b82f6',
          zIndex: -9999
        }}
      />

      {/* Main Content */}
      <main className="relative z-10">
        {/* Earth Visualization */}
        <motion.div 
          className="h-[120vh] w-full"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, delay: 0.3 }}
        >
          <Earth onLocationSelect={handleLocationSelect} />
        </motion.div>
      </main>
    </div>
  );
};

export default Home;
