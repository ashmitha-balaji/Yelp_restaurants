import React from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { FiCoffee, FiCircle, FiStar, FiDroplet } from 'react-icons/fi';

const CATEGORIES = [
  { name: 'Restaurants', icon: FiCoffee, search: 'Restaurants' },
  { name: 'Pizza', icon: FiCircle, search: 'Pizza' },
  { name: 'Mexican', icon: FiStar, search: 'Mexican' },
  { name: 'Sushi', icon: FiDroplet, search: 'Sushi' },
];

export default function CategoriesGrid() {
  const [searchParams] = useSearchParams();
  const currentLocation = searchParams.get('location') || 'San Jose, CA';

  return (
    <section className="py-12 bg-white">
      <h2 className="text-2xl font-bold text-center text-gray-900 mb-8">Categories</h2>
      <div className="max-w-5xl mx-auto px-4 grid grid-cols-2 sm:grid-cols-4 gap-4">
        {CATEGORIES.map(({ name, icon: Icon, search }) => (
          <Link
            key={name}
            to={search ? `/?search=${encodeURIComponent(search)}&location=${encodeURIComponent(currentLocation)}` : '/'}
            className="flex flex-col items-center p-6 bg-white border border-gray-200 rounded-lg hover:border-yelp-red hover:shadow-md transition group"
          >
            <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center mb-3 group-hover:bg-red-50">
              <Icon className="text-yelp-red" size={24} />
            </div>
            <span className="text-sm font-medium text-gray-900 text-center">{name}</span>
          </Link>
        ))}
      </div>
    </section>
  );
}
