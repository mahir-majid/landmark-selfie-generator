'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useSearchParams, useRouter } from 'next/navigation';
import { ArrowLeft, Upload, Camera, Sparkles, Download, Shirt, Briefcase, Zap } from 'lucide-react';
import { fitOptions, generateCompletePrompt, regenerateStyle } from './promptUtils';

const SelfiePage = () => {
  // Helper function to map icon names to icon components
  const getIconComponent = (iconName) => {
    switch (iconName) {
      case 'Shirt':
        return Shirt;
      case 'Briefcase':
        return Briefcase;
      case 'Zap':
        return Zap;
      default:
        return Shirt;
    }
  };
  const searchParams = useSearchParams();
  const router = useRouter();
  const [location, setLocation] = useState(null);
  const [faceImage, setFaceImage] = useState(null);
  const [prompt, setPrompt] = useState('');
  const [selectedFit, setSelectedFit] = useState('casual');
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [isDayTime, setIsDayTime] = useState(true);
  
  // Set default prompt when location changes
  useEffect(() => {
    if (location) {
      const defaultPrompt = generateCompletePrompt(selectedFit, location.name, isDayTime);
      setPrompt(defaultPrompt);
    }
  }, [location, selectedFit, isDayTime]);
  const [generatedImage, setGeneratedImage] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  useEffect(() => {
    document.title = 'Landmark Selfie Generator';
  }, []);

  useEffect(() => {
    const locationParam = searchParams.get('location');
    if (locationParam) {
      try {
        setLocation(JSON.parse(decodeURIComponent(locationParam)));
      } catch (error) {
        console.error('Error parsing location:', error);
        router.push('/');
      }
    } else {
        router.push('/');
    }
  }, [searchParams, router]);

  const handleFaceImageUpload = (file) => {
    if (file && file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setFaceImage(e.target.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFaceImageUpload(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFaceImageUpload(e.target.files[0]);
    }
  };

  const generateImage = async () => {
    if (!faceImage || !prompt.trim()) {
      alert('Please upload a face image and enter a prompt');
      return;
    }

    setIsGenerating(true);
    
    try {
      // Convert base64 data URL to file for upload
      const base64Response = await fetch(faceImage);
      const blob = await base64Response.blob();
      
      // Create FormData for the API request
      const formData = new FormData();
      formData.append('face_image', blob, 'face.jpg');
      formData.append('prompt', prompt);
      
      // Call FastAPI endpoint
      const response = await fetch('http://localhost:8000/generate-selfie', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate image');
      }
      
      const result = await response.json();
      console.log('API Response:', result); // Debug log
      
      if (result.success && result.image) {
        // Ensure the image data is properly formatted for display
        let imageData = result.image;
        if (!imageData.startsWith('data:image/')) {
          // If it's just base64 without data URL prefix, add it
          imageData = `data:image/jpeg;base64,${imageData}`;
        }
        console.log('Formatted image data:', imageData.substring(0, 100) + '...'); // Debug log
        setGeneratedImage(imageData);
      } else {
        throw new Error('No image generated');
      }
    } catch (error) {
      console.error('Error generating image:', error);
      alert(`Error generating image: ${error.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const downloadImage = () => {
    if (generatedImage) {
      const link = document.createElement('a');
      link.href = generatedImage;
      link.download = `selfie-${location?.name}-${Date.now()}.png`;
      link.click();
    }
  };

  if (!location) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-4 animate-spin">🔄</div>
          <div className="text-xl">Loading location...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
      {/* Header */}
      <motion.header 
        className="bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-50"
        initial={{ y: -100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.6 }}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <button
              onClick={() => router.push('/')}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
              Back to Map
            </button>
            
            <div className="flex items-center gap-3">
              <span className="text-2xl">{location.icon}</span>
              <div className="text-center">
                <h1 className="text-xl font-bold text-gray-900">{location.name}</h1>
                <p className="text-sm text-gray-600">{location.country}</p>
              </div>
            </div>
            
            <div className="w-20"></div> {/* Spacer for centering */}
          </div>
        </div>
      </motion.header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Top Control Buttons */}
        <div className="mb-6 flex gap-3">
          {/* Day/Night Toggle */}
          <motion.button
            onClick={() => setIsDayTime(!isDayTime)}
            className={`inline-flex items-center justify-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 shadow-sm w-32 ${
              isDayTime 
                ? 'bg-yellow-100 text-yellow-700 border-2 border-yellow-500 hover:bg-yellow-200 hover:border-yellow-600' 
                : 'bg-indigo-100 text-indigo-700 border-2 border-black hover:bg-indigo-200 hover:border-gray-800'
            }`}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            {isDayTime ? (
              <>
                <span className="text-yellow-600">☀️</span>
                Day
              </>
            ) : (
              <>
                <span className="text-indigo-600">🌙</span>
                Night
              </>
            )}
          </motion.button>
          
          {/* New Clothes Button */}
          <motion.button
            onClick={() => {
              setIsRegenerating(true);
              regenerateStyle(
                selectedFit,
                location.name,
                setPrompt,
                isDayTime
              );
              setTimeout(() => setIsRegenerating(false), 1000);
            }}
            className={`inline-flex items-center justify-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 shadow-sm w-36 ${
              isRegenerating 
                ? 'bg-purple-100 text-purple-700 border-2 border-purple-500 hover:bg-purple-200 hover:border-purple-600' 
                : 'bg-purple-100 text-purple-700 border-2 border-purple-500 hover:bg-purple-200 hover:border-purple-600'
            }`}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <span className={`inline-block mr-1 ${isRegenerating ? 'animate-spin' : ''}`}>🔄</span>
            <span className="whitespace-nowrap">New Clothes</span>
          </motion.button>
          
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Left Column - Inputs */}
          <motion.div 
            className="space-y-6"
            initial={{ x: -50, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            
            {/* Top Row - Face Upload and Style Selector */}
            <div className="flex gap-4">
              {/* Face Upload Section */}
              <div className="bg-white rounded-xl shadow-lg p-4 border border-gray-100 flex-1">
                <h2 className="text-base font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <Camera className="w-4 h-4 text-blue-600" />
                  Upload Your Face
                </h2>
                
                <div
                  className={`border-2 border-dashed rounded-lg p-4 text-center transition-all duration-200 flex items-center justify-center h-28 ${
                    dragActive 
                      ? 'border-blue-500 bg-blue-50' 
                      : 'border-gray-300 hover:border-gray-400'
                  }`}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                >
                  {faceImage ? (
                    <div className="space-y-2">
                      <img 
                        src={faceImage} 
                        alt="Uploaded face" 
                        className="w-20 h-20 mx-auto rounded-full object-cover border-2 border-white shadow-md"
                        style={{ objectPosition: 'center 20%' }}
                      />
                      <button
                        onClick={() => setFaceImage(null)}
                        className="text-red-600 hover:text-red-700 text-xs font-medium"
                      >
                        Remove
                      </button>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <Upload className="w-8 h-8 mx-auto text-gray-400" />
                      <div>
                        <p className="text-sm text-gray-600">
                          Drag & drop or{' '}
                          <label className="text-blue-600 hover:text-blue-700 cursor-pointer font-medium">
                            browse
                            <input
                              type="file"
                              accept="image/*"
                              onChange={handleFileInput}
                              className="hidden"
                            />
                          </label>
                        </p>
                        <p className="text-xs text-gray-500">
                          JPG, PNG, GIF up to 10MB
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Fit Selector Section */}
              <div className="bg-white rounded-xl shadow-lg p-4 border border-gray-100 flex-1 flex flex-col">
                <h2 className="text-base font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-purple-600" />
                  Choose Your Style
                </h2>
                
                <div className="grid grid-cols-2 gap-2 mb-1">
                  {fitOptions.map((fit) => {
                    const IconComponent = getIconComponent(fit.icon);
                    const isSelected = selectedFit === fit.id;
                    
                    return (
                      <motion.button
                        key={fit.id}
                        onClick={() => setSelectedFit(fit.id)}
                        className={`relative p-6 min-h-[110px] rounded-lg border-2 transition-all duration-200 ${
                          isSelected
                            ? `border-transparent bg-gradient-to-br ${fit.color} text-white shadow-md scale-105`
                            : 'border-gray-200 bg-gray-50 text-gray-700 hover:border-gray-300 hover:bg-gray-100'
                        }`}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                      >
                        <div className="flex flex-col items-center space-y-2">
                          <IconComponent className={`w-6 h-6 ${isSelected ? 'text-white' : 'text-gray-600'}`} />
                          <span className="text-sm font-medium">{fit.label}</span>
                        </div>
                        
                        {isSelected && (
                          <motion.div
                            className="absolute -top-1 -right-1 w-5 h-5 bg-white rounded-full flex items-center justify-center"
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            transition={{ type: "spring", stiffness: 500, damping: 30 }}
                          >
                            <div className="w-2.5 h-2.5 bg-green-500 rounded-full"></div>
                          </motion.div>
                        )}
                      </motion.button>
                    );
                  })}
                </div>
                

              </div>
            </div>


            {/* Generate Button */}
            <button
              onClick={generateImage}
              disabled={!faceImage || !prompt.trim() || isGenerating}
              className={`w-full py-4 px-6 rounded-xl font-semibold text-lg transition-all duration-200 flex items-center justify-center gap-3 ${
                !faceImage || !prompt.trim() || isGenerating
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:from-blue-700 hover:to-purple-700 transform hover:scale-105 shadow-lg'
              }`}
            >
              {isGenerating ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Generating...
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  Generate My Selfie
                </>
              )}
            </button>
          </motion.div>

          {/* Right Column - Generated Image */}
          <motion.div 
            className="space-y-6"
            initial={{ x: 50, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            
            <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100 h-[75vh]">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-green-600" />
                Your Generated Selfie
              </h2>
              
              <div className="bg-gray-50 rounded-xl flex items-center justify-center">
                {isGenerating ? (
                  <div className="text-center space-y-4">
                    <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
                    <div className="space-y-2">
                      <p className="text-lg font-medium text-gray-700">Creating your dream selfie...</p>
                      <p className="text-sm text-gray-500">This may take a few moments</p>
                    </div>
                  </div>
                ) : generatedImage ? (
                  <div className="w-full h-full flex items-center justify-center">
                    <img 
                      src={generatedImage} 
                      alt="Generated selfie" 
                      className="w-full h-full object-cover rounded-xl"
                      onError={(e) => {
                        console.error('Image failed to load:', e);
                        console.log('Image src was:', generatedImage);
                      }}
                      onLoad={() => console.log('Image loaded successfully')}
                    />
                  </div>
                ) : (
                  <div className="text-center space-y-4">
                    <div className="w-20 h-20 bg-gray-200 rounded-full flex items-center justify-center mx-auto">
                      <Camera className="w-10 h-10 text-gray-400" />
                    </div>
                    <div className="space-y-2">
                      <p className="text-lg font-medium text-gray-700">Ready to create magic?</p>
                      <p className="text-sm text-gray-500">
                        Upload your photo, write a prompt, and click generate to see yourself at {location.name}!
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        </div>
      </main>
    </div>
  );
};

export default SelfiePage;
