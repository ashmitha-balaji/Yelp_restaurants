import { configureStore } from '@reduxjs/toolkit';
import authReducer from './authSlice';
import appReducer from './appSlice';
import restaurantReducer from './restaurantSlice';
import reviewReducer from './reviewSlice';
import favouritesReducer from './favouritesSlice';

const store = configureStore({
  reducer: {
    auth: authReducer,
    app: appReducer,
    restaurant: restaurantReducer,
    review: reviewReducer,
    favourites: favouritesReducer,
  },
  devTools: process.env.NODE_ENV !== 'production',
});

export default store;
