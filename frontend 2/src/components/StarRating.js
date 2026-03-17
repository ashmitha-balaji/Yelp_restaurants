import React from 'react';
import { FiStar } from 'react-icons/fi';

export function StarDisplay({ rating, size = 16, showNumber = true }) {
  const stars = [];
  const fullStars = Math.floor(rating);
  const hasHalf = rating - fullStars >= 0.25;

  for (let i = 0; i < 5; i++) {
    stars.push(
      <FiStar
        key={i}
        size={size}
        className={i < fullStars ? 'text-yellow-400 fill-yellow-400' : (i === fullStars && hasHalf) ? 'text-yellow-400 fill-yellow-200' : 'text-gray-300'}
      />
    );
  }

  return (
    <div className="flex items-center space-x-1">
      <div className="flex">{stars}</div>
      {showNumber && <span className="text-sm text-gray-600 ml-1">{rating.toFixed(1)}</span>}
    </div>
  );
}

export function StarInput({ rating, onChange }) {
  return (
    <div className="flex items-center space-x-1 star-rating">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          onClick={() => onChange(star)}
          className="star focus:outline-none"
        >
          <FiStar
            size={28}
            className={star <= rating ? 'text-yellow-400 fill-yellow-400' : 'text-gray-300 hover:text-yellow-300'}
          />
        </button>
      ))}
      <span className="ml-2 text-sm text-gray-600">
        {rating > 0 ? `${rating} star${rating > 1 ? 's' : ''}` : 'Select rating'}
      </span>
    </div>
  );
}
