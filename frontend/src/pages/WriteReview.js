import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { reviewAPI, restaurantAPI, API_BASE } from '../services/api';
import { StarInput } from '../components/StarRating';
import { getRestaurantImageUrl } from '../utils/placeholderImages';
import { FiSearch, FiMapPin, FiChevronRight } from 'react-icons/fi';

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
  const [query, setQuery] = useState('');
  const [city, setCity] = useState('');
  const [restaurants, setRestaurants] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState('');
  const [restaurantReviews, setRestaurantReviews] = useState([]);

  const toDedupKey = (r) =>
    r?.yelp_id
      ? `yelp:${r.yelp_id}`
      : `local:${(r?.name || '').trim().toLowerCase()}|${(r?.city || '').trim().toLowerCase()}|${(r?.address || '').trim().toLowerCase()}`;

  const mergeRestaurants = (localRestaurants = [], yelpRestaurants = []) => {
    const combined = [...localRestaurants, ...yelpRestaurants];
    const seen = new Set();
    return combined.filter((r) => {
      const key = toDedupKey(r);
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  };

  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: 'auto' });
  }, []);

  useEffect(() => {
    if (!restaurantId) return;
    restaurantAPI.getById(restaurantId).then((res) => setRestaurant(res.data)).catch(() => {});
    reviewAPI.getForRestaurant(restaurantId).then((res) => setRestaurantReviews(res.data || [])).catch(() => {});

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

  useEffect(() => {
    if (restaurantId) return;

    const fetchInitialRestaurants = async () => {
      setSearchLoading(true);
      setSearchError('');
      try {
        const [localRes, yelpRes] = await Promise.allSettled([
          restaurantAPI.search({ limit: 8 }),
          restaurantAPI.searchYelp({ term: 'restaurants', city: 'San Jose, CA', limit: 8 }),
        ]);

        const localRestaurants = localRes.status === 'fulfilled' ? (localRes.value.data || []) : [];
        const yelpRestaurants = yelpRes.status === 'fulfilled'
          ? (yelpRes.value.data.restaurants || yelpRes.value.data || [])
          : [];

        setRestaurants(mergeRestaurants(localRestaurants, yelpRestaurants));
      } catch {
        setSearchError('Failed to load restaurants.');
      }
      setSearchLoading(false);
    };

    fetchInitialRestaurants();
  }, [restaurantId]);

  const handleRestaurantSearch = async (e) => {
    e.preventDefault();
    setSearchLoading(true);
    setSearchError('');
    try {
      const localParams = { limit: 20 };
      if (query.trim()) localParams.keyword = query.trim();
      if (city.trim()) localParams.city = city.trim();

      const yelpParams = {
        term: query.trim() || 'restaurants',
        city: city.trim() || 'San Jose, CA',
        limit: 20,
      };

      const [localRes, yelpRes] = await Promise.allSettled([
        restaurantAPI.search(localParams),
        restaurantAPI.searchYelp(yelpParams),
      ]);

      const localRestaurants = localRes.status === 'fulfilled' ? (localRes.value.data || []) : [];
      const yelpRestaurants = yelpRes.status === 'fulfilled'
        ? (yelpRes.value.data.restaurants || yelpRes.value.data || [])
        : [];

      setRestaurants(mergeRestaurants(localRestaurants, yelpRestaurants));
    } catch {
      setSearchError('Failed to search restaurants.');
    }
    setSearchLoading(false);
  };

  const ensureLocalRestaurantId = async (selectedRestaurant) => {
    if (!selectedRestaurant) return null;
    if (!selectedRestaurant.yelp_id) return selectedRestaurant.id;

    const matchRes = await restaurantAPI.search({
      name: selectedRestaurant.name,
      city: selectedRestaurant.city,
      limit: 10,
    });
    const matches = matchRes.data || [];
    const exact = matches.find(
      (r) =>
        (r.name || '').trim().toLowerCase() === (selectedRestaurant.name || '').trim().toLowerCase() &&
        (r.city || '').trim().toLowerCase() === (selectedRestaurant.city || '').trim().toLowerCase()
    );
    if (exact?.id) return exact.id;

    const createRes = await restaurantAPI.create({
      name: selectedRestaurant.name,
      cuisine_type: selectedRestaurant.cuisine_type,
      description: 'Imported from Yelp for reviews/favorites.',
      address: selectedRestaurant.address,
      city: selectedRestaurant.city,
      state: selectedRestaurant.state,
      zip_code: selectedRestaurant.zip_code,
      country: selectedRestaurant.country || 'US',
      phone: selectedRestaurant.phone,
      price_range: selectedRestaurant.price_range,
    });
    return createRes.data?.id || null;
  };

  const recentReviews = useMemo(
    () => restaurantReviews.filter((r) => !editId || r.id !== parseInt(editId)).slice(0, 6),
    [restaurantReviews, editId]
  );

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

  if (!restaurantId) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-10">
        <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-3">Find a business to review</h1>
        <p className="text-gray-500 mb-8">Search for owner-added restaurants in our community and share your experience.</p>

        <form onSubmit={handleRestaurantSearch} className="bg-white border border-gray-200 rounded-xl p-3 md:p-4 flex flex-col md:flex-row gap-3 md:gap-2 mb-10">
          <div className="flex-1 flex items-center border border-gray-300 rounded-lg overflow-hidden">
            <FiSearch className="text-gray-400 ml-3" size={18} />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Try lunch, sushi, pizza..."
              className="flex-1 px-3 py-2.5 text-sm focus:outline-none"
            />
          </div>
          <div className="md:w-60 flex items-center border border-gray-300 rounded-lg overflow-hidden">
            <FiMapPin className="text-gray-400 ml-3" size={18} />
            <input
              type="text"
              value={city}
              onChange={(e) => setCity(e.target.value)}
              placeholder="San Jose, CA"
              className="flex-1 px-3 py-2.5 text-sm focus:outline-none"
            />
          </div>
          <button
            type="submit"
            className="bg-yelp-red text-white px-6 py-2.5 rounded-lg font-semibold hover:bg-yelp-dark transition"
          >
            Search
          </button>
        </form>

        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Visited one of these places recently?</h2>
          {searchLoading && <span className="text-sm text-gray-500">Loading...</span>}
        </div>
        {searchError && <div className="bg-red-50 text-red-600 px-4 py-3 rounded-lg mb-4 text-sm">{searchError}</div>}

        {restaurants.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {restaurants.map((r) => {
              const photoUrl = r.photos?.[0]?.photo_url
                ? `${API_BASE}${r.photos[0].photo_url}`
                : (r.image_url || getRestaurantImageUrl(r));

              return (
                <button
                  key={r.yelp_id || r.id}
                  type="button"
                  onClick={async () => {
                    try {
                      const localId = await ensureLocalRestaurantId(r);
                      if (localId) navigate(`/write-review/${localId}`);
                    } catch {
                      setSearchError('Could not open this restaurant for review. Please try another one.');
                    }
                  }}
                  className="text-left bg-white border border-gray-200 rounded-xl overflow-hidden hover:border-yelp-red hover:shadow-md transition group"
                >
                  <div className="flex">
                    <div className="w-28 h-28 bg-gray-100 shrink-0 overflow-hidden">
                      {photoUrl || r.image_url ? (
                        <img src={photoUrl} alt={r.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
                      ) : (
                        <div className="w-full h-full bg-gradient-to-br from-red-50 to-red-100 flex items-center justify-center text-yelp-red font-bold text-2xl">
                          {r.name?.charAt(0)}
                        </div>
                      )}
                    </div>
                    <div className="flex-1 p-4 flex items-center justify-between">
                      <div className="min-w-0">
                        <h3 className="font-semibold text-gray-900 truncate">{r.name}</h3>
                        <p className="text-sm text-gray-500 truncate">{r.cuisine_type || 'Restaurant'}{r.city ? ` • ${r.city}` : ''}</p>
                        <p className="text-xs text-gray-400 mt-1">
                          {r.yelp_id ? 'From Yelp • Write your review' : 'Write your review'}
                        </p>
                      </div>
                      <FiChevronRight className="text-gray-400 group-hover:text-yelp-red ml-3" size={20} />
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        ) : !searchLoading ? (
          <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-gray-500">
            No matching restaurants found. Try a different search.
          </div>
        ) : null}
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="bg-white rounded-2xl shadow-sm p-8 border border-gray-100">
            <h1 className="text-3xl font-bold text-gray-900 mb-1">
              {editId ? 'Edit Your Review' : 'Write a Review'}
            </h1>
            {restaurant && (
              <p className="text-gray-500 mb-8">
                for <span className="font-medium text-gray-700">{restaurant.name}</span>
                {restaurant.city ? ` • ${restaurant.city}` : ''}
              </p>
            )}

            {error && <div className="bg-red-50 text-red-600 px-4 py-3 rounded-lg mb-6 text-sm">{error}</div>}

            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">How would you rate your experience?</label>
                <StarInput rating={rating} onChange={setRating} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tell us about your experience</label>
                <textarea
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  rows={8}
                  className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent"
                  placeholder="Share details of your visit..."
                />
              </div>
              <div className="flex flex-wrap gap-3">
                <button type="submit" disabled={loading} className="bg-yelp-red text-white px-6 py-3 rounded-lg font-semibold hover:bg-yelp-dark transition disabled:opacity-50">
                  {loading ? 'Submitting...' : editId ? 'Update Review' : 'Post Review'}
                </button>
                <button type="button" onClick={() => navigate('/write-review')} className="px-6 py-3 border border-gray-300 rounded-lg font-medium text-gray-600 hover:bg-gray-50 transition">
                  Change Restaurant
                </button>
              </div>
            </form>
          </div>
        </div>

        <aside className="lg:col-span-1">
          <div className="bg-white rounded-2xl shadow-sm p-6 border border-gray-100">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent reviews</h2>
            {recentReviews.length > 0 ? (
              <div className="space-y-4">
                {recentReviews.map((review) => (
                  <div key={review.id} className="border-b border-gray-100 pb-3 last:border-b-0 last:pb-0">
                    <p className="text-sm font-medium text-gray-800">{review.user_name || 'Anonymous'}</p>
                    <p className="text-xs text-gray-500 mb-1">{new Date(review.created_at).toLocaleDateString()}</p>
                    <p className="text-sm text-gray-600 line-clamp-3">{review.comment || `${review.rating} star rating`}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500">No reviews yet for this restaurant. Be the first one.</p>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
