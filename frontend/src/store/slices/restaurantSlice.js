import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  searchResults: [],
  detail: null,
  lastSearchParams: null,
};

const restaurantSlice = createSlice({
  name: 'restaurants',
  initialState,
  reducers: {
    setSearchResults: (state, action) => {
      state.searchResults = action.payload.list || [];
      state.lastSearchParams = action.payload.params || null;
    },
    setRestaurantDetail: (state, action) => {
      state.detail = action.payload;
    },
    clearRestaurantDetail: (state) => {
      state.detail = null;
    },
  },
});

export const { setSearchResults, setRestaurantDetail, clearRestaurantDetail } = restaurantSlice.actions;
export default restaurantSlice.reducer;
