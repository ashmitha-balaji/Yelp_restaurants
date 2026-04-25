import { createSlice } from '@reduxjs/toolkit';

const savedUser = (() => {
  try {
    const raw = localStorage.getItem('user');
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
})();

const initialState = {
  token: localStorage.getItem('token') || null,
  user: savedUser,
  loading: true,
};

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setLoading: (state, action) => {
      state.loading = action.payload;
    },
    setCredentials: (state, action) => {
      const { token, user } = action.payload;
      state.token = token;
      state.user = user;
      if (token) localStorage.setItem('token', token);
      else localStorage.removeItem('token');
      if (user) localStorage.setItem('user', JSON.stringify(user));
      else localStorage.removeItem('user');
    },
    setUser: (state, action) => {
      state.user = action.payload;
      if (action.payload) localStorage.setItem('user', JSON.stringify(action.payload));
      else localStorage.removeItem('user');
    },
    logout: (state) => {
      state.token = null;
      state.user = null;
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    },
  },
});

export const { setLoading, setCredentials, setUser, logout } = authSlice.actions;
export default authSlice.reducer;
