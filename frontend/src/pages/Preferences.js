import React, { useState, useEffect } from 'react';
import { userAPI } from '../services/api';
import { FiSave } from 'react-icons/fi';

const CUISINES = ['Italian', 'Chinese', 'Mexican', 'Indian', 'Japanese', 'American', 'Thai', 'French', 'Mediterranean', 'Korean', 'Vietnamese', 'Greek'];
const DIETARY = ['Vegetarian', 'Vegan', 'Halal', 'Gluten-Free', 'Kosher', 'Dairy-Free', 'Nut-Free'];
const AMBIANCE = ['Casual', 'Fine Dining', 'Family-Friendly', 'Romantic', 'Outdoor Seating', 'Trendy', 'Quiet', 'Lively'];
const PRICES = ['$', '$$', '$$$', '$$$$'];
const SORTS = ['rating', 'distance', 'popularity', 'price'];

export default function Preferences() {
  const [prefs, setPrefs] = useState({
    cuisine_preferences: '',
    price_range: '',
    preferred_locations: '',
    search_radius: '',
    dietary_needs: '',
    ambiance_preferences: '',
    sort_preference: '',
  });
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    userAPI.getPreferences().then((res) => {
      setPrefs({
        cuisine_preferences: res.data.cuisine_preferences || '',
        price_range: res.data.price_range || '',
        preferred_locations: res.data.preferred_locations || '',
        search_radius: res.data.search_radius || '',
        dietary_needs: res.data.dietary_needs || '',
        ambiance_preferences: res.data.ambiance_preferences || '',
        sort_preference: res.data.sort_preference || '',
      });
    }).catch(() => {});
  }, []);

  const toggleItem = (field, item) => {
    const current = prefs[field] ? prefs[field].split(',').map((s) => s.trim()).filter(Boolean) : [];
    const updated = current.includes(item)
      ? current.filter((i) => i !== item)
      : [...current, item];
    setPrefs({ ...prefs, [field]: updated.join(',') });
  };

  const isSelected = (field, item) => {
    const current = prefs[field] ? prefs[field].split(',').map((s) => s.trim()) : [];
    return current.includes(item);
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage('');
    try {
      await userAPI.updatePreferences({
        ...prefs,
        search_radius: prefs.search_radius ? parseInt(prefs.search_radius) : null,
      });
      setMessage('Preferences saved! Your AI assistant will use these for recommendations.');
    } catch {
      setMessage('Failed to save preferences.');
    }
    setSaving(false);
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">AI Assistant Preferences</h1>
      <p className="text-gray-500 mb-8">Set your dining preferences so the AI chatbot can give you personalized recommendations.</p>

      {message && (
        <div className={`px-4 py-3 rounded-lg mb-6 text-sm ${message.includes('saved') ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-600'}`}>
          {message}
        </div>
      )}

      <div className="bg-white rounded-2xl shadow-sm p-8 space-y-8">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Cuisine Preferences</h3>
          <div className="flex flex-wrap gap-2">
            {CUISINES.map((c) => (
              <button key={c} onClick={() => toggleItem('cuisine_preferences', c)} className={`px-4 py-2 rounded-full text-sm font-medium transition ${isSelected('cuisine_preferences', c) ? 'bg-yelp-red text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}>{c}</button>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Price Range</h3>
          <div className="flex gap-3">
            {PRICES.map((p) => (
              <button key={p} onClick={() => setPrefs({ ...prefs, price_range: prefs.price_range === p ? '' : p })} className={`px-6 py-3 rounded-lg text-sm font-bold transition ${prefs.price_range === p ? 'bg-yelp-red text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}>{p}</button>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Dietary Needs</h3>
          <div className="flex flex-wrap gap-2">
            {DIETARY.map((d) => (
              <button key={d} onClick={() => toggleItem('dietary_needs', d)} className={`px-4 py-2 rounded-full text-sm font-medium transition ${isSelected('dietary_needs', d) ? 'bg-green-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}>{d}</button>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Ambiance Preferences</h3>
          <div className="flex flex-wrap gap-2">
            {AMBIANCE.map((a) => (
              <button key={a} onClick={() => toggleItem('ambiance_preferences', a)} className={`px-4 py-2 rounded-full text-sm font-medium transition ${isSelected('ambiance_preferences', a) ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}>{a}</button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Preferred Location(s)</h3>
            <input
              value={prefs.preferred_locations}
              onChange={(e) => setPrefs({ ...prefs, preferred_locations: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-yelp-red"
              placeholder="San Francisco, San Jose"
            />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Search Radius (miles)</h3>
            <input
              type="number"
              value={prefs.search_radius}
              onChange={(e) => setPrefs({ ...prefs, search_radius: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-yelp-red"
              placeholder="10"
            />
          </div>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Sort Preference</h3>
          <div className="flex gap-3">
            {SORTS.map((s) => (
              <button key={s} onClick={() => setPrefs({ ...prefs, sort_preference: prefs.sort_preference === s ? '' : s })} className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition ${prefs.sort_preference === s ? 'bg-yelp-red text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}>{s}</button>
            ))}
          </div>
        </div>

        <button onClick={handleSave} disabled={saving} className="flex items-center space-x-2 bg-yelp-red text-white px-6 py-3 rounded-lg font-semibold hover:bg-yelp-dark transition disabled:opacity-50">
          <FiSave size={16} /><span>{saving ? 'Saving...' : 'Save Preferences'}</span>
        </button>
      </div>
    </div>
  );
}
