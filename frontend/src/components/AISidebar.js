import React, { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { aiAPI } from '../services/api';
import { FiSend, FiTrash2, FiStar, FiChevronLeft, FiChevronRight } from 'react-icons/fi';

const QUICK_ACTIONS = ['Find dinner tonight', 'Best rated near me', 'Vegan options', 'Something romantic'];

export default function AISidebar({ collapsed, onToggle }) {
  const { user } = useAuth();
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Ask for restaurant recommendations! Try:' },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (text) => {
    if (!text?.trim() || loading) return;
    const msg = text.trim();
    const userMsg = { role: 'user', content: msg };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput('');
    setLoading(true);

    try {
      const history = newMessages.slice(1).map((m) => ({
        role: m.role,
        content: typeof m.content === 'string' ? m.content : m.content?.message || '',
      }));
      const res = await aiAPI.chat(msg, history);
      setMessages([...newMessages, {
        role: 'assistant',
        content: res.data.message,
        recommendations: res.data.recommendations || [],
      }]);
    } catch (err) {
      const detail = err.response?.data?.message || err.response?.data?.detail || '';
      const friendly = detail.includes('quota') || detail.includes('429')
        ? 'AI service is temporarily unavailable. Try your question again — I\'ll use smart search!'
        : 'Sorry, something went wrong. Please try again.';
      setMessages([...newMessages, {
        role: 'assistant',
        content: friendly,
      }]);
    }
    setLoading(false);
  };

  const clearChat = () => {
    setMessages([{ role: 'assistant', content: 'Ask for restaurant recommendations! Try:' }]);
  };

  if (!user) return null;

  return (
    <div className={`bg-white border-l border-gray-200 flex flex-col transition-all duration-300 ${collapsed ? 'w-12' : 'w-80 md:w-96'}`}>
      {/* Header - always visible */}
      <button
        onClick={onToggle}
        className="flex items-center justify-between w-full px-4 py-3 border-b border-gray-200 hover:bg-gray-50 transition"
      >
        {!collapsed && <span className="font-semibold text-gray-800 truncate">🤖 AI Assistant</span>}
        {collapsed ? (
          <span className="mx-auto text-lg">🤖</span>
        ) : (
          <FiChevronRight size={18} className="text-gray-500 shrink-0" />
        )}
      </button>

      {!collapsed && (
        <>
          <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-0 chat-messages">
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[90%] rounded-xl px-3 py-2 text-sm ${
                  msg.role === 'user' ? 'bg-yelp-red text-white' : 'bg-gray-100 text-gray-800'
                }`}>
                  <p className="whitespace-pre-wrap">{typeof msg.content === 'string' ? msg.content : msg.content}</p>
                  {msg.recommendations?.length > 0 && (
                    <div className="mt-2 space-y-2">
                      {msg.recommendations.map((rec, j) => (
                        <Link
                          key={j}
                          to={`/restaurant/${rec.id}`}
                          className="block bg-white rounded-lg p-2 border border-gray-200 hover:border-yelp-red text-left"
                        >
                          <div className="font-medium text-gray-900 text-xs">{rec.name}</div>
                          <div className="flex items-center gap-2 text-xs text-gray-500 mt-0.5">
                            <span className="flex items-center"><FiStar size={10} className="text-yellow-400" />{rec.rating}</span>
                            {rec.price_range && <span>{rec.price_range}</span>}
                          </div>
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-xl px-3 py-2 flex gap-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '100ms' }} />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '200ms' }} />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {messages.length <= 1 && (
            <div className="px-4 pb-2 flex flex-wrap gap-1">
              {QUICK_ACTIONS.map((action) => (
                <button
                  key={action}
                  onClick={() => sendMessage(action)}
                  className="text-xs bg-gray-100 text-gray-700 rounded-full px-3 py-1.5 hover:bg-gray-200 transition"
                >
                  {action}
                </button>
              ))}
            </div>
          )}

          <div className="p-3 border-t border-gray-200">
            <form onSubmit={(e) => { e.preventDefault(); sendMessage(input); }} className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="e.g. I'm looking for a place for dinner"
                className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-yelp-red"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={!input.trim() || loading}
                className="bg-yelp-red text-white px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50 hover:bg-yelp-dark"
              >
                Send
              </button>
            </form>
            <button onClick={clearChat} className="text-xs text-gray-500 hover:text-yelp-red mt-2">
              Clear chat
            </button>
          </div>
        </>
      )}
    </div>
  );
}
