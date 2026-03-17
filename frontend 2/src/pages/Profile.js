import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { userAPI, API_BASE } from '../services/api';
import { FiCamera, FiSave } from 'react-icons/fi';

const COUNTRIES = [
  'United States', 'Canada', 'United Kingdom', 'Australia', 'India',
  'Germany', 'France', 'Japan', 'China', 'Brazil', 'Mexico', 'South Korea',
  'Italy', 'Spain', 'Netherlands', 'Sweden', 'Singapore', 'Other',
];

export default function Profile() {
  const { user, updateUser } = useAuth();
  const [form, setForm] = useState({
    name: '', email: '', phone: '', about_me: '', city: '', state: '', country: '', languages: '', gender: '',
  });
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (user) {
      setForm({
        name: user.name || '',
        email: user.email || '',
        phone: user.phone || '',
        about_me: user.about_me || '',
        city: user.city || '',
        state: user.state || '',
        country: user.country || '',
        languages: user.languages || '',
        gender: user.gender || '',
      });
    }
  }, [user]);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setMessage('');
    try {
      const res = await userAPI.updateProfile(form);
      updateUser(res.data);
      setMessage('Profile updated successfully!');
    } catch (err) {
      setMessage('Failed to update profile.');
    }
    setSaving(false);
  };

  const handlePhotoUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      const res = await userAPI.uploadPhoto(file);
      updateUser(res.data);
      setMessage('Profile photo updated!');
    } catch {
      setMessage('Failed to upload photo.');
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Your Profile</h1>

      <div className="bg-white rounded-2xl shadow-sm p-8">
        <div className="flex items-center space-x-6 mb-8">
          <div className="relative">
            <div className="w-24 h-24 rounded-full bg-gray-200 overflow-hidden flex items-center justify-center">
              {user?.profile_picture ? (
                <img src={`${API_BASE}${user.profile_picture}`} alt="Profile" className="w-full h-full object-cover" />
              ) : (
                <span className="text-3xl font-bold text-gray-400">{user?.name?.charAt(0)?.toUpperCase()}</span>
              )}
            </div>
            <label className="absolute bottom-0 right-0 bg-yelp-red text-white p-2 rounded-full cursor-pointer hover:bg-yelp-dark transition">
              <FiCamera size={14} />
              <input type="file" accept="image/*" onChange={handlePhotoUpload} className="hidden" />
            </label>
          </div>
          <div>
            <h2 className="text-xl font-semibold text-gray-900">{user?.name}</h2>
            <p className="text-gray-500">{user?.email}</p>
            <p className="text-sm text-gray-400 capitalize">Role: {user?.role}</p>
          </div>
        </div>

        {message && (
          <div className={`px-4 py-3 rounded-lg mb-6 text-sm ${message.includes('success') || message.includes('updated') ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-600'}`}>
            {message}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
              <input name="name" value={form.name} onChange={handleChange} className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input name="email" type="email" value={form.email} onChange={handleChange} className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
              <input name="phone" value={form.phone} onChange={handleChange} className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent" placeholder="(555) 123-4567" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Gender</label>
              <select name="gender" value={form.gender} onChange={handleChange} className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-yelp-red">
                <option value="">Select...</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
                <option value="prefer_not_to_say">Prefer not to say</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">City</label>
              <input name="city" value={form.city} onChange={handleChange} className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">State (Abbreviated)</label>
              <input name="state" value={form.state} onChange={handleChange} className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent" placeholder="CA" maxLength={5} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Country</label>
              <select name="country" value={form.country} onChange={handleChange} className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-yelp-red">
                <option value="">Select...</option>
                {COUNTRIES.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Languages</label>
              <input name="languages" value={form.languages} onChange={handleChange} className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent" placeholder="English, Spanish" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">About Me</label>
            <textarea name="about_me" value={form.about_me} onChange={handleChange} rows={3} className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent" placeholder="Tell us about yourself..." />
          </div>
          <button type="submit" disabled={saving} className="flex items-center space-x-2 bg-yelp-red text-white px-6 py-2.5 rounded-lg font-semibold hover:bg-yelp-dark transition disabled:opacity-50">
            <FiSave size={16} /><span>{saving ? 'Saving...' : 'Save Changes'}</span>
          </button>
        </form>
      </div>
    </div>
  );
}
