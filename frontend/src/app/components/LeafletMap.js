'use client';

import React, { useEffect, useRef, useState } from 'react';
import { landmarks } from './landmarksData';

const LeafletMap = ({ onLocationSelect }) => {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  useEffect(() => {
    if (!isClient || !mapRef.current) return;

    // Dynamically import Leaflet only on client side
    const loadLeaflet = async () => {
      try {
        const L = await import('leaflet');
        await import('leaflet/dist/leaflet.css');

        // Fix Leaflet icon issues
        delete L.Icon.Default.prototype._getIconUrl;
        L.Icon.Default.mergeOptions({
          iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
          iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
          shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
        });

        // Initialize the map with better settings
        const map = L.map(mapRef.current, {
          center: [0, 0],
          zoom: 2,
          minZoom: 2, // Increased to 2 to absolutely prevent multiple continent renderings
          maxZoom: 8, // Reduced from 10 to keep reasonable detail level
          zoomControl: false,
          attributionControl: false,
          dragging: true,
          touchZoom: true,
          scrollWheelZoom: true,
          doubleClickZoom: true,
          boxZoom: true,
          keyboard: true,
          worldCopyJump: false, // Disable world wrapping to prevent duplicates
          maxBounds: [[-90, -180], [90, 180]], // Full world bounds
        });

        // Use Esri World Street Map for English labels globally
        const colorfulTileLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {
          maxZoom: 8, // Match our map maxZoom
          attribution: '© Esri'
        });

        // Add colorful tile layer
        colorfulTileLayer.addTo(map);



        // Zoom constraints to prevent multiple continent renderings
        map.on('zoomend', function() {
          const currentZoom = map.getZoom();
          if (currentZoom < 2) {
            map.setZoom(2, { animate: false });
          }
          if (currentZoom > 8) {
            map.setZoom(8, { animate: false });
          }
        });

        // Prevent zooming beyond limits during zoom (real-time prevention)
        map.on('zoom', function() {
          const currentZoom = map.getZoom();
          if (currentZoom < 2) {
            map.setZoom(2, { animate: false });
            return false; // Stop the zoom operation
          }
          if (currentZoom > 8) {
            map.setZoom(8, { animate: false });
            return false; // Stop the zoom operation
          }
        });

        // Block wheel zoom beyond limits
        map.on('wheel', function(e) {
          const currentZoom = map.getZoom();
          if (e.deltaY > 0 && currentZoom <= 2) { // Zooming out
            e.preventDefault();
            e.stopPropagation();
            return false;
          }
          if (e.deltaY < 0 && currentZoom >= 8) { // Zooming in
            e.preventDefault();
            e.stopPropagation();
            return false;
          }
        });

        // Constrain map bounds to prevent multiple continent renderings
        const maxBounds = L.latLngBounds([[-90, -180], [90, 180]]);
        map.setMaxBounds(maxBounds);

        // Force initial view to be within bounds
        map.setView([0, 0], 2, { animate: false });

        // Add view reset function to prevent overflow
        map.on('viewreset', function() {
          const center = map.getCenter();
          const zoom = map.getZoom();
          
          // Ensure zoom is within bounds
          if (zoom < 2) map.setZoom(2, { animate: false });
          if (zoom > 8) map.setZoom(8, { animate: false });
          
          // Ensure center is within bounds
          if (center.lat < -90) map.setView([-90, center.lng], zoom, { animate: false });
          if (center.lat > 90) map.setView([90, center.lng], zoom, { animate: false });
        });

        // Add scale control with better styling
        L.control.scale({
          position: 'bottomleft',
          metric: true,
          imperial: true,
          maxWidth: 200
        }).addTo(map);

        // Add landmarks with improved positioning and styling
        landmarks.forEach(landmark => {
          // Create custom colorful icon for landmarks
                           const landmarkIcon = L.divIcon({
                   className: 'landmark-marker',
                   html: `
                     <div class="relative group">
                       <div class="w-6 h-6 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-full border-2 border-white shadow-lg animate-pulse"></div>
                       <div class="absolute -top-1 -right-1 w-4 h-4 bg-white rounded-full flex items-center justify-center text-xs shadow-md">
                         ${landmark.icon}
                       </div>
                       
                       <!-- Sexy Purple Hover Overlay -->
                       <div class="absolute ${landmark.lat < 0 ? 'top-8' : '-top-29'} left-1/2 transform -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-all duration-300 ease-out pointer-events-none z-50">
                         <div class="bg-gradient-to-r from-purple-600/95 to-purple-800/95 backdrop-blur-md border border-purple-400/50 rounded-lg px-3 py-2 shadow-xl min-w-[160px] max-w-[180px]">
                           <div class="flex items-center gap-2 mb-1">
                             <div class="text-sm">${landmark.icon}</div>
                             <div>
                               <div class="text-white font-semibold text-xs">${landmark.name}</div>
                               <div class="text-purple-200 text-xs">${landmark.country}</div>
                             </div>
                           </div>
                           <div class="mb-1">
                             <span class="inline-block px-1.5 py-0.5 bg-purple-500/30 text-purple-100 text-xs rounded-full font-medium border border-purple-400/30">
                               ${landmark.category}
                             </span>
                           </div>
                           <div class="text-purple-200 text-xs leading-tight line-clamp-2">
                             ${landmark.description}
                           </div>
                         </div>
                         <!-- Purple Arrow -->
                         <div class="absolute ${landmark.lat < 0 ? '-top-1' : '-bottom-1'} left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-3 border-r-3 ${landmark.lat < 0 ? 'border-b-3 border-transparent border-b-purple-600/95' : 'border-t-3 border-transparent border-t-purple-600/95'}"></div>
                       </div>
                     </div>
                   `,
                   iconSize: [24, 24],
                   iconAnchor: [12, 24],
                   popupAnchor: [0, -12]
                 });

          // Add marker to map with proper coordinates
          const marker = L.marker([landmark.lat, landmark.lng], {
            icon: landmarkIcon,
            title: landmark.name
          }).addTo(map);



          // Add click handler
          marker.on('click', () => {
            if (onLocationSelect) {
              onLocationSelect(landmark);
            }
          });

          // Add hover effects
          marker.on('mouseover', function() {
            this.setZIndexOffset(1000);
          });
          
          marker.on('mouseout', function() {
            this.setZIndexOffset(0);
          });
        });

        // Store map instance
        mapInstanceRef.current = map;

        // Cleanup function
        return () => {
          if (mapInstanceRef.current) {
            mapInstanceRef.current.remove();
          }
        };
      } catch (error) {
        console.error('Failed to load Leaflet:', error);
      }
    };

    loadLeaflet();
  }, [isClient, onLocationSelect]);



  if (!isClient) {
    return (
      <div className="flex items-center justify-center h-full text-white">
        <div className="text-center">
          <div className="text-4xl mb-4 animate-pulse">🗺️</div>
          <div className="text-xl font-semibold mb-2">Loading Professional Map</div>
          <div className="text-sm text-gray-300">Preparing your world exploration experience...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full">
      <div ref={mapRef} className="w-full h-full" />
      
      {/* Enhanced Custom CSS for Leaflet */}
                   <style jsx global>{`
               .leaflet-container {
                 background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 50%, #1e40af 100%);
                 font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                 overflow: visible !important;
                 max-width: 100vw !important;
                 max-height: 100vh !important;
                 border: none !important;
                 outline: none !important;
               }
        
        .landmark-marker {
          background: transparent;
          border: none;
          transition: all 0.3s ease;
        }
        
        .landmark-marker:hover {
          transform: scale(1.1);
          z-index: 1000 !important;
        }
        

        
        .leaflet-control-layers {
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(20px);
          border-radius: 12px;
          border: 2px solid rgba(59, 130, 246, 0.2);
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
          padding: 8px;
        }
        
        .leaflet-control-layers label {
          font-weight: 500;
          color: #374151;
        }
        
        .leaflet-control-zoom {
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(20px);
          border-radius: 12px;
          border: 2px solid rgba(59, 130, 246, 0.2);
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
          overflow: hidden;
        }
        
        .leaflet-control-zoom a {
          color: #374151;
          font-weight: 600;
          transition: all 0.2s ease;
        }
        
        .leaflet-control-zoom a:hover {
          background: #3b82f6;
          color: white;
        }
        
        .leaflet-control-scale {
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(20px);
          border-radius: 8px;
          border: 2px solid rgba(59, 130, 246, 0.2);
          padding: 6px 12px;
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
        }
        
        .leaflet-control-scale-line {
          border: 2px solid #3b82f6;
          border-top: none;
          color: #374151;
          font-weight: 500;
        }
        

      `}</style>
    </div>
  );
};

export default LeafletMap; 