import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  user: null,
  token: null,
  loading: true,
};

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setCredentials: (state, action) => {
      state.user = action.payload.user || null;
      state.token = action.payload.token || null;
      state.loading = false;
    },
    updateAuthUser: (state, action) => {
      state.user = action.payload || null;
    },
    clearCredentials: (state) => {
      state.user = null;
      state.token = null;
      state.loading = false;
    },
    setAuthLoading: (state, action) => {
      state.loading = Boolean(action.payload);
    },
  },
});

export const {
  setCredentials,
  updateAuthUser,
  clearCredentials,
  setAuthLoading,
} = authSlice.actions;

export default authSlice.reducer;
