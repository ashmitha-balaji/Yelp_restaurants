# MongoDB collections (Lab 2)

| Collection | Purpose |
|------------|---------|
| `sessions` | Server-side session records on login: `user_id`, `token_fingerprint`, `created_at`, `expires_at`. |
| `review_jobs` | Async review pipeline: `job_id`, `status` (`queued` / `completed` / `error`), `review_id`, `payload`, timestamps. |

**Future / full migration (optional):** mirror MySQL entities as `users`, `restaurants`, `reviews`, `favourites`, `photos`, `activity_logs` documents — see [../migrations/mysql_to_mongo.py](../migrations/mysql_to_mongo.py).

Passwords remain **bcrypt hashes** in MySQL until full cutover; the migration script copies `password_hash` as-is.
