import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { reviewAPI } from '../services/api';
import { API_BASE } from '../services/api';
import { StarDisplay } from './StarRating';
import { FiThumbsUp } from 'react-icons/fi';

function formatTimeAgo(dateStr) {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  if (diffMins < 60) return `${diffMins} minutes ago`;
  if (diffHours < 24) return `${diffHours} hours ago`;
  return date.toLocaleDateString();
}

export default function RecentActivity() {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    reviewAPI.getRecent(6)
      .then((res) => setReviews(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <section className="py-12 bg-gray-50">
        <h2 className="text-2xl font-bold text-center text-gray-900 mb-8">Recent Activity</h2>
        <div className="max-w-6xl mx-auto px-4 grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="bg-white rounded-lg border border-gray-200 p-4 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-3" />
              <div className="h-32 bg-gray-200 rounded" />
            </div>
          ))}
        </div>
      </section>
    );
  }

  if (reviews.length === 0) {
    return (
      <section className="py-12 bg-gray-50">
        <h2 className="text-2xl font-bold text-center text-gray-900 mb-8">Recent Activity</h2>
        <div className="max-w-6xl mx-auto px-4 text-center py-12 bg-white rounded-lg border border-gray-200">
          <p className="text-gray-500">No recent activity yet. Be the first to write a review!</p>
        </div>
      </section>
    );
  }

  return (
    <section className="py-12 bg-gray-50">
      <h2 className="text-2xl font-bold text-center text-gray-900 mb-8">Recent Activity</h2>
      <div className="max-w-6xl mx-auto px-4 grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {reviews.map((review) => (
          <Link
            key={review.id}
            to={`/restaurant/${review.restaurant_id}`}
            className="bg-white rounded-lg border border-gray-200 overflow-hidden hover:shadow-lg hover:border-gray-300 transition group"
          >
            <div className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-sm font-bold text-gray-600">
                  {review.user_name?.charAt(0) || '?'}
                </div>
                <span className="text-sm text-gray-600">
                  {review.user_name} wrote a review
                </span>
              </div>
              <p className="text-xs text-gray-500 mb-2">{formatTimeAgo(review.created_at)}</p>
              <h3 className="font-semibold text-gray-900 group-hover:text-yelp-red transition">{review.restaurant_name}</h3>
              <div className="flex items-center gap-2 mt-1">
                <StarDisplay rating={review.rating} size={14} showNumber={false} />
              </div>
              {review.comment && (
                <p className="text-sm text-gray-600 mt-2 line-clamp-2">{review.comment}</p>
              )}
            </div>
            <div className="h-32 bg-gradient-to-br from-red-50 to-red-100 flex items-center justify-center">
              <span className="text-4xl font-bold text-yelp-red opacity-30">
                {review.restaurant_name?.charAt(0)}
              </span>
            </div>
            <div className="p-2 border-t border-gray-100">
              <button className="text-gray-400 hover:text-yelp-red p-1">
                <FiThumbsUp size={16} />
              </button>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}
