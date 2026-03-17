/**
 * Placeholder images for restaurants without photos.
 * Uses Unsplash (free to use) - cuisine-based food/restaurant images.
 * Each cuisine has multiple images; we pick one per restaurant using id+name for variety.
 */
const CUISINE_IMAGES = {
  pizza: [
    'https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400&h=300&fit=crop',
    'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400&h=300&fit=crop',
    'https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=400&h=300&fit=crop',
  ],
  italian: [
    'https://images.unsplash.com/photo-1551183053-bf91a1d81141?w=400&h=300&fit=crop',
    'https://images.unsplash.com/photo-1473093295043-cdd812d0e601?w=400&h=300&fit=crop',
    'https://images.unsplash.com/photo-1563379926898-05f4575a45d8?w=400&h=300&fit=crop',
  ],
  mexican: [
    'https://images.unsplash.com/photo-1565299585323-38d6b0865b47?w=400&h=300&fit=crop',
    'https://images.unsplash.com/photo-1551504734-5ee1c4a1479b?w=400&h=300&fit=crop',
    'https://images.unsplash.com/photo-1599970605070-0e1d0c7c8e2?w=400&h=300&fit=crop',
  ],
  chinese: [
    'https://images.unsplash.com/photo-1525755662778-989d0524087e?w=400&h=300&fit=crop',
    'https://images.unsplash.com/photo-1563245372-f21724e3856d?w=400&h=300&fit=crop',
    'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400&h=300&fit=crop',
  ],
  japanese: [
    'https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=400&h=300&fit=crop',
    'https://images.unsplash.com/photo-1569718212165-3a244159147e?w=400&h=300&fit=crop',
    'https://images.unsplash.com/photo-1557872943-16a5ac26437e?w=400&h=300&fit=crop',
  ],
  sushi: [
    'https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=400&h=300&fit=crop',
    'https://images.unsplash.com/photo-1569718212165-3a244159147e?w=400&h=300&fit=crop',
  ],
  ramen: [
    'https://images.unsplash.com/photo-1569718212165-3a244159147e?w=400&h=300&fit=crop',
    'https://images.unsplash.com/photo-1557872943-16a5ac26437e?w=400&h=300&fit=crop',
  ],
  indian: [
    'https://images.unsplash.com/photo-1565557623262-b51c2513a641?w=400&h=300&fit=crop',
    'https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=400&h=300&fit=crop',
  ],
  thai: [
    'https://images.unsplash.com/photo-1552566626-52f8b828add9?w=400&h=300&fit=crop',
    'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400&h=300&fit=crop',
  ],
  american: [
    'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop',
    'https://images.unsplash.com/photo-1550547660-d9450f859349?w=400&h=300&fit=crop',
  ],
  burger: [
    'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400&h=300&fit=crop',
    'https://images.unsplash.com/photo-1550547660-d9450f859349?w=400&h=300&fit=crop',
  ],
  korean: [
    'https://images.unsplash.com/photo-1512058564366-18510be2db19?w=400&h=300&fit=crop',
    'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400&h=300&fit=crop',
  ],
  vietnamese: [
    'https://images.unsplash.com/photo-1582878826629-29b7ad4fb111?w=400&h=300&fit=crop',
    'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400&h=300&fit=crop',
  ],
  mediterranean: [
    'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop',
    'https://images.unsplash.com/photo-1473093295043-cdd812d0e601?w=400&h=300&fit=crop',
  ],
  french: [
    'https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=400&h=300&fit=crop',
    'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400&h=300&fit=crop',
  ],
  greek: [
    'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop',
    'https://images.unsplash.com/photo-1473093295043-cdd812d0e601?w=400&h=300&fit=crop',
  ],
  bakery: [
    'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=400&h=300&fit=crop',
    'https://images.unsplash.com/photo-1555507036-ab1f4038808a?w=400&h=300&fit=crop',
  ],
  coffee: [
    'https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=400&h=300&fit=crop',
    'https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=400&h=300&fit=crop',
  ],
  seafood: [
    'https://images.unsplash.com/photo-1559339352-11d035aa65de?w=400&h=300&fit=crop',
    'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400&h=300&fit=crop',
  ],
  default: [
    'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=400&h=300&fit=crop',
    'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400&h=300&fit=crop',
    'https://images.unsplash.com/photo-1544025162-d76694265947?w=400&h=300&fit=crop',
  ],
};

/** Simple hash for deterministic image selection per restaurant */
function hash(str) {
  let h = 0;
  for (let i = 0; i < (str || '').length; i++) {
    h = (h << 5) - h + str.charCodeAt(i);
    h |= 0;
  }
  return Math.abs(h);
}

export function getRestaurantImageUrl(restaurant) {
  const hasPhoto = restaurant.photos?.[0]?.photo_url;
  if (hasPhoto) return null; // Caller will prepend API_BASE

  const cuisine = (restaurant.cuisine_type || '').toLowerCase();
  let images = CUISINE_IMAGES.default;
  for (const [key, urls] of Object.entries(CUISINE_IMAGES)) {
    if (key !== 'default' && cuisine.includes(key)) {
      images = urls;
      break;
    }
  }
  const idx = hash((restaurant.id || '') + (restaurant.name || '')) % images.length;
  return images[idx];
}
