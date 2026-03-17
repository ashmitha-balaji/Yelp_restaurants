import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { historyAPI, reviewAPI } from '../services/api';
import { StarDisplay } from '../components/StarRating';
import { FiStar, FiEdit2, FiTrash2, FiCoffee } from 'react-icons/fi';

export default function History() {
  const [data, setData] = useState({ reviews: [], restaurants: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    historyAPI.get()
      .then((res) => setData(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleDeleteReview = async (id) => {
    if (!window.confirm('Delete this review?')) return;
    try {
      await reviewAPI.delete(id);
      setData((prev) => ({
        ...prev,
        reviews: prev.reviews.filter((r) => r.id !== id),
      }));
    } catch {}
  };

  if (loading) {
    return <div className="flex justify-center py-20"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yelp-red" /></div>;
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="flex items-center space-x-3 mb-8">
        <FiStar className="text-yelp-red" size={28} />
        <h1 className="text-3xl font-bold text-gray-900">My History</h1>
      </div>

      <div className="space-y-8">
        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">My Reviews ({data.reviews?.length || 0})</h2>
          {data.reviews?.length > 0 ? (
            <div className="space-y-4">
              {data.reviews.map((r) => (
                <div key={r.id} className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
                  <div className="flex justify-between items-start">
                    <div>
                      <Link to={`/restaurant/${r.restaurant_id}`} className="text-lg font-semibold text-yelp-red hover:underline">
                        {r.restaurant_name}
                      </Link>
                      <div className="flex items-center space-x-2 mt-1 mb-2">
                        <StarDisplay rating={r.rating} size={14} showNumber={false} />
                        <span className="text-xs text-gray-500">{r.created_at ? new Date(r.created_at).toLocaleDateString() : ''}</span>
                      </div>
                    </div>
                    <div className="flex space-x-2">
                      <Link to={`/write-review/${r.restaurant_id}?edit=${r.id}`} className="text-gray-400 hover:text-yelp-red p-1">
                        <FiEdit2 size={16} />
                      </Link>
                      <button onClick={() => handleDeleteReview(r.id)} className="text-gray-400 hover:text-red-600 p-1">
                        <FiTrash2 size={16} />
                      </button>
                    </div>
                  </div>
                  {r.comment && <p className="text-gray-700 leading-relaxed">{r.comment}</p>}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 py-4">No reviews yet. Visit a restaurant and share your experience!</p>
          )}
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Restaurants I've Added ({data.restaurants?.length || 0})</h2>
          {data.restaurants?.length > 0 ? (
            <div className="space-y-4">
              {data.restaurants.map((r) => (
                <Link
                  key={r.id}
                  to={`/restaurant/${r.id}`}
                  className="block bg-white rounded-xl shadow-sm p-6 border border-gray-100 hover:border-yelp-red transition"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
                      <FiCoffee className="text-yelp-red" size={24} />
                    </div>
                    <div>
                      <span className="font-semibold text-gray-900">{r.name}</span>
                      <div className="text-sm text-gray-500">
                        {r.cuisine_type}{r.city ? ` · ${r.city}` : ''}
                        {r.average_rating ? ` · ★ ${r.average_rating}` : ''}
                      </div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 py-4">No restaurants added yet. Add one from the home page!</p>
          )}
        </section>
      </div>
    </div>
  );
}
