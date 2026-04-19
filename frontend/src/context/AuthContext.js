import React, { createContext, useState, useContext, useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { userAPI } from '../services/api';
import {
  setCredentials,
  clearCredentials,
  setAuthLoading,
  updateAuthUser,
} from '../store/authSlice';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const dispatch = useDispatch();

  useEffect(() => {
    dispatch(setAuthLoading(true));
    const token = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    if (token && savedUser) {
      try {
        const parsedUser = JSON.parse(savedUser);
        setUser(parsedUser);
        dispatch(setCredentials({ token, user: parsedUser }));
        userAPI.getProfile()
          .then((res) => {
            setUser(res.data);
            localStorage.setItem('user', JSON.stringify(res.data));
            dispatch(updateAuthUser(res.data));
          })
          .catch(() => {
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            setUser(null);
            dispatch(clearCredentials());
          });
      } catch {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        dispatch(clearCredentials());
      }
    } else {
      dispatch(clearCredentials());
    }
    setLoading(false);
    dispatch(setAuthLoading(false));
  }, [dispatch]);

  const login = (token, userData) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
    dispatch(setCredentials({ token, user: userData }));
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    dispatch(clearCredentials());
  };

  const updateUser = (userData) => {
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
    dispatch(updateAuthUser(userData));
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
