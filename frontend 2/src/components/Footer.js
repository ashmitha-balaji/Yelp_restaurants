import React from 'react';
import { Link } from 'react-router-dom';
import YelpLogo from './YelpLogo';

export default function Footer() {
  const footerSections = {
    'About': [
      'About Yelp',
      'Careers',
      'Press',
      'Investor Relations',
      'Trust & Safety',
      'Content Guidelines',
      'Accessibility Statement',
      'Terms of Service',
      'Privacy Policy',
      'Ad Choices',
      'Your Privacy Choices',
    ],
    'Discover': [
      'Restaurant Search',
      'Write a Review',
      'Favorites',
      'Support',
    ],
    'For Restaurant Owners': [
      'Add Your Restaurant',
      'Claim Your Business',
      'Owner Dashboard',
      'Manage Reviews',
    ],
  };

  return (
    <footer className="bg-white border-t border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-12">
          {Object.entries(footerSections).map(([title, links]) => (
            <div key={title}>
              <h4 className="font-semibold text-gray-900 mb-4 text-sm">{title}</h4>
              <ul className="space-y-2">
                {links.slice(0, 8).map((link) => (
                  <li key={link}>
                    <Link to="/" className="text-gray-600 hover:text-yelp-red text-sm transition">
                      {link}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="border-t border-gray-200 pt-8 flex flex-col md:flex-row gap-6">
          <div className="flex items-center gap-4">
            <select className="border border-gray-300 rounded px-3 py-2 text-sm text-gray-700">
              <option>Languages - English</option>
            </select>
            <select className="border border-gray-300 rounded px-3 py-2 text-sm text-gray-700">
              <option>Cities - Explore a City</option>
            </select>
          </div>
        </div>

        <div className="border-t border-gray-200 mt-8 pt-8 flex flex-col md:flex-row justify-between items-start gap-6">
          <div>
            <YelpLogo className="mb-4" />
            <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-600">
              <Link to="/" className="hover:text-yelp-red">About</Link>
              <Link to="/" className="hover:text-yelp-red">Blog</Link>
              <Link to="/" className="hover:text-yelp-red">Support</Link>
              <Link to="/" className="hover:text-yelp-red">Terms</Link>
              <Link to="/" className="hover:text-yelp-red">Privacy Policy</Link>
              <Link to="/" className="hover:text-yelp-red">Your Privacy Choices</Link>
              <Link to="/add-restaurant" className="hover:text-yelp-red">Add Restaurant</Link>
            </div>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-gray-200 text-center text-sm text-gray-500">
          <p>Copyright © 2004–2026 Yelp Inc. Yelp, Elite Squad, Yelp logo, Yelp burst and related marks are registered trademarks of Yelp.</p>
          <p className="mt-2 text-xs">This is a prototype for educational purposes. Not affiliated with Yelp Inc.</p>
        </div>
      </div>
    </footer>
  );
}
