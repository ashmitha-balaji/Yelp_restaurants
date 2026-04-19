import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  list: [],
  byRestaurantId: {},
  loading: false,
  error: null,
};

const favouritesSlice = createSlice({
  name: 'favourites',
  initialState,
  reducers: {
    setFavouritesLoading: (state, action) => {
      state.loading = Boolean(action.payload);
      if (action.payload) state.error = null;
    },
    setFavourites: (state, action) => {
      const list = Array.isArray(action.payload) ? action.payload : [];
      state.list = list;
      state.byRestaurantId = {};
      list.forEach((fav) => {
        const rid = fav?.restaurant?.id || fav?.restaurant_id;
        if (rid != null) state.byRestaurantId[String(rid)] = true;
      });
      state.loading = false;
      state.error = null;
    },
    setFavouriteStatus: (state, action) => {
      const restaurantId = String(action.payload?.restaurantId || '');
      if (!restaurantId) return;
      state.byRestaurantId[restaurantId] = Boolean(action.payload?.isFavorite);
    },
    setFavouritesError: (state, action) => {
      state.error = action.payload || 'Favorites request failed';
      state.loading = false;
    },
    clearFavouritesState: () => initialState,
  },
});

export const {
  setFavouritesLoading,
  setFavourites,
  setFavouriteStatus,
  setFavouritesError,
  clearFavouritesState,
} = favouritesSlice.actions;

export const selectFavourites = (state) => state.favourites.list;
export const selectFavouriteStatusByRestaurant = (restaurantId) => (state) =>
  Boolean(state.favourites.byRestaurantId[String(restaurantId || '')]);
export const selectFavouritesLoading = (state) => state.favourites.loading;

export default favouritesSlice.reducer;
