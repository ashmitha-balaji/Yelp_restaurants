import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { restaurantAPI } from '../services/api';
import RestaurantCard from '../components/RestaurantCard';
import RestaurantCardSkeleton from '../components/RestaurantCardSkeleton';
import CategoriesGrid from '../components/CategoriesGrid';
import ExploreCities from '../components/ExploreCities';
import RecentActivity from '../components/RecentActivity';
import { useAuth } from '../context/AuthContext';
import { FiSearch, FiFilter, FiMapPin, FiClock, FiDollarSign, FiList } from 'react-icons/fi';

const CUISINES = ['Italian', 'Chinese', 'Mexican', 'Indian', 'Japanese', 'American', 'Thai', 'French', 'Mediterranean', 'Korean'];

export default function Home() {
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState(searchParams.get('search') || '');
  const [location, setLocation] = useState(searchParams.get('location') || '');
  const [filters, setFilters] = useState({ cuisine_type: '', city: '', price_range: '' });
  const [showFilters, setShowFilters] = useState(false);

  const priceOptions = ['$', '$$', '$$$', '$$$$'];

  const fetchRestaurants = useCallback(async () => {
    setLoading(true);
    try {
      // Build Yelp params
      const term = search || filters.cuisine_type || 'restaurants';
      const city =
        (filters.city && filters.city.trim()) ||
        (location && location.trim()) ||
        'San Jose, CA';
  
      const res = await restaurantAPI.searchYelp({
        term,
        city,
        limit: 20,
      });
  
      // Backend returns { restaurants: [...] }
      setRestaurants(res.data.restaurants || res.data || []);
    } catch (err) {
      console.error('Failed to load Yelp restaurants:', err);
  
      // Optional fallback to your own DB if Yelp fails
      try {
        const params = {};
        if (search) params.keyword = search;
        if (location) params.city = location;
        if (filters.cuisine_type) params.cuisine_type = filters.cuisine_type;
        if (filters.city) params.city = filters.city || location;
        if (filters.price_range) params.price_range = filters.price_range;
  
        const res = await restaurantAPI.search(params);
        setRestaurants(res.data || []);
      } catch (fallbackErr) {
        console.error('Fallback DB search failed:', fallbackErr);
        setRestaurants([]);
      }
    }
    setLoading(false);
  }, [search, location, filters]);

  useEffect(() => {
    const urlSearch = searchParams.get('search');
    const urlLocation = searchParams.get('location');
    if (urlSearch) setSearch(urlSearch);
    if (urlLocation) setLocation(urlLocation);
  }, [searchParams]);

  useEffect(() => {
    const timer = setTimeout(fetchRestaurants, 400);
    return () => clearTimeout(timer);
  }, [fetchRestaurants]);

  const clearFilters = () => {
    setFilters({ cuisine_type: '', city: '', price_range: '' });
    setSearch('');
    setLocation('');
    setSearchParams({});
  };

  const hasActiveFilters = filters.cuisine_type || filters.city || filters.price_range || search || location;

  return (
    <div className="min-h-screen flex flex-col bg-white">
      {/* Hero Section - Yelp "Top 100 Places to Eat" style */}
      <section className="relative bg-gray-900 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-gray-900 via-gray-800 to-transparent z-10" />
        <div
          className="absolute inset-0 bg-cover bg-center opacity-60"
          style={{
            backgroundImage: "url('https://images.unsplash.com/photo-1544025162-d76694265947?w=1200')",
          }}
        />
        <div className="relative z-20 max-w-7xl mx-auto px-4 py-20 md:py-28">
          <div className="max-w-xl">
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Top 100 Places to Eat in 2026
            </h1>
            <Link
              to="/"
              className="inline-flex items-center gap-2 bg-yelp-red text-white px-6 py-3 rounded-lg font-semibold hover:bg-yelp-dark transition"
            >
              <FiList size={20} /> See list
            </Link>
            <p className="text-white/80 text-sm mt-6">Fat Of The Land • Photo from the business owner</p>
          </div>
        </div>
      </section>

      {/* Search & Filters bar */}
      <section className="bg-white border-b border-gray-200 sticky top-[7.5rem] z-40">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex flex-col md:flex-row gap-4">
            <form
            onSubmit={(e) => {
              e.preventDefault();
              setSearchParams({ ...(search && { search }), ...(location && { location }) });
              fetchRestaurants();
            }}
            className="flex-1 flex gap-2"
          >
            <div className="flex-1 flex items-center border border-gray-300 rounded-lg overflow-hidden">
              <FiSearch className="text-gray-400 ml-3" size={18} />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Restaurants, pizza, delivery..."
                className="flex-1 px-3 py-2.5 text-sm focus:outline-none"
              />
            </div>
            <div className="flex items-center border border-gray-300 rounded-lg overflow-hidden w-48">
              <FiMapPin className="text-gray-400 ml-3" size={18} />
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="San Jose, CA or zip code"
                className="flex-1 px-3 py-2.5 text-sm focus:outline-none"
              />
            </div>
            <button
              type="submit"
              className="bg-yelp-red text-white px-6 py-2.5 rounded-lg font-semibold hover:bg-yelp-dark transition"
            >
              Search
            </button>
          </form>
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`flex items-center gap-1 text-sm font-medium ${showFilters ? 'text-yelp-red' : 'text-gray-600 hover:text-yelp-red'}`}
            >
              <FiFilter size={14} /> {showFilters ? '▲' : '▼'} Filters
            </button>
          </div>

          {showFilters && (
            <div className="mt-4 pt-4 border-t border-gray-100 grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Cuisine</label>
                <select
                  value={filters.cuisine_type}
                  onChange={(e) => setFilters({ ...filters, cuisine_type: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                >
                  <option value="">All cuisines</option>
                  {CUISINES.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">City</label>
                <input
                  value={filters.city || location}
                  onChange={(e) => setFilters({ ...filters, city: e.target.value })}
                  placeholder="City or zip"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Price</label>
                <select
                  value={filters.price_range}
                  onChange={(e) => setFilters({ ...filters, price_range: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                >
                  <option value="">Any</option>
                  {priceOptions.map((p) => <option key={p} value={p}>{p}</option>)}
                </select>
              </div>
              <div className="flex items-end">
                <button onClick={clearFilters} className="text-sm text-yelp-red hover:underline font-medium">
                  Clear all filters
                </button>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Categories - Yelp style */}
      <CategoriesGrid />

      {/* Main content */}
      <div className="flex-1 flex min-h-0 bg-gray-50">
        <div className="flex-1 overflow-auto w-full">
          {/* Restaurant results */}
          <div className="max-w-5xl mx-auto px-4 py-8">
            {loading ? (
              <div className="space-y-6">
                {[1, 2, 3, 4, 5].map((i) => <RestaurantCardSkeleton key={i} />)}
              </div>
            ) : restaurants.length > 0 ? (
              <>
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-bold text-gray-900">
                    {search || hasActiveFilters ? 'Search Results' : 'Best Restaurants'}
                    <span className="text-gray-500 font-normal ml-2">({restaurants.length})</span>
                  </h2>
                  <div className="flex items-center gap-4 text-sm text-gray-500">
                    <span className="flex items-center gap-1"><FiClock size={14} />Open now</span>
                    <span className="flex items-center gap-1"><FiDollarSign size={14} />Price</span>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {restaurants.map((r) => (
                    <RestaurantCard key={r.id} restaurant={r} />
                  ))}
                </div>
              </>
            ) : (
              <div className="text-center py-16 bg-white rounded-xl border border-gray-200">
                <div className="text-6xl mb-4">🍽️</div>
                <h3 className="text-xl font-bold text-gray-800 mb-2">No restaurants found</h3>
                <p className="text-gray-500 mb-6">
                  {search || hasActiveFilters
                ? 'Try adjusting your search or filters.'
                : 'Be the first to add a restaurant!'}
                </p>
                <Link to="/add-restaurant" className="inline-block bg-yelp-red text-white px-6 py-3 rounded-full font-semibold hover:bg-yelp-dark transition">
                  Add a Restaurant
                </Link>
              </div>
            )}
          </div>

          {/* Explore searches in popular cities */}
          <ExploreCities />

          {/* Recent Activity */}
          <RecentActivity />
        </div>
      </div>
    </div>
  );
}
