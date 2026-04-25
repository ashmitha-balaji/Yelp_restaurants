import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import restaurantReducer from './slices/restaurantSlice';
import reviewReducer from './slices/reviewSlice';
import favouriteReducer from './slices/favouriteSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    restaurants: restaurantReducer,
    reviews: reviewReducer,
    favourites: favouriteReducer,
  },
  devTools: process.env.NODE_ENV !== 'production',
});
