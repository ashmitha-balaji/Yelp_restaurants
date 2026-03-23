import React, { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { createPortal } from 'react-dom';
import { useAuth } from '../context/AuthContext';
import { aiAPI } from '../services/api';
import { FiMessageCircle, FiX, FiSend, FiTrash2, FiStar } from 'react-icons/fi';

const DEFAULT_WELCOME_MESSAGE = {
  role: 'assistant',
  content: "Hi! I'm your restaurant assistant. Ask me for personalized recommendations based on your preferences!",
};

const getChatStorageKey = (userId) => `chatbot_messages_${userId}`;

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
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([DEFAULT_WELCOME_MESSAGE]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Keep chat isolated per user and reset on user switch/logout.
  useEffect(() => {
    if (!user?.id) {
      setIsOpen(false);
      setMessages([DEFAULT_WELCOME_MESSAGE]);
      return;
    }

    const stored = localStorage.getItem(getChatStorageKey(user.id));
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
  }, [user?.id]);

  useEffect(() => {
    if (!user?.id) return;
    localStorage.setItem(getChatStorageKey(user.id), JSON.stringify(messages));
  }, [user?.id, messages]);

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
      const friendly = detail.includes('quota') || detail.includes('429')
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
    if (user?.id) {
      localStorage.setItem(getChatStorageKey(user.id), JSON.stringify(cleared));
    }
  };

  if (!user) return null;

  const chatbotUI = (
    <>
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 bg-yelp-red text-white p-4 rounded-full shadow-xl hover:bg-yelp-dark transition-all z-[2000] group"
          aria-label="Open AI Assistant"
        >
          <FiMessageCircle size={24} />
          <span className="absolute -top-2 -left-2 bg-yellow-400 text-black text-xs font-bold px-2 py-0.5 rounded-full animate-pulse">
            AI
          </span>
        </button>
      )}

      {isOpen && (
        <div className="fixed bottom-6 right-6 w-96 max-w-[calc(100vw-2rem)] h-[32rem] bg-white rounded-2xl shadow-2xl flex flex-col z-[2000] border border-gray-200">
          <div className="bg-yelp-red text-white px-4 py-3 rounded-t-2xl flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <FiMessageCircle size={20} />
              <span className="font-semibold">AI Restaurant Assistant</span>
            </div>
            <div className="flex items-center space-x-2">
              <button onClick={clearChat} className="hover:bg-red-800 p-1 rounded" title="Clear chat">
                <FiTrash2 size={16} />
              </button>
              <button onClick={() => setIsOpen(false)} className="hover:bg-red-800 p-1 rounded">
                <FiX size={18} />
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-3 chat-messages">
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[80%] rounded-2xl px-4 py-2 text-sm ${
                  msg.role === 'user'
                    ? 'bg-yelp-red text-white rounded-br-md'
                    : 'bg-gray-100 text-gray-800 rounded-bl-md'
                }`}>
                  <p className="whitespace-pre-wrap">{typeof msg.content === 'string' ? msg.content : msg.content}</p>
                  {msg.recommendations?.length > 0 && (
                    <div className="mt-2 space-y-2">
                      {msg.recommendations.map((rec, j) => (
                        <Link
                          key={j}
                          to={getRecommendationRoute(rec)}
                          onClick={() => setIsOpen(false)}
                          className="block bg-white rounded-lg p-2 border border-gray-200 hover:border-yelp-red transition text-left"
                        >
                          <div className="font-medium text-gray-900">{rec.name}</div>
                          <div className="flex items-center space-x-2 text-xs text-gray-600 mt-1">
                            <span className="flex items-center"><FiStar size={10} className="text-yellow-400 mr-0.5" />{rec.rating}</span>
                            {rec.price_range && <span>{rec.price_range}</span>}
                            {rec.cuisine_type && <span>{rec.cuisine_type}</span>}
                          </div>
                          {rec.reason && <div className="text-xs text-gray-500 mt-1 italic">{rec.reason}</div>}
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-2xl rounded-bl-md px-4 py-3">
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
            <div className="px-4 pb-2 flex flex-wrap gap-1">
              {quickActions.map((action) => (
                <button
                  key={action}
                  onClick={() => sendMessage(action)}
                  className="text-xs bg-red-50 text-yelp-red border border-red-200 rounded-full px-3 py-1 hover:bg-red-100 transition"
                >
                  {action}
                </button>
              ))}
            </div>
          )}

          <div className="p-3 border-t border-gray-200">
            <form
              onSubmit={(e) => { e.preventDefault(); sendMessage(input); }}
              className="flex items-center space-x-2"
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask for restaurant recommendations..."
                className="flex-1 border border-gray-300 rounded-full px-4 py-2 text-sm focus:outline-none focus:border-yelp-red"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={!input.trim() || loading}
                className="bg-yelp-red text-white p-2 rounded-full disabled:opacity-50 hover:bg-yelp-dark transition"
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
