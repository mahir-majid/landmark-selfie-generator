// Utility functions for generating prompts in the selfie page

// Fit options configuration
export const fitOptions = [
  { id: 'casual', label: 'Casual', icon: 'Shirt', color: 'from-blue-500 to-cyan-500' },
  { id: 'formal', label: 'Formal', icon: 'Briefcase', color: 'from-gray-600 to-slate-700' }
];

// Color and clothing options
const colors = ['red', 'blue', 'green', 'purple', 'orange', 'yellow', 'pink', 'teal', 'navy', 'maroon', 'coral', 'lavender', 'mint', 'rose', 'gold', 'silver', 'turquoise', 'violet', 'amber', 'emerald'];
const casualPants = ['blue jeans', 'black jeans', 'brown khakis', 'white sweatpants', 'gray sweatpants', 'navy chinos', 'olive cargo pants', 'beige linen pants', 'dark wash jeans', 'light wash jeans'];
const formalColors = ['black', 'gray', 'silver', 'navy', 'charcoal', 'dark blue', 'burgundy', 'dark green'];

// Store last clothing descriptions
let lastMainClothing = {
  casual: 'with a white t-shirt, blue jeans',
  formal: 'with a black suit, black pants'
};

/**
 * Generate clothing description based on selected fit
 * @param {string} fit - The selected fit type ('casual', 'formal')
 * @param {boolean} forceNewClothes - Whether to force new random clothes
 * @returns {string} - The generated clothing description
 */
export const generateClothingDescription = (fit, forceNewClothes = false) => {
  // If not forcing new clothes, use the last stored clothing for this fit
  if (!forceNewClothes) {
    return lastMainClothing[fit] || lastMainClothing.casual;
  }
  
  // Generate new random clothes and store them
  let newClothing;
  switch (fit) {
    case 'casual':
      const randomColor = colors[Math.floor(Math.random() * colors.length)];
      const randomPants = casualPants[Math.floor(Math.random() * casualPants.length)];
      const casualShirts = ['t-shirt', 'polo shirt', 'henley shirt', 'v-neck shirt', 'crew neck shirt', 'long sleeve shirt'];
      const randomShirt = casualShirts[Math.floor(Math.random() * casualShirts.length)];
      newClothing = `with a ${randomColor} ${randomShirt}, ${randomPants}`;
      break;
    
    case 'formal':
      const formalColor = formalColors[Math.floor(Math.random() * formalColors.length)];
      newClothing = `with a ${formalColor} suit, ${formalColor} pants`;
      break;
    
    default:
      newClothing = 'with a white shirt, blue jeans';
  }
  
  // Store the new clothing for future use
  lastMainClothing[fit] = newClothing;
  return newClothing;
};

/**
 * Generate the complete prompt for image generation
 * @param {string} fit - The selected fit type
 * @param {string} locationName - The location name
 * @param {boolean} isDayTime - Whether it's day or night
 * @param {boolean} forceNewClothes - Whether to force new random clothes
 * @returns {string} - The complete generated prompt
 */
export const generateCompletePrompt = (fit, locationName, isDayTime = true, forceNewClothes = false) => {
  const clothing = generateClothingDescription(fit, forceNewClothes);
  const timeOfDay = isDayTime ? 'sunny afternoon' : 'starry night';
  
  return `High-resolution focused shot of a young attractive person with a smile, ${clothing}, standing by the ${locationName} on a ${timeOfDay}`;
};

/**
 * Regenerate clothing description and update prompt
 * @param {string} fit - The selected fit type
 * @param {string} locationName - The location name
 * @param {Function} setPrompt - Function to update the prompt state
 * @param {boolean} isDayTime - Whether it's day or night
 */
export const regenerateStyle = (fit, locationName, setPrompt, isDayTime = true) => {
  const newPrompt = generateCompletePrompt(
    fit,
    locationName,
    isDayTime,
    true // forceNewClothes = true
  );
  setPrompt(newPrompt);
};
