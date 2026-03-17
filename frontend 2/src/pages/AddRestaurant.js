import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { restaurantAPI } from '../services/api';

const CUISINES = ['Italian', 'Chinese', 'Mexican', 'Indian', 'Japanese', 'American', 'Thai', 'French', 'Mediterranean', 'Korean', 'Vietnamese', 'Greek', 'Other'];
const PRICES = ['$', '$$', '$$$', '$$$$'];

export default function AddRestaurant() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: '', cuisine_type: '', description: '', address: '', city: '', state: '', zip_code: '',
    country: 'US', phone: '', email: '', website: '', price_range: '', hours_of_operation: '',
    amenities: '', ambiance: '', dietary_options: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) { setError('Restaurant name is required'); return; }
    setLoading(true);
    setError('');
    try {
      const res = await restaurantAPI.create(form);
      navigate(`/restaurant/${res.data.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create restaurant.');
    }
    setLoading(false);
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Add a Restaurant</h1>

      <div className="bg-white rounded-2xl shadow-sm p-8">
        {error && <div className="bg-red-50 text-red-600 px-4 py-3 rounded-lg mb-6 text-sm">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Restaurant Name *</label>
            <input name="name" value={form.name} onChange={handleChange} required className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent" placeholder="e.g., Pasta Paradise" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Cuisine Type</label>
              <select name="cuisine_type" value={form.cuisine_type} onChange={handleChange} className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-yelp-red">
                <option value="">Select cuisine...</option>
                {CUISINES.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Price Range</label>
              <select name="price_range" value={form.price_range} onChange={handleChange} className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-yelp-red">
                <option value="">Select price range...</option>
                {PRICES.map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea name="description" value={form.description} onChange={handleChange} rows={3} className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent" placeholder="Describe the restaurant..." />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Street Address</label>
            <input name="address" value={form.address} onChange={handleChange} className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent" placeholder="123 Main Street" />
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">City</label>
              <input name="city" value={form.city} onChange={handleChange} className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">State</label>
              <input name="state" value={form.state} onChange={handleChange} className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent" placeholder="CA" maxLength={5} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Zip Code</label>
              <input name="zip_code" value={form.zip_code} onChange={handleChange} className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Country</label>
              <input name="country" value={form.country} onChange={handleChange} className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent" />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
              <input name="phone" value={form.phone} onChange={handleChange} className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent" placeholder="(555) 123-4567" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input name="email" type="email" value={form.email} onChange={handleChange} className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent" />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Website</label>
              <input name="website" value={form.website} onChange={handleChange} className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent" placeholder="https://..." />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Ambiance</label>
              <input name="ambiance" value={form.ambiance} onChange={handleChange} className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent" placeholder="Casual, Romantic, etc." />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Hours of Operation</label>
            <input name="hours_of_operation" value={form.hours_of_operation} onChange={handleChange} className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent" placeholder="Mon-Fri: 9am-10pm, Sat-Sun: 10am-11pm" />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Dietary Options</label>
            <input name="dietary_options" value={form.dietary_options} onChange={handleChange} className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent" placeholder="Vegetarian, Vegan, Gluten-Free" />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Amenities</label>
            <input name="amenities" value={form.amenities} onChange={handleChange} className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent" placeholder="WiFi, Parking, Outdoor Seating" />
          </div>

          <button type="submit" disabled={loading} className="w-full bg-yelp-red text-white py-3 rounded-lg font-semibold hover:bg-yelp-dark transition disabled:opacity-50">
            {loading ? 'Creating...' : 'Add Restaurant'}
          </button>
        </form>
      </div>
    </div>
  );
}
