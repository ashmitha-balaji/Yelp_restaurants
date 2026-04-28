import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate, useLocation, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { API_BASE, notificationAPI } from '../services/api';
import YelpLogo from './YelpLogo';
import { FiMenu, FiX, FiUser, FiHeart, FiStar, FiLogOut, FiSettings, FiGrid, FiSearch, FiChevronDown, FiBell } from 'react-icons/fi';

const CATEGORIES = ['Restaurants'];

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const [menuOpen, setMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [notifMenuOpen, setNotifMenuOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState([]);
  const notifMenuRef = useRef(null);

  // Poll for unread notification count
  useEffect(() => {
    if (!user) { setUnreadCount(0); return; }
    let cancelled = false;
    const tick = async () => {
      try {
        const r = await notificationAPI.unreadCount();
        if (!cancelled) setUnreadCount(r.data?.unread_count || 0);
      } catch {}
    };
    tick();
    const id = setInterval(tick, 30000);
    return () => { cancelled = true; clearInterval(id); };
  }, [user]);

  // Close notification dropdown on outside click
  useEffect(() => {
    const onClickAway = (e) => {
      if (notifMenuRef.current && !notifMenuRef.current.contains(e.target)) setNotifMenuOpen(false);
    };
    if (notifMenuOpen) document.addEventListener('mousedown', onClickAway);
    return () => document.removeEventListener('mousedown', onClickAway);
  }, [notifMenuOpen]);

  const openNotifications = async () => {
    setNotifMenuOpen(!notifMenuOpen);
    if (!notifMenuOpen) {
      try {
        const r = await notificationAPI.list({ limit: 10 });
        setNotifications(r.data?.notifications || r.data || []);
      } catch {}
    }
  };

  const markAllRead = async () => {
    try {
      await notificationAPI.markAllRead();
      setUnreadCount(0);
      setNotifications(notifications.map((n) => ({ ...n, is_read: true, read: true })));
    } catch {}
  };
  const [searchInput, setSearchInput] = useState('');
  const [locationInput, setLocationInput] = useState('');
  // Hide top navbar search on home page (Home already has its own search UI)
  const showSearchBar = location.pathname !== '/';
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
      setSearchInput(urlSearch || '');
      setLocationInput(urlLocation || '');
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

  const handleLogoClick = () => {
    setSearchInput('');
    setLocationInput('');
    navigate(`/?reset=${Date.now()}`);
  };

  const hasProfilePhoto = !!user?.profile_picture;
  const profilePhotoUrl = hasProfilePhoto ? `${API_BASE}${user.profile_picture}` : '';

  return (
    <>
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <YelpLogo onClick={handleLogoClick} />

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
              <Link to="/write-review" className="text-gray-700 hover:text-yelp-red px-3 py-2 text-sm transition">
                Write a Review
              </Link>
              <Link to="/add-restaurant" className="text-gray-700 hover:text-yelp-red px-3 py-2 text-sm transition">
                Start a Project
              </Link>
              {user && (
                <div ref={notifMenuRef} className="relative ml-2">
                  <button
                    onClick={openNotifications}
                    className="relative flex items-center justify-center w-10 h-10 rounded-full border border-gray-300 hover:border-yelp-red transition"
                    title="Notifications"
                  >
                    <FiBell size={18} className="text-gray-700" />
                    {unreadCount > 0 && (
                      <span className="absolute -top-1 -right-1 bg-yelp-red text-white text-[10px] font-bold rounded-full min-w-[18px] h-[18px] flex items-center justify-center px-1">
                        {unreadCount > 99 ? '99+' : unreadCount}
                      </span>
                    )}
                  </button>
                  {notifMenuOpen && (
                    <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-xl py-2 border border-gray-100 max-h-96 overflow-auto">
                      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-100">
                        <span className="text-sm font-semibold text-gray-900">Notifications</span>
                        {unreadCount > 0 && (
                          <button onClick={markAllRead} className="text-xs text-yelp-red hover:underline">
                            Mark all read
                          </button>
                        )}
                      </div>
                      {notifications.length === 0 ? (
                        <div className="px-4 py-6 text-center text-sm text-gray-500">No notifications yet</div>
                      ) : (
                        notifications.map((n) => {
                          const isRead = n.is_read ?? n.read ?? false;
                          const title = n.title || n.subject || '(no subject)';
                          return (
                            <div
                              key={n.id || n._id}
                              className={`px-4 py-3 border-b border-gray-50 last:border-b-0 ${isRead ? 'bg-white' : 'bg-red-50/50'}`}
                            >
                              <div className="flex items-start gap-2">
                                {!isRead && <span className="w-2 h-2 mt-1.5 rounded-full bg-yelp-red flex-shrink-0" />}
                                <div className="flex-1 min-w-0">
                                  <p className="text-sm font-medium text-gray-900">{title}</p>
                                  {n.body && (
                                    <p className="text-xs text-gray-600 mt-0.5 whitespace-pre-line line-clamp-3">
                                      {n.body}
                                    </p>
                                  )}
                                  {n.created_at && (
                                    <p className="text-xs text-gray-400 mt-1">{new Date(n.created_at).toLocaleString()}</p>
                                  )}
                                </div>
                              </div>
                            </div>
                          );
                        })
                      )}
                    </div>
                  )}
                </div>
              )}
              {user ? (
                <div ref={userMenuRef} className="relative ml-2">
                  <button
                    onClick={() => setUserMenuOpen(!userMenuOpen)}
                    className="flex items-center gap-2 px-3 py-2 rounded-full border border-gray-300 hover:border-yelp-red transition"
                  >
                    <div className="w-7 h-7 rounded-full bg-yelp-red overflow-hidden flex items-center justify-center text-white text-xs font-bold">
                      {hasProfilePhoto ? (
                        <img src={profilePhotoUrl} alt={user.name || 'Profile'} className="w-full h-full object-cover" />
                      ) : (
                        user.name?.charAt(0).toUpperCase()
                      )}
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
                <Link to="/write-review" onClick={() => setMenuOpen(false)} className="block py-2 text-gray-700">Write a Review</Link>
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
