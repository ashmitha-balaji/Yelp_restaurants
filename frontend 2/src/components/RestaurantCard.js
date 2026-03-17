import React, { useState, memo } from 'react';
import { Link } from 'react-router-dom';
import { StarDisplay } from './StarRating';
import { FiChevronRight } from 'react-icons/fi';
import { API_BASE } from '../services/api';
import { getRestaurantImageUrl } from '../utils/placeholderImages';

function RestaurantCard({ restaurant }) {
  const [imgError, setImgError] = useState(false);
  const photoUrl = restaurant.photos?.[0]?.photo_url
    ? `${API_BASE}${restaurant.photos[0].photo_url}`
    : getRestaurantImageUrl(restaurant);
  const showImage = photoUrl && !imgError;

  return (
    <Link
      to={`/restaurant/${restaurant.id}`}
      className="flex bg-white rounded-lg border border-gray-200 hover:shadow-lg hover:border-gray-300 transition-all overflow-hidden group"
    >
      {/* Photo - lazy load, fallback on error */}
      <div className="w-36 md:w-44 h-36 md:h-44 shrink-0 bg-gray-100 overflow-hidden">
        {showImage ? (
          <img
            src={photoUrl}
            alt={restaurant.name}
            loading="lazy"
            onError={() => setImgError(true)}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-red-50 to-red-100">
            <span className="text-4xl font-bold text-yelp-red opacity-50">
              {restaurant.name?.charAt(0)}
            </span>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 p-4 min-w-0 flex flex-col justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 group-hover:text-yelp-red transition truncate">
            {restaurant.name}
          </h3>
          <div className="flex items-center gap-2 mt-1 flex-wrap">
            <StarDisplay rating={restaurant.average_rating || 0} size={16} />
            <span className="text-sm text-gray-500">
              {restaurant.review_count || 0} reviews
            </span>
            {restaurant.price_range && (
              <span className="text-sm text-gray-500">• {restaurant.price_range}</span>
            )}
          </div>
          {restaurant.cuisine_type && (
            <p className="text-sm text-gray-600 mt-1">
              {restaurant.cuisine_type}
              {restaurant.city && ` • ${restaurant.city}`}
            </p>
          )}
          {restaurant.description && (
            <p className="text-sm text-gray-500 mt-2 line-clamp-2">{restaurant.description}</p>
          )}
        </div>
        <div className="flex justify-end mt-2">
          <FiChevronRight className="text-gray-400 group-hover:text-yelp-red transition" size={20} />
        </div>
      </div>
    </Link>
  );
}

export default memo(RestaurantCard);
