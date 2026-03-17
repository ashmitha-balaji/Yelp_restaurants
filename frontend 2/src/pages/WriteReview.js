import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { reviewAPI, restaurantAPI } from '../services/api';
import { StarInput } from '../components/StarRating';

export default function WriteReview() {
  const { restaurantId } = useParams();
  const [searchParams] = useSearchParams();
  const editId = searchParams.get('edit');
  const navigate = useNavigate();

  const [restaurant, setRestaurant] = useState(null);
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    restaurantAPI.getById(restaurantId).then((res) => setRestaurant(res.data)).catch(() => {});

    if (editId) {
      reviewAPI.getForRestaurant(restaurantId).then((res) => {
        const review = res.data.find((r) => r.id === parseInt(editId));
        if (review) {
          setRating(review.rating);
          setComment(review.comment || '');
        }
      }).catch(() => {});
    }
  }, [restaurantId, editId]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (rating === 0) { setError('Please select a rating'); return; }
    setLoading(true);
    setError('');
    try {
      if (editId) {
        await reviewAPI.update(editId, { rating, comment });
      } else {
        await reviewAPI.create({ restaurant_id: parseInt(restaurantId), rating, comment });
      }
      navigate(`/restaurant/${restaurantId}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit review.');
    }
    setLoading(false);
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">
        {editId ? 'Edit Your Review' : 'Write a Review'}
      </h1>
      {restaurant && (
        <p className="text-gray-500 mb-8">for <span className="font-medium text-gray-700">{restaurant.name}</span></p>
      )}

      <div className="bg-white rounded-2xl shadow-sm p-8">
        {error && <div className="bg-red-50 text-red-600 px-4 py-3 rounded-lg mb-6 text-sm">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Your Rating *</label>
            <StarInput rating={rating} onChange={setRating} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Your Review</label>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              rows={5}
              className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent"
              placeholder="Share your experience... What did you love? What could be better?"
            />
          </div>
          <div className="flex space-x-4">
            <button type="submit" disabled={loading} className="flex-1 bg-yelp-red text-white py-3 rounded-lg font-semibold hover:bg-yelp-dark transition disabled:opacity-50">
              {loading ? 'Submitting...' : editId ? 'Update Review' : 'Post Review'}
            </button>
            <button type="button" onClick={() => navigate(-1)} className="px-6 py-3 border border-gray-300 rounded-lg font-medium text-gray-600 hover:bg-gray-50 transition">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
