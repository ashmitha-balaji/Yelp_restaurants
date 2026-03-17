import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import ChatBot from './components/ChatBot';
import Home from './pages/Home';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Profile from './pages/Profile';
import Preferences from './pages/Preferences';
import RestaurantDetails from './pages/RestaurantDetails';
import AddRestaurant from './pages/AddRestaurant';
import WriteReview from './pages/WriteReview';
import Favorites from './pages/Favorites';
import MyReviews from './pages/MyReviews';
import History from './pages/History';
import OwnerDashboard from './pages/OwnerDashboard';

function PrivateRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="flex justify-center items-center h-screen"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yelp-red" /></div>;
  return user ? children : <Navigate to="/login" />;
}

function AppRoutes() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Navbar />
      <main className="flex-1">
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/restaurant/:id" element={<RestaurantDetails />} />
        <Route path="/profile" element={<PrivateRoute><Profile /></PrivateRoute>} />
        <Route path="/preferences" element={<PrivateRoute><Preferences /></PrivateRoute>} />
        <Route path="/add-restaurant" element={<PrivateRoute><AddRestaurant /></PrivateRoute>} />
        <Route path="/write-review/:restaurantId" element={<PrivateRoute><WriteReview /></PrivateRoute>} />
        <Route path="/favorites" element={<PrivateRoute><Favorites /></PrivateRoute>} />
        <Route path="/my-reviews" element={<PrivateRoute><MyReviews /></PrivateRoute>} />
        <Route path="/history" element={<PrivateRoute><History /></PrivateRoute>} />
        <Route path="/owner/dashboard" element={<PrivateRoute><OwnerDashboard /></PrivateRoute>} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
      </main>
      <Footer />
      <ChatBot />
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <AppRoutes />
      </Router>
    </AuthProvider>
  );
}

export default App;
