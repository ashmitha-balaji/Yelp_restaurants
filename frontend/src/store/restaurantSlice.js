import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  list: [],
  detailsById: {},
  loadingList: false,
  loadingDetails: false,
  error: null,
  lastQuery: null,
};

const restaurantSlice = createSlice({
  name: 'restaurant',
  initialState,
  reducers: {
    setRestaurantListLoading: (state, action) => {
      state.loadingList = Boolean(action.payload);
      if (action.payload) state.error = null;
    },
    setRestaurantList: (state, action) => {
      state.list = Array.isArray(action.payload?.restaurants) ? action.payload.restaurants : [];
      state.lastQuery = action.payload?.query || null;
      state.loadingList = false;
      state.error = null;
    },
    setRestaurantDetailLoading: (state, action) => {
      state.loadingDetails = Boolean(action.payload);
      if (action.payload) state.error = null;
    },
    setRestaurantDetail: (state, action) => {
      const restaurant = action.payload || null;
      if (!restaurant?.id) {
        state.loadingDetails = false;
        return;
      }
      state.detailsById[restaurant.id] = restaurant;
      state.loadingDetails = false;
      state.error = null;
    },
    setRestaurantError: (state, action) => {
      state.error = action.payload || 'Restaurant request failed';
      state.loadingList = false;
      state.loadingDetails = false;
    },
    clearRestaurantState: () => initialState,
  },
});

export const {
  setRestaurantListLoading,
  setRestaurantList,
  setRestaurantDetailLoading,
  setRestaurantDetail,
  setRestaurantError,
  clearRestaurantState,
} = restaurantSlice.actions;

export const selectRestaurantList = (state) => state.restaurant.list;
export const selectRestaurantDetailsById = (state) => state.restaurant.detailsById;
export const selectRestaurantLoadingList = (state) => state.restaurant.loadingList;
export const selectRestaurantLoadingDetails = (state) => state.restaurant.loadingDetails;

export default restaurantSlice.reducer;
