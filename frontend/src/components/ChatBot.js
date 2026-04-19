import React, { useState, useRef, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { createPortal } from 'react-dom';
import { useAuth } from '../context/AuthContext';
import { aiAPI } from '../services/api';
import { FiMessageCircle, FiX, FiSend, FiTrash2, FiStar } from 'react-icons/fi';

const DEFAULT_WELCOME_MESSAGE = {
  role: 'assistant',
  content: "Hi! I'm your restaurant assistant. Ask me for personalized recommendations based on your preferences!",
};

const getChatStorageKey = (userId) => `chatbot_messages_${userId}`;
const GUEST_CHAT_STORAGE_KEY = 'chatbot_messages_guest';

const normalizeAssistantPayload = (data) => {
  const fallback = {
    message: typeof data?.message === 'string' && data.message.trim()
      ? data.message
      : 'Here are some restaurant recommendations for you.',
    recommendations: Array.isArray(data?.recommendations) ? data.recommendations : [],
  };

  if (typeof data?.message !== 'string') return fallback;
  const raw = data.message.trim();
  if (!raw.includes('"recommendations"') && !raw.startsWith('{')) return fallback;

  try {
    const parsed = JSON.parse(raw);
    return {
      message: typeof parsed?.message === 'string' && parsed.message.trim() ? parsed.message : fallback.message,
      recommendations: Array.isArray(parsed?.recommendations) ? parsed.recommendations : fallback.recommendations,
    };
  } catch {
    return fallback;
  }
};

export default function ChatBot() {
  const { user } = useAuth();
  const { pathname } = useLocation();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([DEFAULT_WELCOME_MESSAGE]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const activeStorageKey = user?.id ? getChatStorageKey(user.id) : GUEST_CHAT_STORAGE_KEY;
  const isGuestHomepage = !user && pathname === '/';

  // Keep chat isolated per user (or guest) and reset on identity switch.
  useEffect(() => {
    if (!user && pathname !== '/') {
      setIsOpen(false);
      setMessages([DEFAULT_WELCOME_MESSAGE]);
      return;
    }

    const stored = localStorage.getItem(activeStorageKey);
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed) && parsed.length > 0) {
          setMessages(parsed);
          return;
        }
      } catch {}
    }

    setMessages([DEFAULT_WELCOME_MESSAGE]);
  }, [activeStorageKey, user, pathname]);

  useEffect(() => {
    if (!user && pathname !== '/') return;
    localStorage.setItem(activeStorageKey, JSON.stringify(messages));
  }, [activeStorageKey, user, pathname, messages]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const quickActions = [
    'Find dinner tonight',
    'Best rated near me',
    'Vegan options',
    'Something romantic',
  ];

  const sendMessage = async (text) => {
    if (!text.trim() || loading) return;
    const userMsg = { role: 'user', content: text };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput('');
    setLoading(true);

    try {
      const history = newMessages.slice(1).map((m) => ({
        role: m.role,
        content: typeof m.content === 'string' ? m.content : m.content.message || '',
      }));

      const res = await aiAPI.chat(text, history);
      const normalized = normalizeAssistantPayload(res?.data || {});
      setMessages([...newMessages, {
        role: 'assistant',
        content: normalized.message,
        recommendations: normalized.recommendations,
      }]);
    } catch (err) {
      const detail = err.response?.data?.message || err.response?.data?.detail || '';
      const status = err.response?.status;
      const friendly = status === 401
        ? 'Please log in to use AI chat recommendations.'
        : detail.includes('quota') || detail.includes('429')
        ? 'The AI service is temporarily unavailable. I\'ll use smart search to help you instead — please try your question again!'
        : 'Sorry, I encountered an error. Please try again.';
      setMessages([...newMessages, {
        role: 'assistant',
        content: friendly,
      }]);
    }
    setLoading(false);
  };

  const getRecommendationRoute = (rec) => {
    const id = rec?.id;
    const yelpId = rec?.yelp_id;
    const looksNumeric = typeof id === 'number' || /^\d+$/.test(String(id || ''));
    if (rec?.source === 'yelp' || yelpId || !looksNumeric) {
      return `/restaurant/yelp/${yelpId || id}`;
    }
    return `/restaurant/${id}`;
  };

  const clearChat = () => {
    const cleared = [
      { role: 'assistant', content: "Chat cleared! How can I help you find your next meal?" },
    ];
    setMessages(cleared);
    localStorage.setItem(activeStorageKey, JSON.stringify(cleared));
  };

  if (!user && !isGuestHomepage) return null;

  const chatbotUI = (
    <>
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-5 right-5 md:bottom-6 md:right-6 bg-gradient-to-r from-yelp-red to-red-500 text-white p-4 rounded-2xl shadow-2xl hover:shadow-red-300/40 hover:-translate-y-0.5 transition-all duration-200 z-[2000] group flex items-center gap-2"
          aria-label="Open AI Assistant"
        >
          <FiMessageCircle size={24} />
          <span className="hidden md:inline text-sm font-semibold pr-1">Ask AI</span>
          <span className="absolute -top-2 -left-2 bg-yellow-400 text-black text-xs font-bold px-2 py-0.5 rounded-full animate-pulse">
            AI
          </span>
        </button>
      )}

      {isOpen && (
        <div className="fixed bottom-4 right-4 left-4 md:left-auto md:bottom-6 md:right-6 w-auto md:w-[26rem] max-w-[calc(100vw-2rem)] h-[72vh] md:h-[38rem] bg-white/95 backdrop-blur-sm rounded-3xl shadow-2xl flex flex-col z-[2000] border border-gray-200 overflow-hidden">
          <div className="bg-gradient-to-r from-yelp-red via-red-500 to-red-600 text-white px-4 py-3.5 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-xl bg-white/20 flex items-center justify-center">
                <FiMessageCircle size={17} />
              </div>
              <div>
                <div className="font-semibold leading-tight">AI Restaurant Assistant</div>
                <div className="text-[11px] text-red-100">Personalized suggestions in seconds</div>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <button onClick={clearChat} className="hover:bg-white/20 p-1.5 rounded-lg transition" title="Clear chat">
                <FiTrash2 size={16} />
              </button>
              <button onClick={() => setIsOpen(false)} className="hover:bg-white/20 p-1.5 rounded-lg transition" aria-label="Close chat">
                <FiX size={18} />
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4 md:p-5 space-y-3 bg-gradient-to-b from-gray-50 to-white chat-messages">
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm shadow-sm ${
                  msg.role === 'user'
                    ? 'bg-gradient-to-r from-yelp-red to-red-500 text-white rounded-br-md'
                    : 'bg-white text-gray-800 border border-gray-200 rounded-bl-md'
                }`}>
                  <p className="whitespace-pre-wrap">{typeof msg.content === 'string' ? msg.content : msg.content}</p>
                  {msg.recommendations?.length > 0 && (
                    <div className="mt-3 space-y-2">
                      {msg.recommendations.map((rec, j) => (
                        <Link
                          key={j}
                          to={getRecommendationRoute(rec)}
                          onClick={() => setIsOpen(false)}
                          className="block bg-white rounded-xl p-3 border border-gray-200 hover:border-yelp-red hover:shadow-md transition text-left"
                        >
                          <div className="font-semibold text-gray-900">{rec.name}</div>
                          <div className="flex items-center gap-2 text-xs text-gray-600 mt-1.5 flex-wrap">
                            <span className="inline-flex items-center bg-amber-50 text-amber-700 border border-amber-200 rounded-full px-2 py-0.5">
                              <FiStar size={10} className="mr-1" /> {rec.rating}
                            </span>
                            {rec.price_range && <span className="bg-gray-100 rounded-full px-2 py-0.5">{rec.price_range}</span>}
                            {rec.cuisine_type && <span className="bg-gray-100 rounded-full px-2 py-0.5">{rec.cuisine_type}</span>}
                          </div>
                          {rec.reason && <div className="text-xs text-gray-500 mt-2 italic">Why this: {rec.reason}</div>}
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-md px-4 py-3 shadow-sm">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {messages.length <= 1 && (
            <div className="px-4 md:px-5 pb-3 flex flex-wrap gap-2">
              {quickActions.map((action) => (
                <button
                  key={action}
                  onClick={() => sendMessage(action)}
                  className="text-xs bg-white text-yelp-red border border-red-200 rounded-full px-3 py-1.5 hover:bg-red-50 hover:border-red-300 transition shadow-sm"
                >
                  {action}
                </button>
              ))}
            </div>
          )}

          <div className="p-3 md:p-4 border-t border-gray-200 bg-white/90 backdrop-blur-sm">
            <form
              onSubmit={(e) => { e.preventDefault(); sendMessage(input); }}
              className="flex items-center space-x-2"
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask for restaurant recommendations..."
                className="flex-1 border border-gray-300 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-yelp-red focus:ring-2 focus:ring-red-100"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={!input.trim() || loading}
                className="bg-gradient-to-r from-yelp-red to-red-500 text-white p-2.5 rounded-xl disabled:opacity-50 hover:brightness-95 transition shadow-sm"
              >
                <FiSend size={16} />
              </button>
            </form>
          </div>
        </div>
      )}
    </>
  );

  if (typeof document === 'undefined') return chatbotUI;
  return createPortal(chatbotUI, document.body);
}
