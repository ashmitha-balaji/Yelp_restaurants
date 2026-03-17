import { useState } from 'react';

export default function ReviewForm({
  initialRating = 0,
  initialComment = '',
  onSubmit,
  onCancel,
}) {
  const [rating, setRating] = useState(initialRating);
  const [comment, setComment] = useState(initialComment);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (rating < 1 || rating > 5) {
      setError('Please select a rating 1-5');
      return;
    }
    try {
      await onSubmit(rating, comment);
    } catch (err) {
      setError(err.response?.data?.detail ?? 'Failed to save review');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="p-4 bg-gray-50 rounded-lg mb-4">
      <label className="block mb-2">
        <span className="font-medium text-gray-700">Rating</span>
        <div className="flex gap-1 mt-1">
          {[1, 2, 3, 4, 5].map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setRating(s)}
              className={`w-10 h-10 rounded-full border-2 transition ${
                rating >= s
                  ? 'bg-yellow-400 border-yellow-500 text-gray-900'
                  : 'border-gray-300 hover:border-yellow-400'
              }`}
            >
              ★
            </button>
          ))}
        </div>
      </label>
      <label className="block mb-2">
        <span className="font-medium text-gray-700">Comment</span>
        <textarea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          rows={3}
          className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yelp-red focus:border-transparent"
          placeholder="Share your experience..."
        />
      </label>
      {error && <p className="text-red-600 text-sm mb-2">{error}</p>}
      <div className="flex gap-2">
        <button
          type="submit"
          className="px-4 py-2 bg-yelp-red text-white rounded-lg hover:bg-yelp-dark transition"
        >
          Submit
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-100 transition"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
