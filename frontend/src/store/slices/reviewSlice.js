import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  recent: [],
  byRestaurantId: {},
  myReviews: [],
  lastJobStatus: null,
};

const reviewSlice = createSlice({
  name: 'reviews',
  initialState,
  reducers: {
    setRecent: (state, action) => {
      state.recent = action.payload;
    },
    setForRestaurant: (state, action) => {
      const { restaurantId, list } = action.payload;
      state.byRestaurantId[restaurantId] = list;
    },
    setMyReviews: (state, action) => {
      state.myReviews = action.payload;
    },
    setLastJobStatus: (state, action) => {
      state.lastJobStatus = action.payload;
    },
  },
});

export const { setRecent, setForRestaurant, setMyReviews, setLastJobStatus } = reviewSlice.actions;
export default reviewSlice.reducer;
