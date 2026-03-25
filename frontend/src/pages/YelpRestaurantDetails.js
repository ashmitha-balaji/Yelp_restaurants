import React, { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { favoriteAPI, restaurantAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { StarDisplay } from '../components/StarRating';
import {
  FiExternalLink,
  FiMapPin,
  FiPhone,
  FiDollarSign,
  FiHeart,
  FiImage,
  FiNavigation,
  FiClock,
} from 'react-icons/fi';

export default function YelpRestaurantDetails() {
  const { yelpId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [restaurant, setRestaurant] = useState(null);
  const [localRestaurantId, setLocalRestaurantId] = useState(null);
  const [isFavorite, setIsFavorite] = useState(false);
  const [favoriteLoading, setFavoriteLoading] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const run = async () => {
      setLoading(true);
      try {
        const res = await restaurantAPI.getYelpById(yelpId);
        setRestaurant(res.data);
      } catch (e) {
        setRestaurant(null);
      } finally {
        setLoading(false);
      }
    };
    run();
  }, [yelpId]);

  useEffect(() => {
    if (!user || !restaurant) return;

    const syncFavoriteState = async () => {
      try {
        const matchRes = await restaurantAPI.search({
          name: restaurant.name,
          city: restaurant.city,
          limit: 10,
        });
        const matches = matchRes.data || [];
        const exact = matches.find(
          (r) =>
            (r.name || '').trim().toLowerCase() === (restaurant.name || '').trim().toLowerCase() &&
            (r.city || '').trim().toLowerCase() === (restaurant.city || '').trim().toLowerCase()
        );
        if (!exact) return;

        setLocalRestaurantId(exact.id);
        const favRes = await favoriteAPI.check(exact.id);
        setIsFavorite(!!favRes.data?.is_favorite);
      } catch {}
    };

    syncFavoriteState();
  }, [user, restaurant]);

  const toggleFavorite = async () => {
    if (!user) {
      navigate('/login');
      return;
    }

    if (!restaurant || favoriteLoading) return;
    setFavoriteLoading(true);
    try {
      let targetRestaurantId = localRestaurantId;
      if (!targetRestaurantId) {
        const createRes = await restaurantAPI.create({
          name: restaurant.name,
          cuisine_type: restaurant.cuisine_type,
          description: 'Imported from Yelp for favorites.',
          address: restaurant.address,
          city: restaurant.city,
          state: restaurant.state,
          zip_code: restaurant.zip_code,
          country: restaurant.country || 'US',
          phone: restaurant.phone,
          price_range: restaurant.price_range,
        });
        targetRestaurantId = createRes.data.id;
        setLocalRestaurantId(targetRestaurantId);
      }

      if (isFavorite) {
        await favoriteAPI.remove(targetRestaurantId);
        setIsFavorite(false);
      } else {
        await favoriteAPI.add(targetRestaurantId);
        setIsFavorite(true);
      }
    } catch (err) {
      // If backend says it's already in favorites, treat it as selected.
      if (err?.response?.status === 400) {
        setIsFavorite(true);
      }
    } finally {
      setFavoriteLoading(false);
    }
  };

  const ensureLocalRestaurantId = async () => {
    if (!restaurant) return null;
    if (localRestaurantId) return localRestaurantId;

    const matchRes = await restaurantAPI.search({
      name: restaurant.name,
      city: restaurant.city,
      limit: 10,
    });
    const matches = matchRes.data || [];
    const exact = matches.find(
      (r) =>
        (r.name || '').trim().toLowerCase() === (restaurant.name || '').trim().toLowerCase() &&
        (r.city || '').trim().toLowerCase() === (restaurant.city || '').trim().toLowerCase()
    );

    if (exact?.id) {
      setLocalRestaurantId(exact.id);
      return exact.id;
    }

    const createRes = await restaurantAPI.create({
      name: restaurant.name,
      cuisine_type: restaurant.cuisine_type,
      description: 'Imported from Yelp for reviews/favorites.',
      address: restaurant.address,
      city: restaurant.city,
      state: restaurant.state,
      zip_code: restaurant.zip_code,
      country: restaurant.country || 'US',
      phone: restaurant.phone,
      price_range: restaurant.price_range,
    });
    const createdId = createRes.data?.id;
    if (createdId) {
      setLocalRestaurantId(createdId);
      return createdId;
    }
    return null;
  };

  const handleWriteReview = async () => {
    if (!user) {
      navigate('/login');
      return;
    }

    try {
      const targetRestaurantId = await ensureLocalRestaurantId();
      if (targetRestaurantId) {
        navigate(`/write-review/${targetRestaurantId}`);
      }
    } catch {}
  };

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yelp-red" />
      </div>
    );
  }

  if (!restaurant) {
    return <div className="text-center py-20 text-gray-500">Restaurant not found.</div>;
  }

  const photos = Array.isArray(restaurant.photos) ? restaurant.photos : [];
  const heroPhoto = photos[0];
  const morePhotos = photos.slice(1, 5);

  const addressLine = [
    restaurant.address,
    restaurant.city,
    restaurant.state,
    restaurant.zip_code,
  ]
    .filter(Boolean)
    .join(', ');

  const directionsUrl = addressLine
    ? `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(addressLine)}`
    : null;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Yelp-inspired hero */}
      <div className="relative bg-black">
        <div className="absolute inset-0">
          {heroPhoto ? (
            <img
              src={heroPhoto}
              alt={restaurant.name}
              className="w-full h-[420px] object-cover opacity-90"
            />
          ) : (
            <div className="w-full h-[420px] bg-gradient-to-br from-gray-900 to-gray-700" />
          )}
          {/* Gradient overlay */}
          <div className="absolute inset-0 bg-gradient-to-r from-black/75 via-black/40 to-black/10" />
          <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />
        </div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="pt-10 pb-8 h-[420px] flex flex-col justify-end">
            <div className="mb-3">
              <Link to="/" className="text-sm text-white/80 hover:text-white">
                ← Back to search
              </Link>
            </div>

            <h1 className="text-4xl md:text-5xl font-extrabold text-white tracking-tight">
              {restaurant.name}
            </h1>

            <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-2 text-white/90">
              <div className="flex items-center gap-2">
                <StarDisplay rating={restaurant.average_rating || 0} size={18} showNumber={true} />
                <span className="text-sm">({restaurant.review_count || 0} reviews)</span>
              </div>
              <span className="text-white/50">•</span>
              {restaurant.price_range ? (
                <span className="text-sm">{restaurant.price_range}</span>
              ) : (
                <span className="text-sm text-white/70">—</span>
              )}
              {restaurant.cuisine_type ? (
                <>
                  <span className="text-white/50">•</span>
                  <span className="text-sm">{restaurant.cuisine_type}</span>
                </>
              ) : null}
              {restaurant.is_closed === false ? (
                <>
                  <span className="text-white/50">•</span>
                  <span className="inline-flex items-center gap-1 text-sm text-green-300">
                    <FiClock /> Open
                  </span>
                </>
              ) : null}
            </div>

            {/* Action bar */}
            <div className="mt-6 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={handleWriteReview}
                className="inline-flex items-center gap-2 bg-white text-gray-900 px-4 py-2 rounded-lg font-semibold hover:bg-gray-100 transition"
              >
                Write a review
              </button>
              <button
                type="button"
                onClick={toggleFavorite}
                disabled={favoriteLoading}
                className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg font-semibold transition border ${
                  isFavorite
                    ? 'bg-red-50 text-yelp-red border-yelp-red'
                    : 'bg-white/10 text-white border-white/20 hover:bg-white/15'
                } ${favoriteLoading ? 'opacity-70 cursor-not-allowed' : ''}`}
              >
                <FiHeart className={isFavorite ? 'fill-yelp-red' : ''} />
                {isFavorite ? 'Favourited' : 'Favourites'}
              </button>
              {restaurant.yelp_url && (
                <a
                  href={restaurant.yelp_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 bg-yelp-red text-white px-4 py-2 rounded-lg font-semibold hover:bg-yelp-dark transition"
                >
                  View on Yelp <FiExternalLink />
                </a>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Photo strip */}
      {morePhotos.length > 0 && (
        <div className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold text-gray-900">Photos</h2>
              <a
                href={restaurant.yelp_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-yelp-red font-medium hover:underline inline-flex items-center gap-1"
              >
                <FiImage /> See all photos
              </a>
            </div>
            <div className="grid grid-cols-4 gap-3">
              {morePhotos.map((p) => (
                <a
                  key={p}
                  href={restaurant.yelp_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="aspect-[4/3] bg-gray-100 rounded-lg overflow-hidden"
                  title="Open Yelp for the full gallery"
                >
                  <img src={p} alt="" className="w-full h-full object-cover hover:scale-105 transition-transform duration-300" />
                </a>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Main content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white rounded-2xl border border-gray-200 p-6">
              <h2 className="text-lg font-bold text-gray-900 mb-2">About</h2>
              <p className="text-sm text-gray-600">
                This page shows live business data from Yelp Fusion. For the complete listing, photos, and reviews, use “View on Yelp”.
              </p>
              <div className="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-xl text-amber-900 text-sm">
                Yelp results are live. Reviews/Favorites in this app only apply to restaurants stored in your own database.
              </div>
            </div>
          </div>

          {/* Right */}
          <div className="space-y-6">
            <div className="bg-white rounded-2xl border border-gray-200 p-6">
              <h3 className="text-sm font-semibold text-gray-900 mb-4">Location & Info</h3>

              {addressLine && (
                <div className="flex items-start gap-3 text-sm text-gray-700 mb-4">
                  <FiMapPin className="mt-0.5 text-gray-500" />
                  <div>
                    <div className="font-medium">{addressLine}</div>
                    {Array.isArray(restaurant.location_display) && restaurant.location_display.length > 0 && (
                      <div className="text-gray-500">{restaurant.location_display.join(', ')}</div>
                    )}
                  </div>
                </div>
              )}

              {restaurant.phone && (
                <div className="flex items-center gap-3 text-sm text-gray-700 mb-4">
                  <FiPhone className="text-gray-500" />
                  <span>{restaurant.phone}</span>
                </div>
              )}

              <div className="flex flex-col gap-2">
                {directionsUrl && (
                  <a
                    href={directionsUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg border border-gray-300 hover:border-gray-400 text-sm font-medium"
                  >
                    <FiNavigation /> Get directions
                  </a>
                )}
                {restaurant.yelp_url && (
                  <a
                    href={restaurant.yelp_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-yelp-red text-white hover:bg-yelp-dark text-sm font-semibold"
                  >
                    View on Yelp <FiExternalLink />
                  </a>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

