import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { restaurantAPI, reviewAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { StarDisplay } from '../components/StarRating';
import {
  FiGrid, FiStar, FiEye, FiMessageSquare, FiPlusCircle,
  FiEdit2, FiSave, FiX, FiTrendingUp, FiCalendar, FiMapPin,
  FiPhone, FiGlobe, FiClock, FiDollarSign,
} from 'react-icons/fi';

function EditRestaurantModal({ restaurant, onClose, onSave }) {
  const [form, setForm] = useState({
    name: restaurant.name || '',
    cuisine_type: restaurant.cuisine_type || '',
    description: restaurant.description || '',
    address: restaurant.address || '',
    city: restaurant.city || '',
    state: restaurant.state || '',
    zip_code: restaurant.zip_code || '',
    phone: restaurant.phone || '',
    email: restaurant.email || '',
    website: restaurant.website || '',
    price_range: restaurant.price_range || '',
    hours_of_operation: restaurant.hours_of_operation || '',
    amenities: restaurant.amenities || '',
    ambiance: restaurant.ambiance || '',
    dietary_options: restaurant.dietary_options || '',
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      const res = await restaurantAPI.update(restaurant.id, form);
      onSave(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update restaurant.');
    }
    setSaving(false);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-100">
          <h2 className="text-xl font-bold text-gray-900">Edit Restaurant</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 p-1">
            <FiX size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && <div className="bg-red-50 text-red-600 px-4 py-3 rounded-lg text-sm">{error}</div>}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Restaurant Name</label>
              <input name="name" value={form.name} onChange={handleChange} required
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Cuisine Type</label>
              <input name="cuisine_type" value={form.cuisine_type} onChange={handleChange}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent" placeholder="Italian, Chinese, etc." />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
              <input name="phone" value={form.phone} onChange={handleChange}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input name="email" type="email" value={form.email} onChange={handleChange}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Website</label>
              <input name="website" value={form.website} onChange={handleChange}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent" placeholder="https://..." />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Price Range</label>
              <select name="price_range" value={form.price_range} onChange={handleChange}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-yelp-red">
                <option value="">Select...</option>
                <option value="$">$ - Budget</option>
                <option value="$$">$$ - Moderate</option>
                <option value="$$$">$$$ - Upscale</option>
                <option value="$$$$">$$$$ - Fine Dining</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Address</label>
            <input name="address" value={form.address} onChange={handleChange}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent" />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">City</label>
              <input name="city" value={form.city} onChange={handleChange}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">State</label>
              <input name="state" value={form.state} onChange={handleChange} maxLength={5}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent" placeholder="CA" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Zip Code</label>
              <input name="zip_code" value={form.zip_code} onChange={handleChange}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent" />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea name="description" value={form.description} onChange={handleChange} rows={3}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Hours of Operation</label>
              <input name="hours_of_operation" value={form.hours_of_operation} onChange={handleChange}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent" placeholder="Mon-Fri 9am-10pm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Ambiance</label>
              <input name="ambiance" value={form.ambiance} onChange={handleChange}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent" placeholder="Casual, Romantic, etc." />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Amenities</label>
              <input name="amenities" value={form.amenities} onChange={handleChange}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent" placeholder="WiFi, Parking, etc." />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Dietary Options</label>
              <input name="dietary_options" value={form.dietary_options} onChange={handleChange}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent" placeholder="Vegetarian, Vegan, Gluten-free" />
            </div>
          </div>

          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-100">
            <button type="button" onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50 transition">
              Cancel
            </button>
            <button type="submit" disabled={saving}
              className="flex items-center space-x-2 bg-yelp-red text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-yelp-dark transition disabled:opacity-50">
              <FiSave size={14} /><span>{saving ? 'Saving...' : 'Save Changes'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function OwnerDashboard() {
  const { user } = useAuth();
  const [restaurants, setRestaurants] = useState([]);
  const [selectedRestaurant, setSelectedRestaurant] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingRestaurant, setEditingRestaurant] = useState(null);

  useEffect(() => {
    restaurantAPI.getOwnerRestaurants()
      .then((res) => {
        setRestaurants(res.data);
        if (res.data.length > 0) setSelectedRestaurant(res.data[0]);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const fetchReviews = useCallback(() => {
    if (selectedRestaurant) {
      reviewAPI.getForRestaurant(selectedRestaurant.id)
        .then((res) => setReviews(res.data))
        .catch(() => {});
    }
  }, [selectedRestaurant]);

  useEffect(() => { fetchReviews(); }, [fetchReviews]);

  const totalReviews = restaurants.reduce((sum, r) => sum + (r.review_count || 0), 0);
  const avgRating = restaurants.length > 0
    ? (restaurants.reduce((sum, r) => sum + (r.average_rating || 0), 0) / restaurants.length).toFixed(1)
    : '0.0';

  const ratingDistribution = [5, 4, 3, 2, 1].map((star) => ({
    star,
    count: reviews.filter((r) => r.rating === star).length,
  }));
  const maxRatingCount = Math.max(...ratingDistribution.map((d) => d.count), 1);

  const recentReviews = [...reviews].sort((a, b) => new Date(b.created_at) - new Date(a.created_at)).slice(0, 10);

  const avgReviewLength = reviews.length > 0
    ? Math.round(reviews.reduce((sum, r) => sum + (r.comment?.length || 0), 0) / reviews.length)
    : 0;

  const handleSaveRestaurant = (updated) => {
    setRestaurants((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
    if (selectedRestaurant?.id === updated.id) setSelectedRestaurant(updated);
    setEditingRestaurant(null);
  };

  if (loading) {
    return <div className="flex justify-center py-20"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yelp-red" /></div>;
  }

  if (user?.role !== 'owner') {
    return (
      <div className="text-center py-20">
        <h2 className="text-xl font-semibold text-gray-700">Owner Dashboard</h2>
        <p className="text-gray-500 mt-2">This page is only available for restaurant owners.</p>
        <Link to="/" className="inline-block mt-4 text-yelp-red hover:underline">Go to Home</Link>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {editingRestaurant && (
        <EditRestaurantModal
          restaurant={editingRestaurant}
          onClose={() => setEditingRestaurant(null)}
          onSave={handleSaveRestaurant}
        />
      )}

      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center space-x-3">
          <FiGrid className="text-yelp-red" size={28} />
          <h1 className="text-3xl font-bold text-gray-900">Owner Dashboard</h1>
        </div>
        <Link to="/add-restaurant" className="flex items-center space-x-2 bg-yelp-red text-white px-4 py-2 rounded-lg hover:bg-yelp-dark transition text-sm font-medium">
          <FiPlusCircle size={16} /><span>Add Restaurant</span>
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-xl shadow-sm p-5 border border-gray-100">
          <div className="flex items-center space-x-3">
            <div className="bg-blue-50 p-3 rounded-lg"><FiEye className="text-blue-600" size={22} /></div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide">Restaurants</p>
              <p className="text-2xl font-bold text-gray-900">{restaurants.length}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm p-5 border border-gray-100">
          <div className="flex items-center space-x-3">
            <div className="bg-yellow-50 p-3 rounded-lg"><FiStar className="text-yellow-600" size={22} /></div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide">Avg Rating</p>
              <p className="text-2xl font-bold text-gray-900">{avgRating}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm p-5 border border-gray-100">
          <div className="flex items-center space-x-3">
            <div className="bg-green-50 p-3 rounded-lg"><FiMessageSquare className="text-green-600" size={22} /></div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide">Total Reviews</p>
              <p className="text-2xl font-bold text-gray-900">{totalReviews}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm p-5 border border-gray-100">
          <div className="flex items-center space-x-3">
            <div className="bg-purple-50 p-3 rounded-lg"><FiTrendingUp className="text-purple-600" size={22} /></div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide">Avg Review Length</p>
              <p className="text-2xl font-bold text-gray-900">{avgReviewLength}<span className="text-sm font-normal text-gray-400"> chars</span></p>
            </div>
          </div>
        </div>
      </div>

      {restaurants.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: My Restaurants */}
          <div className="lg:col-span-1 space-y-4">
            <h2 className="text-lg font-semibold text-gray-900">My Restaurants</h2>
            <div className="space-y-3">
              {restaurants.map((r) => (
                <div
                  key={r.id}
                  className={`p-4 rounded-xl transition border cursor-pointer ${
                    selectedRestaurant?.id === r.id
                      ? 'bg-red-50 border-yelp-red'
                      : 'bg-white border-gray-100 hover:border-gray-300'
                  }`}
                  onClick={() => setSelectedRestaurant(r)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-gray-900 truncate">{r.name}</h3>
                      <div className="flex items-center space-x-2 mt-1">
                        <StarDisplay rating={r.average_rating || 0} size={12} />
                        <span className="text-xs text-gray-500">({r.review_count || 0})</span>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">{r.cuisine_type} {r.price_range && `\u2022 ${r.price_range}`}</p>
                      {r.city && (
                        <p className="text-xs text-gray-400 mt-0.5 flex items-center gap-1">
                          <FiMapPin size={10} />{r.city}{r.state ? `, ${r.state}` : ''}
                        </p>
                      )}
                    </div>
                    <button
                      onClick={(e) => { e.stopPropagation(); setEditingRestaurant(r); }}
                      className="text-gray-400 hover:text-yelp-red p-1 ml-2 flex-shrink-0"
                      title="Edit restaurant"
                    >
                      <FiEdit2 size={16} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right: Selected Restaurant Details */}
          <div className="lg:col-span-2 space-y-6">
            {selectedRestaurant && (
              <>
                {/* Restaurant Profile Card */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                  <div className="bg-gradient-to-r from-red-500 to-red-600 px-6 py-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h2 className="text-xl font-bold text-white">{selectedRestaurant.name}</h2>
                        <p className="text-red-100 text-sm mt-0.5">
                          {selectedRestaurant.cuisine_type}{selectedRestaurant.price_range ? ` \u2022 ${selectedRestaurant.price_range}` : ''}
                        </p>
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => setEditingRestaurant(selectedRestaurant)}
                          className="bg-white bg-opacity-20 hover:bg-opacity-30 text-white px-3 py-1.5 rounded-lg text-sm font-medium transition flex items-center space-x-1"
                        >
                          <FiEdit2 size={14} /><span>Edit Profile</span>
                        </button>
                        <Link to={`/restaurant/${selectedRestaurant.id}`}
                          className="bg-white bg-opacity-20 hover:bg-opacity-30 text-white px-3 py-1.5 rounded-lg text-sm font-medium transition">
                          View Public Page
                        </Link>
                      </div>
                    </div>
                  </div>
                  <div className="p-6">
                    {selectedRestaurant.description && (
                      <p className="text-gray-600 text-sm mb-4">{selectedRestaurant.description}</p>
                    )}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
                      {selectedRestaurant.address && (
                        <div className="flex items-start space-x-2 text-gray-600">
                          <FiMapPin className="mt-0.5 text-gray-400 flex-shrink-0" size={14} />
                          <span>{selectedRestaurant.address}{selectedRestaurant.city ? `, ${selectedRestaurant.city}` : ''}{selectedRestaurant.state ? `, ${selectedRestaurant.state}` : ''} {selectedRestaurant.zip_code || ''}</span>
                        </div>
                      )}
                      {selectedRestaurant.phone && (
                        <div className="flex items-center space-x-2 text-gray-600">
                          <FiPhone className="text-gray-400 flex-shrink-0" size={14} /><span>{selectedRestaurant.phone}</span>
                        </div>
                      )}
                      {selectedRestaurant.website && (
                        <div className="flex items-center space-x-2 text-gray-600">
                          <FiGlobe className="text-gray-400 flex-shrink-0" size={14} />
                          <a href={selectedRestaurant.website} target="_blank" rel="noreferrer" className="text-yelp-red hover:underline truncate">{selectedRestaurant.website}</a>
                        </div>
                      )}
                      {selectedRestaurant.hours_of_operation && (
                        <div className="flex items-center space-x-2 text-gray-600">
                          <FiClock className="text-gray-400 flex-shrink-0" size={14} /><span>{selectedRestaurant.hours_of_operation}</span>
                        </div>
                      )}
                      {selectedRestaurant.email && (
                        <div className="flex items-center space-x-2 text-gray-600">
                          <span className="text-gray-400 flex-shrink-0 text-xs">@</span><span>{selectedRestaurant.email}</span>
                        </div>
                      )}
                      {selectedRestaurant.ambiance && (
                        <div className="flex items-center space-x-2 text-gray-600">
                          <span className="text-gray-400 flex-shrink-0 text-xs">~</span><span>Ambiance: {selectedRestaurant.ambiance}</span>
                        </div>
                      )}
                    </div>
                    {selectedRestaurant.dietary_options && (
                      <div className="mt-3 flex flex-wrap gap-1">
                        {selectedRestaurant.dietary_options.split(',').map((opt) => (
                          <span key={opt} className="bg-green-50 text-green-700 px-2 py-0.5 rounded-full text-xs">{opt.trim()}</span>
                        ))}
                      </div>
                    )}
                    {selectedRestaurant.amenities && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {selectedRestaurant.amenities.split(',').map((a) => (
                          <span key={a} className="bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full text-xs">{a.trim()}</span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Rating Analytics */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="bg-white rounded-xl shadow-sm p-5 border border-gray-100">
                    <h3 className="text-sm font-semibold text-gray-700 mb-3">Rating Distribution</h3>
                    {ratingDistribution.map(({ star, count }) => (
                      <div key={star} className="flex items-center space-x-2 mb-1.5">
                        <span className="text-xs text-gray-600 w-8 font-medium">{star}{'\u2605'}</span>
                        <div className="flex-1 bg-gray-100 rounded-full h-3.5 overflow-hidden">
                          <div
                            className="bg-yellow-400 h-full rounded-full transition-all duration-500"
                            style={{ width: `${(count / maxRatingCount) * 100}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-500 w-6 text-right font-medium">{count}</span>
                      </div>
                    ))}
                  </div>
                  <div className="bg-white rounded-xl shadow-sm p-5 border border-gray-100">
                    <h3 className="text-sm font-semibold text-gray-700 mb-3">Restaurant Stats</h3>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-500">Rating</span>
                        <div className="flex items-center space-x-1">
                          <StarDisplay rating={selectedRestaurant.average_rating || 0} size={14} />
                        </div>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-500">Total Reviews</span>
                        <span className="text-sm font-semibold text-gray-900">{selectedRestaurant.review_count || 0}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-500">Price Range</span>
                        <span className="text-sm font-semibold text-gray-900 flex items-center"><FiDollarSign size={12} />{selectedRestaurant.price_range || 'N/A'}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-500">5-Star %</span>
                        <span className="text-sm font-semibold text-green-600">
                          {reviews.length > 0 ? Math.round((ratingDistribution.find((d) => d.star === 5)?.count / reviews.length) * 100) : 0}%
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-500">Claimed</span>
                        <span className={`text-sm font-semibold ${selectedRestaurant.is_claimed ? 'text-green-600' : 'text-gray-400'}`}>
                          {selectedRestaurant.is_claimed ? 'Yes' : 'No'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Recent Reviews */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center space-x-2">
                    <FiCalendar size={18} className="text-gray-400" />
                    <span>Recent Reviews</span>
                    <span className="text-sm font-normal text-gray-400">({reviews.length} total)</span>
                  </h3>
                  <div className="space-y-3">
                    {recentReviews.length > 0 ? recentReviews.map((review) => (
                      <div key={review.id} className="bg-white rounded-xl shadow-sm p-5 border border-gray-100">
                        <div className="flex items-center space-x-2 mb-2">
                          <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-xs font-bold text-gray-600">
                            {review.user_name?.charAt(0) || '?'}
                          </div>
                          <div className="flex-1 min-w-0">
                            <span className="font-medium text-gray-900 text-sm">{review.user_name}</span>
                            <div className="flex items-center space-x-2">
                              <StarDisplay rating={review.rating} size={12} showNumber={false} />
                              <span className="text-xs text-gray-400">{new Date(review.created_at).toLocaleDateString()}</span>
                            </div>
                          </div>
                        </div>
                        {review.comment && <p className="text-gray-700 text-sm leading-relaxed">{review.comment}</p>}
                      </div>
                    )) : (
                      <div className="bg-white rounded-xl shadow-sm p-8 text-center border border-gray-100">
                        <p className="text-gray-500">No reviews yet for this restaurant.</p>
                      </div>
                    )}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      ) : (
        <div className="text-center py-16 bg-white rounded-2xl shadow-sm">
          <FiGrid size={48} className="mx-auto text-gray-300 mb-4" />
          <h3 className="text-xl font-semibold text-gray-700 mb-2">No restaurants yet</h3>
          <p className="text-gray-500 mb-4">Add your first restaurant to get started!</p>
          <Link to="/add-restaurant" className="inline-block bg-yelp-red text-white px-6 py-2 rounded-lg hover:bg-yelp-dark transition">
            Add Restaurant
          </Link>
        </div>
      )}
    </div>
  );
}
