import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  byRestaurant: {},
  myReviews: [],
  loading: false,
  error: null,
};

const reviewSlice = createSlice({
  name: 'review',
  initialState,
  reducers: {
    setReviewLoading: (state, action) => {
      state.loading = Boolean(action.payload);
      if (action.payload) state.error = null;
    },
    setRestaurantReviews: (state, action) => {
      const restaurantId = String(action.payload?.restaurantId || '');
      if (!restaurantId) return;
      state.byRestaurant[restaurantId] = Array.isArray(action.payload?.reviews)
        ? action.payload.reviews
        : [];
      state.loading = false;
      state.error = null;
    },
    setMyReviews: (state, action) => {
      state.myReviews = Array.isArray(action.payload) ? action.payload : [];
      state.loading = false;
      state.error = null;
    },
    removeReviewFromState: (state, action) => {
      const reviewId = Number(action.payload);
      state.myReviews = state.myReviews.filter((r) => r.id !== reviewId);
      Object.keys(state.byRestaurant).forEach((rid) => {
        state.byRestaurant[rid] = (state.byRestaurant[rid] || []).filter((r) => r.id !== reviewId);
      });
    },
    upsertReviewInState: (state, action) => {
      const review = action.payload;
      if (!review?.id) return;
      const rid = String(review.restaurant_id || '');
      if (!rid) return;
      const current = state.byRestaurant[rid] || [];
      const idx = current.findIndex((r) => r.id === review.id);
      if (idx >= 0) current[idx] = review;
      else current.unshift(review);
      state.byRestaurant[rid] = current;
      const myIdx = state.myReviews.findIndex((r) => r.id === review.id);
      if (myIdx >= 0) state.myReviews[myIdx] = review;
    },
    setReviewError: (state, action) => {
      state.error = action.payload || 'Review request failed';
      state.loading = false;
    },
    clearReviewState: () => initialState,
  },
});

export const {
  setReviewLoading,
  setRestaurantReviews,
  setMyReviews,
  removeReviewFromState,
  upsertReviewInState,
  setReviewError,
  clearReviewState,
} = reviewSlice.actions;

export const selectReviewsForRestaurant = (restaurantId) => (state) =>
  state.review.byRestaurant[String(restaurantId || '')] || [];
export const selectMyReviews = (state) => state.review.myReviews;
export const selectReviewLoading = (state) => state.review.loading;

export default reviewSlice.reducer;
