import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { reviewAPI } from '../services/api';
import { StarDisplay } from '../components/StarRating';
import { FiEdit2, FiTrash2, FiStar } from 'react-icons/fi';

export default function MyReviews() {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    reviewAPI.getMyReviews()
      .then((res) => setReviews(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this review?')) return;
    try {
      await reviewAPI.delete(id);
      setReviews(reviews.filter((r) => r.id !== id));
    } catch {}
  };

  if (loading) {
    return <div className="flex justify-center py-20"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yelp-red" /></div>;
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="flex items-center space-x-3 mb-8">
        <FiStar className="text-yelp-red" size={28} />
        <h1 className="text-3xl font-bold text-gray-900">My Reviews</h1>
      </div>

      {reviews.length > 0 ? (
        <div className="space-y-4">
          {reviews.map((review) => (
            <div key={review.id} className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
              <div className="flex justify-between items-start">
                <div>
                  <Link to={`/restaurant/${review.restaurant_id}`} className="text-lg font-semibold text-yelp-red hover:underline">
                    {review.restaurant_name || `Restaurant #${review.restaurant_id}`}
                  </Link>
                  <div className="flex items-center space-x-2 mt-1 mb-2">
                    <StarDisplay rating={review.rating} size={14} showNumber={false} />
                    <span className="text-xs text-gray-500">{new Date(review.created_at).toLocaleDateString()}</span>
                    {review.updated_at && (
                      <span className="text-xs text-gray-400">(edited)</span>
                    )}
                  </div>
                </div>
                <div className="flex space-x-2">
                  <Link to={`/write-review/${review.restaurant_id}?edit=${review.id}`} className="text-gray-400 hover:text-yelp-red p-1">
                    <FiEdit2 size={16} />
                  </Link>
                  <button onClick={() => handleDelete(review.id)} className="text-gray-400 hover:text-red-600 p-1">
                    <FiTrash2 size={16} />
                  </button>
                </div>
              </div>
              {review.comment && <p className="text-gray-700 leading-relaxed">{review.comment}</p>}
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-20 bg-white rounded-2xl shadow-sm">
          <FiStar size={48} className="mx-auto text-gray-300 mb-4" />
          <h3 className="text-xl font-semibold text-gray-700 mb-2">No reviews yet</h3>
          <p className="text-gray-500">Visit a restaurant and share your experience!</p>
        </div>
      )}
    </div>
  );
}
