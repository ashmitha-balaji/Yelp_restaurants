import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate, useLocation, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import YelpLogo from './YelpLogo';
import { FiMenu, FiX, FiUser, FiHeart, FiStar, FiLogOut, FiSettings, FiGrid, FiSearch, FiChevronDown } from 'react-icons/fi';

const CATEGORIES = ['Restaurants'];

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const [menuOpen, setMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [searchInput, setSearchInput] = useState('');
  const [locationInput, setLocationInput] = useState('Livermore, CA');
  const showSearchBar = true; // Show search on all pages like Yelp
  const userMenuRef = useRef(null);

  // Close user dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target)) {
        setUserMenuOpen(false);
      }
    };
    if (userMenuOpen) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [userMenuOpen]);

  // Sync search inputs with URL when on home
  useEffect(() => {
    if (location.pathname === '/') {
      const urlSearch = searchParams.get('search');
      const urlLocation = searchParams.get('location');
      if (urlSearch) setSearchInput(urlSearch);
      if (urlLocation) setLocationInput(urlLocation);
    }
  }, [location.pathname, searchParams]);

  const handleCategoryClick = (category) => {
    const params = new URLSearchParams();
    params.set('search', category);
    params.set('location', locationInput);
    navigate(`/?${params.toString()}`);
  };

  const handleLogout = () => {
    logout();
    navigate('/');
    setMenuOpen(false);
    setUserMenuOpen(false);
  };

  const handleSearch = (e) => {
    e?.preventDefault();
    const params = new URLSearchParams();
    if (searchInput) params.set('search', searchInput);
    if (locationInput) params.set('location', locationInput);
    navigate(`/?${params.toString()}`);
  };

  return (
    <>
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <YelpLogo />

            {/* Search bar - Yelp style */}
            {showSearchBar && (
              <form onSubmit={handleSearch} className="hidden lg:flex flex-1 max-w-2xl mx-8">
                <div className="flex w-full border border-gray-300 rounded-lg overflow-hidden">
                  <input
                    type="text"
                    value={searchInput}
                    onChange={(e) => setSearchInput(e.target.value)}
                    placeholder="Restaurants, pizza, delivery..."
                    className="flex-1 px-4 py-2.5 text-sm text-gray-800 placeholder-gray-500 focus:outline-none border-r border-gray-300"
                  />
                  <input
                    type="text"
                    value={locationInput}
                    onChange={(e) => setLocationInput(e.target.value)}
                    placeholder="Location"
                    className="w-40 px-4 py-2.5 text-sm text-gray-700 border-r border-gray-300 focus:outline-none"
                  />
                  <button type="submit" className="bg-yelp-red text-white px-5 py-2.5 hover:bg-yelp-dark transition flex items-center">
                    <FiSearch size={18} />
                  </button>
                </div>
              </form>
            )}

            {/* Right nav - Yelp style */}
            <div className="hidden md:flex items-center gap-1">
              {user?.role === 'owner' && (
                <Link to="/owner/dashboard" className="text-gray-700 hover:text-yelp-red px-3 py-2 text-sm transition flex items-center gap-1">
                  For Restaurant Owners
                </Link>
              )}
              <Link to="/" className="text-gray-700 hover:text-yelp-red px-3 py-2 text-sm transition">
                Write a Review
              </Link>
              <Link to="/add-restaurant" className="text-gray-700 hover:text-yelp-red px-3 py-2 text-sm transition">
                Start a Project
              </Link>
              {user ? (
                <div ref={userMenuRef} className="relative ml-2">
                  <button
                    onClick={() => setUserMenuOpen(!userMenuOpen)}
                    className="flex items-center gap-2 px-3 py-2 rounded-full border border-gray-300 hover:border-yelp-red transition"
                  >
                    <div className="w-7 h-7 rounded-full bg-yelp-red flex items-center justify-center text-white text-xs font-bold">
                      {user.name?.charAt(0).toUpperCase()}
                    </div>
                    <span className="text-sm font-medium text-gray-700 max-w-24 truncate">{user.name?.split(' ')[0]}</span>
                  </button>
                  {userMenuOpen && (
                  <div className="absolute right-0 mt-2 w-52 bg-white rounded-lg shadow-xl py-2 border border-gray-100">
                    <Link to="/profile" onClick={() => setUserMenuOpen(false)} className="flex items-center px-4 py-2.5 text-gray-700 hover:bg-gray-50 text-sm">
                      <FiUser className="mr-3 text-gray-400" size={16} />Profile
                    </Link>
                    <Link to="/preferences" onClick={() => setUserMenuOpen(false)} className="flex items-center px-4 py-2.5 text-gray-700 hover:bg-gray-50 text-sm">
                      <FiSettings className="mr-3 text-gray-400" size={16} />Preferences
                    </Link>
                    <Link to="/favorites" onClick={() => setUserMenuOpen(false)} className="flex items-center px-4 py-2.5 text-gray-700 hover:bg-gray-50 text-sm">
                      <FiHeart className="mr-3 text-gray-400" size={16} />Favorites
                    </Link>
                    <Link to="/my-reviews" onClick={() => setUserMenuOpen(false)} className="flex items-center px-4 py-2.5 text-gray-700 hover:bg-gray-50 text-sm">
                      <FiStar className="mr-3 text-gray-400" size={16} />My Reviews
                    </Link>
                    <Link to="/history" onClick={() => setUserMenuOpen(false)} className="flex items-center px-4 py-2.5 text-gray-700 hover:bg-gray-50 text-sm">
                      <FiStar className="mr-3 text-gray-400" size={16} />History
                    </Link>
                    {user.role === 'owner' && (
                      <Link to="/owner/dashboard" onClick={() => setUserMenuOpen(false)} className="flex items-center px-4 py-2.5 text-gray-700 hover:bg-gray-50 text-sm">
                        <FiGrid className="mr-3 text-gray-400" size={16} />Dashboard
                      </Link>
                    )}
                    <hr className="my-2" />
                    <button onClick={handleLogout} className="flex items-center w-full px-4 py-2.5 text-red-600 hover:bg-gray-50 text-sm">
                      <FiLogOut className="mr-3" size={16} />Log Out
                    </button>
                  </div>
                  )}
                </div>
              ) : (
                <>
                  <Link to="/login" className="text-gray-700 hover:text-yelp-red px-4 py-2 text-sm font-medium transition border border-gray-300 rounded-full ml-2">
                    Log In
                  </Link>
                  <Link to="/signup" className="bg-yelp-red text-white px-4 py-2 rounded-full text-sm font-semibold hover:bg-yelp-dark transition ml-2">
                    Sign Up
                  </Link>
                </>
              )}
            </div>

            <button onClick={() => setMenuOpen(!menuOpen)} className="md:hidden text-gray-700 p-2">
              {menuOpen ? <FiX size={24} /> : <FiMenu size={24} />}
            </button>
          </div>
        </div>

        {/* Category navigation - Yelp style */}
        {showSearchBar && (
          <div className="border-t border-gray-200 hidden lg:block">
            <div className="max-w-7xl mx-auto px-4">
              <div className="flex items-center gap-1 py-2">
                {CATEGORIES.map((cat) => (
                  <button
                    key={cat}
                    onClick={() => handleCategoryClick(cat)}
                    className="flex items-center gap-1 px-3 py-2 text-sm text-gray-700 hover:text-yelp-red transition rounded hover:bg-gray-50"
                  >
                    {cat} <FiChevronDown size={12} />
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Mobile menu */}
        {menuOpen && (
          <div className="md:hidden bg-white border-t border-gray-200 px-4 py-4 shadow-lg">
            {user ? (
              <div className="space-y-1">
                <Link to="/profile" onClick={() => setMenuOpen(false)} className="block py-2 text-gray-700">Profile</Link>
                <Link to="/add-restaurant" onClick={() => setMenuOpen(false)} className="block py-2 text-gray-700">Write a Review</Link>
                <Link to="/favorites" onClick={() => setMenuOpen(false)} className="block py-2 text-gray-700">Favorites</Link>
                <Link to="/history" onClick={() => setMenuOpen(false)} className="block py-2 text-gray-700">History</Link>
                <Link to="/my-reviews" onClick={() => setMenuOpen(false)} className="block py-2 text-gray-700">My Reviews</Link>
                <button onClick={handleLogout} className="block py-2 text-red-600 w-full text-left">Log Out</button>
              </div>
            ) : (
              <div className="space-y-1">
                <Link to="/login" onClick={() => setMenuOpen(false)} className="block py-2 text-gray-700">Log In</Link>
                <Link to="/signup" onClick={() => setMenuOpen(false)} className="block py-2 text-yelp-red font-medium">Sign Up</Link>
              </div>
            )}
          </div>
        )}
      </nav>
    </>
  );
}
