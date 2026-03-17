import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { restaurantAPI, reviewAPI, favoriteAPI, API_BASE } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { StarDisplay } from '../components/StarRating';
import ReviewForm from '../components/ReviewForm';
import { getRestaurantImageUrl } from '../utils/placeholderImages';
import { FiHeart, FiMapPin, FiPhone, FiGlobe, FiClock, FiEdit2, FiTrash2, FiDollarSign, FiCheckCircle, FiFlag } from 'react-icons/fi';

export default function RestaurantDetails() {
  const { id } = useParams();
  const { user } = useAuth();
  const [restaurant, setRestaurant] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [isFavorite, setIsFavorite] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [editingReviewId, setEditingReviewId] = useState(null);
  const [claiming, setClaiming] = useState(false);
  const [claimMsg, setClaimMsg] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [restRes, revRes] = await Promise.all([
          restaurantAPI.getById(id),
          reviewAPI.getForRestaurant(id),
        ]);
        setRestaurant(restRes.data);
        setReviews(revRes.data);

        if (user) {
          try {
            const favRes = await favoriteAPI.check(id);
            setIsFavorite(favRes.data.is_favorite);
          } catch {}
        }
      } catch (err) {
        console.error('Failed to fetch restaurant:', err);
      }
      setLoading(false);
    };
    fetchData();
  }, [id, user]);

  const toggleFavorite = async () => {
    try {
      if (isFavorite) {
        await favoriteAPI.remove(id);
      } else {
        await favoriteAPI.add(parseInt(id));
      }
      setIsFavorite(!isFavorite);
    } catch (err) {
      console.error('Failed to toggle favorite:', err);
    }
  };

  const handleClaim = async () => {
    setClaiming(true);
    setClaimMsg('');
    try {
      const res = await restaurantAPI.claim(id);
      setRestaurant(res.data);
      setClaimMsg('Restaurant claimed successfully!');
    } catch (err) {
      setClaimMsg(err.response?.data?.detail || 'Failed to claim restaurant.');
    }
    setClaiming(false);
  };

  const handleDeleteReview = async (reviewId) => {
    if (!window.confirm('Delete this review?')) return;
    try {
      await reviewAPI.delete(reviewId);
      setReviews(reviews.filter((r) => r.id !== reviewId));
      const restRes = await restaurantAPI.getById(id);
      setRestaurant(restRes.data);
    } catch (err) {
      console.error('Failed to delete review:', err);
    }
  };

  const handleReviewSubmit = async (rating, comment) => {
    try {
      if (editingReviewId) {
        await reviewAPI.update(editingReviewId, { rating, comment });
        setReviews((prev) =>
          prev.map((r) => (r.id === editingReviewId ? { ...r, rating, comment } : r))
        );
      } else {
        const res = await reviewAPI.create({ restaurant_id: parseInt(id), rating, comment });
        setReviews((prev) => [...prev, res.data]);
      }
      setShowReviewForm(false);
      setEditingReviewId(null);
      const restRes = await restaurantAPI.getById(id);
      setRestaurant(restRes.data);
    } catch (err) {
      throw err;
    }
  };

  const handleEditReview = (review) => {
    setEditingReviewId(review.id);
    setShowReviewForm(true);
  };

  const myReview = reviews.find((r) => r.user_id === user?.id);

  if (loading) {
    return <div className="flex justify-center py-20"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yelp-red" /></div>;
  }

  if (!restaurant) {
    return <div className="text-center py-20 text-gray-500">Restaurant not found.</div>;
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="bg-white rounded-2xl shadow-sm overflow-hidden">
        {(() => {
          const photoUrl = restaurant.photos?.[0]?.photo_url
            ? `${API_BASE}${restaurant.photos[0].photo_url}`
            : getRestaurantImageUrl(restaurant);
          return photoUrl ? (
            <div className="h-64 md:h-80 overflow-hidden">
              <img
                src={photoUrl}
                alt={restaurant.name}
                className="w-full h-full object-cover"
              />
            </div>
          ) : (
            <div className="h-48 bg-gradient-to-br from-red-100 to-red-50 flex items-center justify-center">
              <span className="text-6xl font-bold text-yelp-red opacity-20">{restaurant.name?.charAt(0)}</span>
            </div>
          );
        })()}

        <div className="p-6 md:p-8">
          <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">{restaurant.name}</h1>
              <div className="flex items-center space-x-3 mb-3">
                <StarDisplay rating={restaurant.average_rating || 0} size={20} />
                <span className="text-gray-500">({restaurant.review_count || 0} reviews)</span>
              </div>
              <div className="flex flex-wrap gap-2 mb-4">
                {restaurant.cuisine_type && (
                  <span className="bg-red-50 text-yelp-red px-3 py-1 rounded-full text-sm font-medium">{restaurant.cuisine_type}</span>
                )}
                {restaurant.price_range && (
                  <span className="bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-sm flex items-center">
                    <FiDollarSign size={14} className="mr-0.5" />{restaurant.price_range}
                  </span>
                )}
                {restaurant.ambiance && (
                  <span className="bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-sm">{restaurant.ambiance}</span>
                )}
              </div>
            </div>

            {user && (
              <div className="flex flex-wrap gap-3">
                <button
                  onClick={toggleFavorite}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg border transition ${
                    isFavorite
                      ? 'bg-red-50 border-yelp-red text-yelp-red'
                      : 'border-gray-300 text-gray-600 hover:border-yelp-red hover:text-yelp-red'
                  }`}
                >
                  <FiHeart size={16} className={isFavorite ? 'fill-yelp-red' : ''} />
                  <span className="text-sm font-medium">{isFavorite ? 'Saved' : 'Save'}</span>
                </button>
                <button
                  onClick={() => {
                    setEditingReviewId(null);
                    setShowReviewForm(!showReviewForm);
                  }}
                  className="flex items-center space-x-2 bg-yelp-red text-white px-4 py-2 rounded-lg hover:bg-yelp-dark transition text-sm font-medium"
                >
                  <FiEdit2 size={16} /><span>{myReview ? 'Edit Review' : 'Write Review'}</span>
                </button>
                {user.role === 'owner' && !restaurant.is_claimed && (
                  <button
                    onClick={handleClaim}
                    disabled={claiming}
                    className="flex items-center space-x-2 px-4 py-2 rounded-lg border border-blue-500 text-blue-600 hover:bg-blue-50 transition text-sm font-medium disabled:opacity-50"
                  >
                    <FiFlag size={16} /><span>{claiming ? 'Claiming...' : 'Claim This Restaurant'}</span>
                  </button>
                )}
                {restaurant.is_claimed && restaurant.owner_id === user.id && (
                  <span className="flex items-center space-x-1 px-4 py-2 text-green-600 text-sm font-medium">
                    <FiCheckCircle size={16} /><span>You own this restaurant</span>
                  </span>
                )}
              </div>
            )}
            {claimMsg && (
              <p className={`text-sm mt-2 ${claimMsg.includes('success') ? 'text-green-600' : 'text-red-600'}`}>{claimMsg}</p>
            )}
          </div>

          {restaurant.description && (
            <p className="text-gray-600 mb-6 leading-relaxed">{restaurant.description}</p>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            {restaurant.address && (
              <div className="flex items-start space-x-2 text-gray-600">
                <FiMapPin className="mt-1 flex-shrink-0" />
                <span>{restaurant.address}{restaurant.city ? `, ${restaurant.city}` : ''}{restaurant.state ? `, ${restaurant.state}` : ''} {restaurant.zip_code || ''}</span>
              </div>
            )}
            {restaurant.phone && (
              <div className="flex items-center space-x-2 text-gray-600">
                <FiPhone className="flex-shrink-0" /><span>{restaurant.phone}</span>
              </div>
            )}
            {restaurant.website && (
              <div className="flex items-center space-x-2 text-gray-600">
                <FiGlobe className="flex-shrink-0" />
                <a href={restaurant.website} target="_blank" rel="noreferrer" className="text-yelp-red hover:underline">{restaurant.website}</a>
              </div>
            )}
            {restaurant.hours_of_operation && (
              <div className="flex items-start space-x-2 text-gray-600">
                <FiClock className="mt-1 flex-shrink-0" /><span>{restaurant.hours_of_operation}</span>
              </div>
            )}
          </div>

          {restaurant.dietary_options && (
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Dietary Options</h3>
              <div className="flex flex-wrap gap-2">
                {restaurant.dietary_options.split(',').map((opt) => (
                  <span key={opt} className="bg-green-50 text-green-700 px-2 py-1 rounded-full text-xs">{opt.trim()}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="mt-8">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Reviews ({reviews.length})</h2>
          {user && !showReviewForm && (
            <button
              onClick={() => {
                setEditingReviewId(null);
                setShowReviewForm(true);
              }}
              className="text-sm font-medium text-yelp-red hover:underline"
            >
              {myReview ? 'Edit Review' : 'Write a Review'}
            </button>
          )}
        </div>
        {showReviewForm && (
          <ReviewForm
            initialRating={reviews.find((r) => r.id === editingReviewId)?.rating}
            initialComment={reviews.find((r) => r.id === editingReviewId)?.comment || ''}
            onSubmit={handleReviewSubmit}
            onCancel={() => {
              setShowReviewForm(false);
              setEditingReviewId(null);
            }}
          />
        )}
        {reviews.length > 0 ? (
          <div className="space-y-4">
            {reviews.map((review) => (
              <div key={review.id} className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center space-x-2 mb-1">
                      <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-sm font-bold text-gray-600">
                        {review.user_name?.charAt(0) || '?'}
                      </div>
                      <span className="font-medium text-gray-900">{review.user_name || 'Anonymous'}</span>
                    </div>
                    <div className="flex items-center space-x-2 mb-2">
                      <StarDisplay rating={review.rating} size={14} showNumber={false} />
                      <span className="text-xs text-gray-500">
                        {new Date(review.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                  {user && review.user_id === user.id && (
                    <div className="flex space-x-2">
                      <button onClick={() => handleEditReview(review)} className="text-gray-400 hover:text-yelp-red p-1">
                        <FiEdit2 size={16} />
                      </button>
                      <button onClick={() => handleDeleteReview(review.id)} className="text-gray-400 hover:text-red-600 p-1">
                        <FiTrash2 size={16} />
                      </button>
                    </div>
                  )}
                </div>
                {review.comment && <p className="text-gray-700 leading-relaxed">{review.comment}</p>}
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-xl shadow-sm p-8 text-center">
            <p className="text-gray-500">No reviews yet. Be the first to review!</p>
            {user && !showReviewForm && (
              <button
                onClick={() => setShowReviewForm(true)}
                className="inline-block mt-4 bg-yelp-red text-white px-6 py-2 rounded-lg hover:bg-yelp-dark transition text-sm font-medium"
              >
                Write a Review
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
