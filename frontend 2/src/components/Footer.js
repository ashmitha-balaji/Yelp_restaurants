import React from 'react';
import YelpLogo from './YelpLogo';

export default function Footer() {
  return (
    <footer className="bg-white border-t border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="flex justify-center">
          <YelpLogo />
        </div>

        <div className="mt-6 pt-6 border-t border-gray-200 text-center text-sm text-gray-500">
          <p>Copyright © 2004–2026 Yelp Inc. Yelp, Elite Squad, Yelp logo, Yelp burst and related marks are registered trademarks of Yelp.</p>
          <p className="mt-2 text-xs">This is a prototype for educational purposes. Not affiliated with Yelp Inc.</p>
        </div>
      </div>
    </footer>
  );
}
