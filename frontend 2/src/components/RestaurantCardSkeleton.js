import React from 'react';

export default function RestaurantCardSkeleton() {
  return (
    <div className="flex bg-white rounded-lg border border-gray-200 overflow-hidden animate-pulse">
      <div className="w-36 md:w-44 h-36 md:h-44 shrink-0 bg-gray-200" />
      <div className="flex-1 p-4 space-y-3">
        <div className="h-5 bg-gray-200 rounded w-3/4" />
        <div className="h-4 bg-gray-200 rounded w-1/2" />
        <div className="h-4 bg-gray-200 rounded w-2/3" />
        <div className="h-3 bg-gray-200 rounded w-full" />
        <div className="h-3 bg-gray-200 rounded w-4/5" />
      </div>
    </div>
  );
}
