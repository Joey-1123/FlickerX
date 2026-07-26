<p align="center">
  <img src="frontend/public/logo.svg" alt="FlickerX" width="400">
</p>

<p align="center">
  AI chat and file intelligence platform.
  <br>
  Chat with AI, upload documents, get structured answers instantly.
</p>

<p align="center">
  <a href="CODE_OF_CONDUCT.md">Code of Conduct</a> •
  <a href="CONTRIBUTING.md">Contributing</a> •
  <a href="SECURITY.md">Security</a> •
  <a href="LICENSE">License</a>
</p>

---

## Features

| Feature | Description |
| ------- | ----------- |
| **Smart Chat** | Ask anything, debug errors, brainstorm workflows with AI |
| **File Understanding** | Upload images, code, or documents for analysis |
| **Slash Commands** | `/fix`, `/explain`, `/summarize` shortcuts |
| **User Auth** | Register / login with JWT-based sessions |
| **Model Selection** | Choose from multiple AI models via OpenRouter |
| **Dark Mode** | Toggle between light and dark themes |
| **Streaming** | Real-time response streaming with SSE |
| **Rate Limiting** | Configurable per-endpoint rate limits |

## Tech Stack

| Layer     | Tech                                                   |
| --------- | ------------------------------------------------------ |
| Frontend  | React 19, Vite, Tailwind CSS, React Router, Lucide     |
| Backend   | Express 5, Helmet, CORS, Cookie Parser                 |
| Auth      | JWT, bcryptjs, Refresh Tokens                          |
| AI        | OpenRouter API (multi-model with fallbacks)            |
| Storage   | Cloudinary (file uploads)                              |
| Validation| Zod                                                    |

## Quick Start

```bash
git clone https://github.com/Joey-1123/FlickerX.git
cd FlickerX
```

### Backend

```bash
cd backend
cp .env.example .env   # fill in your keys
npm install
npm run dev
```

### Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

### Run Both

```bash
npm install    # root: installs concurrently
npm run dev    # starts both frontend & backend
```

## Environment Variables

### Backend `.env`

| Variable                | Description                          | Default |
| ----------------------- | ------------------------------------ | ------- |
| `OPENROUTER_API_KEY`    | API key for OpenRouter AI models     | — |
| `OPENROUTER_BASE`       | OpenRouter API base URL              | `https://openrouter.ai/api/v1/chat/completions` |
| `OPENROUTER_TIMEOUT_MS` | HTTP request timeout (ms)            | `10000` |
| `OPENROUTER_STREAM_TIMEOUT_MS` | Stream timeout (ms)          | `30000` |
| `JWT_SECRET`            | Secret for signing JWT tokens        | — |
| `JWT_ACCESS_EXPIRES`    | Access token expiry string           | `15m` |
| `JWT_REFRESH_EXPIRES_SECONDS` | Refresh token expiry (seconds)| `2592000` |
| `JWT_ALGORITHM`         | JWT signing algorithm(s)             | `HS256` |
| `RESET_TOKEN_EXPIRES_MS`| Password reset token expiry (ms)    | `3600000` |
| `RATE_LIMIT_CHAT_MAX`   | Chat endpoint max requests per window| `20` |
| `RATE_LIMIT_AUTH_MAX`   | Auth endpoint max requests per window| `10` |
| `RATE_LIMIT_WINDOW_MS`  | Rate limit window (ms)               | `60000` |
| `CLOUD_NAME`            | Cloudinary cloud name                | — |
| `CLOUDINARY_API_KEY`    | Cloudinary API key                   | — |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret                | — |
| `FRONTEND_ORIGIN`       | CORS allowed origin                  | `http://localhost:5173` |
| `BCRYPT_SALT_ROUNDS`    | bcrypt hash rounds                   | `12` |
| `PORT`                  | Server port                          | `5000` |

### Frontend `.env`

| Variable         | Description                | Default |
| ---------------- | -------------------------- | ------- |
| `VITE_API_BASE`  | Backend API URL            | `http://localhost:5000` |

## Scripts

| Command              | Description                  |
| -------------------- | ---------------------------- |
| `npm run dev`        | Start both frontend & backend |
| `npm run backend`    | Start backend only           |
| `npm run frontend`   | Start frontend only          |

## Project Structure

```
FlickerX/
├── backend/
│   ├── config/          # Cloudinary config
│   ├── controllers/     # Route handlers
│   ├── middleware/       # Rate limiting, auth
│   ├── routes/          # Express route definitions
│   └── services/        # Business logic (AI, user, token)
├── frontend/
│   ├── src/
│   │   ├── assets/      # Images, icons
│   │   ├── auth/        # Auth context & hooks
│   │   ├── components/  # Reusable UI components
│   │   ├── context/     # Theme context
│   │   ├── pages/       # Route pages
│   │   ├── services/    # API client functions
│   │   └── utils/       # Helpers (models, sessions)
│   └── public/          # Static assets (logo, favicon)
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── SECURITY.md
├── LICENSE
└── package.json
```

## Security

See [SECURITY.md](SECURITY.md) for our security policy and how to report vulnerabilities.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on commits, PRs, and code style.

## Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md).
By participating, you are expected to uphold this code.

## License

MIT — see [LICENSE](LICENSE) for details.
