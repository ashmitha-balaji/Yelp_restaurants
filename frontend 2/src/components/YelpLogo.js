import React from 'react';
import { Link } from 'react-router-dom';

export default function YelpLogo({ className = '' }) {
  return (
    <Link to="/" className={`flex items-center gap-1.5 ${className}`}>
      {/* Yelp burst logo - simplified red burst */}
      <svg width="32" height="32" viewBox="0 0 32 32" fill="none" className="shrink-0">
        <path d="M16 2L18 8L16 14L14 8L16 2Z" fill="#d32323"/>
        <path d="M16 30L14 24L16 18L18 24L16 30Z" fill="#d32323"/>
        <path d="M2 16L8 18L14 16L8 14L2 16Z" fill="#d32323"/>
        <path d="M30 16L24 14L18 16L24 18L30 16Z" fill="#d32323"/>
        <path d="M6 6L10 10L8 16L4 12L6 6Z" fill="#d32323"/>
        <path d="M26 26L22 22L16 24L20 28L26 26Z" fill="#d32323"/>
        <path d="M6 26L4 20L10 22L8 28L6 26Z" fill="#d32323"/>
        <path d="M26 6L28 12L22 10L24 4L26 6Z" fill="#d32323"/>
        <circle cx="16" cy="16" r="4" fill="#d32323"/>
      </svg>
      <span className="text-yelp-red text-2xl font-bold tracking-tight lowercase">yelp</span>
    </Link>
  );
}
