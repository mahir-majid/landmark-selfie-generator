'use client';

import React, { useCallback } from 'react';
import { motion } from 'framer-motion';
import { landmarks } from './landmarksData';
import LeafletMap from './LeafletMap';

const Earth = ({ onLocationSelect }) => {
  const handleLocationSelect = useCallback((landmark) => {
    if (onLocationSelect) {
      onLocationSelect(landmark);
    }
  }, [onLocationSelect]);

  return (
    <div className="relative w-full h-full overflow-hidden">
      {/* Background stars effect */}
      <div className="absolute inset-0 opacity-20">
        {[...Array(30)].map((_, i) => (
          <div
            key={i}
            className="absolute w-1 h-1 bg-white rounded-full animate-pulse"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 2}s`,
              animationDuration: `${2 + Math.random() * 3}s`
            }}
          />
        ))}
      </div>



      {/* Real Map - Leaflet */}
      <LeafletMap onLocationSelect={handleLocationSelect} />


    </div>
  );
};

export default Earth; 