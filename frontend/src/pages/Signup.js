import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { authAPI } from '../services/api';

export default function Signup() {
  const [form, setForm] = useState({ name: '', email: '', password: '', confirmPassword: '', role: 'user', restaurant_location: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (form.password !== form.confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    if (form.password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }
    setLoading(true);
    try {
      const payload = { name: form.name, email: form.email, password: form.password, role: form.role };
      if (form.role === 'owner') payload.restaurant_location = form.restaurant_location;
      const res = await authAPI.signup(payload);
      login(res.data.access_token, res.data.user);
      navigate('/');
    } catch (err) {
      const detail = err.response?.data?.detail;
      let msg = 'Signup failed. Please try again.';
      if (typeof detail === 'string') {
        msg = detail;
      } else if (Array.isArray(detail) && detail.length > 0) {
        msg = detail.map((d) => d.msg || JSON.stringify(d)).join('. ');
      } else if (err.message === 'Network Error') {
        msg = 'Cannot reach server. Is the backend running on http://localhost:8000?';
      }
      setError(msg);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-lg p-8">
          <h1 className="text-3xl font-bold text-center text-gray-900 mb-2">Sign Up for Yelp</h1>
          <p className="text-center text-gray-500 mb-8">Join the community and discover great restaurants.</p>

          {error && (
            <div className="bg-red-50 text-red-600 px-4 py-3 rounded-lg mb-4 text-sm">{error}</div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
              <input
                name="name"
                value={form.name}
                onChange={handleChange}
                required
                className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent"
                placeholder="John Doe"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                name="email"
                value={form.email}
                onChange={handleChange}
                required
                className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent"
                placeholder="you@example.com"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <input
                type="password"
                name="password"
                value={form.password}
                onChange={handleChange}
                required
                className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent"
                placeholder="Min 6 characters"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Confirm Password</label>
              <input
                type="password"
                name="confirmPassword"
                value={form.confirmPassword}
                onChange={handleChange}
                required
                className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent"
                placeholder="Re-enter password"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">I am a...</label>
              <select
                name="role"
                value={form.role}
                onChange={handleChange}
                className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-yelp-red"
              >
                <option value="user">Restaurant Reviewer / User</option>
                <option value="owner">Restaurant Owner</option>
              </select>
            </div>
            {form.role === 'owner' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Restaurant Location</label>
                <input
                  name="restaurant_location"
                  value={form.restaurant_location}
                  onChange={handleChange}
                  className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-yelp-red focus:border-transparent"
                  placeholder="City, State"
                />
              </div>
            )}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-yelp-red text-white py-3 rounded-lg font-semibold hover:bg-yelp-dark transition disabled:opacity-50"
            >
              {loading ? 'Creating account...' : 'Sign Up'}
            </button>
          </form>

          <p className="text-center text-sm text-gray-500 mt-6">
            Already on Yelp?{' '}
            <Link to="/login" className="text-yelp-red font-medium hover:underline">Log In</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
