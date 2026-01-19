export const landmarks = [
  {
    id: 'niagara-falls',
    name: 'Niagara Falls',
    lat: 43.0962,
    lng: -79.0377,
    country: 'Canada/USA',
    description: 'Majestic waterfalls on the border of Canada and the United States',
    category: 'natural',
    icon: '🌊'
  },


  {
    id: 'grand-canyon',
    name: 'Grand Canyon',
    lat: 36.1069,
    lng: -112.1129,
    country: 'USA',
    description: 'Breathtaking natural wonder carved by the Colorado River',
    category: 'natural',
    icon: '🏞️'
  },
  {
    id: 'burj-khalifa',
    name: 'Burj Khalifa',
    lat: 25.1972,
    lng: 55.2744,
    country: 'UAE',
    description: 'Tallest building in the world',
    category: 'architecture',
    icon: '🏗️'
  },
  {
    id: 'eiffel-tower',
    name: 'Eiffel Tower',
    lat: 48.8584,
    lng: 2.2945,
    country: 'France',
    description: 'Iconic iron lattice tower in Paris',
    category: 'monument',
    icon: '🗼'
  },
  {
    id: 'taj-mahal',
    name: 'Taj Mahal',
    lat: 27.1751,
    lng: 78.0421,
    country: 'India',
    description: 'Magnificent white marble mausoleum',
    category: 'monument',
    icon: '🕌'
  },
  {
    id: 'great-wall',
    name: 'Great Wall of China',
    lat: 40.4319,
    lng: 116.5704,
    country: 'China',
    description: 'Ancient defensive structure spanning thousands of miles',
    category: 'monument',
    icon: '🏛️'
  },

  {
    id: 'sydney-opera',
    name: 'Sydney Opera House',
    lat: -33.8568,
    lng: 151.2153,
    country: 'Australia',
    description: 'Iconic performing arts center',
    category: 'architecture',
    icon: '🎭'
  },

  {
    id: 'amazon-rainforest',
    name: 'Amazon Rainforest',
    lat: -3.4653,
    lng: -58.3801,
    country: 'Brazil',
    description: 'World\'s largest tropical rainforest ecosystem',
    category: 'natural',
    icon: '🌳'
  },
  {
    id: 'disney-world',
    name: 'Disney World',
    lat: 28.3852,
    lng: -81.5639,
    country: 'USA',
    description: 'The most magical place on Earth - theme park paradise',
    category: 'entertainment',
    icon: '🏰'
  },
  {
    id: 'angkor-wat',
    name: 'Angkor Wat',
    lat: 13.4125,
    lng: 103.8670,
    country: 'Cambodia',
    description: 'Largest religious monument in the world',
    category: 'monument',
    icon: '🕍'
  },

  {
    id: 'mount-fuji',
    name: 'Mount Fuji',
    lat: 35.3606,
    lng: 138.7274,
    country: 'Japan',
    description: 'Sacred mountain and Japan\'s highest peak',
    category: 'natural',
    icon: '🗻'
  },
  {
    id: 'vancouver',
    name: 'Vancouver',
    lat: 49.2827,
    lng: -123.1207,
    country: 'Canada',
    description: 'Beautiful coastal city with stunning mountain views',
    category: 'city',
    icon: '🌲'
  },

  {
    id: 'pyramids',
    name: 'Pyramids of Giza',
    lat: 29.9792,
    lng: 31.1342,
    country: 'Egypt',
    description: 'Ancient wonders of the world',
    category: 'monument',
    icon: '🔺'
  },

  {
    id: 'mount-kilimanjaro',
    name: 'Mount Kilimanjaro',
    lat: -3.0674,
    lng: 37.3556,
    country: 'Tanzania',
    description: 'Africa\'s highest mountain',
    category: 'natural',
    icon: '🏔️'
  },
  {
    id: 'waikiki-beach',
    name: 'Waikiki Beach',
    lat: 21.2790,
    lng: -157.8317,
    country: 'USA (Hawaii)',
    description: 'Famous white sand beach with crystal clear waters',
    category: 'natural',
    icon: '🏖️'
  },
  {
    id: 'lake-baikal',
    name: 'Lake Baikal',
    lat: 53.5587,
    lng: 108.1650,
    country: 'Russia',
    description: 'World\'s deepest and oldest freshwater lake',
    category: 'natural',
    icon: '💧'
  },

];

export const getLandmarksByCategory = (category) => {
  return landmarks.filter(landmark => landmark.category === category);
};

export const getLandmarksByCountry = (country) => {
  return landmarks.filter(landmark => landmark.country === country);
};

export const searchLandmarks = (query) => {
  const lowercaseQuery = query.toLowerCase();
  return landmarks.filter(landmark => 
    landmark.name.toLowerCase().includes(lowercaseQuery) ||
    landmark.country.toLowerCase().includes(lowercaseQuery) ||
    landmark.description.toLowerCase().includes(lowercaseQuery)
  );
}; 