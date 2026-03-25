import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const CITIES = [
  'Los Angeles', 'New York', 'Chicago', 'Houston', 'San Diego', 'Las Vegas',
  'San Francisco', 'Dallas', 'San Jose', 'Phoenix', 'Philadelphia', 'Atlanta',
  'Austin', 'Brooklyn', 'Seattle', 'Miami', 'Denver', 'Boston',
];

const TOP_SEARCHES = ['Ramen', 'Korean BBQ', 'Sushi', 'Coffee', 'Chinese Food', 'Pizza', 'Mexican', 'Indian', 'Thai'];
const TRENDING_SEARCHES = ['Margaritas', 'Chinese Bakery', 'Steak House', 'Brunch', 'Salmon', 'Burgers'];
const SEASONAL_SEARCHES = ['Steak House', 'King Cake', 'Urgent Care 24 Hour'];

export default function ExploreCities() {
  const navigate = useNavigate();
  const [selectedCity, setSelectedCity] = useState('Los Angeles');

  const handleSearchClick = (searchTerm) => {
    const location = selectedCity.includes(',') ? selectedCity : `${selectedCity}, CA`;
    navigate(`/?search=${encodeURIComponent(searchTerm)}&location=${encodeURIComponent(location)}`);
  };

  return (
    <section className="py-12 bg-white">
      <div className="max-w-5xl mx-auto px-4">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Explore searches in popular cities</h2>
        <p className="text-gray-600 mb-6">Discover what people are searching for in each city</p>

        <div className="flex flex-wrap gap-2 mb-8">
          {CITIES.map((city) => (
            <button
              key={city}
              onClick={() => setSelectedCity(city)}
              className={`px-4 py-2 rounded-full text-sm font-medium transition ${
                selectedCity === city
                  ? 'bg-teal-500 text-white'
                  : 'bg-white border border-gray-300 text-gray-700 hover:border-teal-500 hover:text-teal-600'
              }`}
            >
              {city}
            </button>
          ))}
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">Top Searches in {selectedCity}, CA</h3>
            <ul className="space-y-2">
              {TOP_SEARCHES.map((s) => (
                <li key={s}>
                  <button onClick={() => handleSearchClick(s)} className="text-yelp-red hover:underline text-left">
                    {s}
                  </button>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">Trending Searches in {selectedCity}, CA</h3>
            <ul className="space-y-2">
              {TRENDING_SEARCHES.map((s) => (
                <li key={s}>
                  <button onClick={() => handleSearchClick(s)} className="text-yelp-red hover:underline text-left">
                    {s}
                  </button>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">Seasonal Searches in {selectedCity}, CA</h3>
            <ul className="space-y-2">
              {SEASONAL_SEARCHES.map((s) => (
                <li key={s}>
                  <button onClick={() => handleSearchClick(s)} className="text-yelp-red hover:underline text-left">
                    {s}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
