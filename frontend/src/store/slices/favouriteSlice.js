import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  items: [],
  favoriteIds: [],
};

const favouriteSlice = createSlice({
  name: 'favourites',
  initialState,
  reducers: {
    setFavourites: (state, action) => {
      state.items = action.payload.items || action.payload || [];
      state.favoriteIds = (action.payload.items || action.payload || []).map((f) =>
        f.restaurant_id != null ? f.restaurant_id : f.restaurant?.id
      ).filter(Boolean);
    },
    addFavoriteId: (state, action) => {
      const id = action.payload;
      if (!state.favoriteIds.includes(id)) state.favoriteIds.push(id);
    },
    removeFavoriteId: (state, action) => {
      const id = action.payload;
      state.favoriteIds = state.favoriteIds.filter((x) => x !== id);
    },
  },
});

export const { setFavourites, addFavoriteId, removeFavoriteId } = favouriteSlice.actions;
export default favouriteSlice.reducer;
