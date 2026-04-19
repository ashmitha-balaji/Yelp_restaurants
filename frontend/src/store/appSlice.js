import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  currentPath: '/',
  currentQuery: '',
  routeVisitCount: 0,
  lastVisitedAt: null,
};

const appSlice = createSlice({
  name: 'app',
  initialState,
  reducers: {
    routeVisited: (state, action) => {
      state.currentPath = action.payload.pathname || '/';
      state.currentQuery = action.payload.search || '';
      state.routeVisitCount += 1;
      state.lastVisitedAt = new Date().toISOString();
    },
  },
});

export const { routeVisited } = appSlice.actions;

export default appSlice.reducer;
