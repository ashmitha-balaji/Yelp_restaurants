import React, { useState, useEffect } from 'react';
import { favoriteAPI } from '../services/api';
import RestaurantCard from '../components/RestaurantCard';
import { FiHeart } from 'react-icons/fi';

export default function Favorites() {
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    favoriteAPI.getAll()
      .then((res) => setFavorites(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="flex justify-center py-20"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yelp-red" /></div>;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex items-center space-x-3 mb-8">
        <FiHeart className="text-yelp-red" size={28} />
        <h1 className="text-3xl font-bold text-gray-900">My Favorites</h1>
      </div>

      {favorites.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {favorites.map((fav) => (
            fav.restaurant && <RestaurantCard key={fav.id} restaurant={fav.restaurant} />
          ))}
        </div>
      ) : (
        <div className="text-center py-20 bg-white rounded-2xl shadow-sm">
          <FiHeart size={48} className="mx-auto text-gray-300 mb-4" />
          <h3 className="text-xl font-semibold text-gray-700 mb-2">No favorites yet</h3>
          <p className="text-gray-500">Start exploring restaurants and save your favorites!</p>
        </div>
      )}
    </div>
  );
}
