<picture>
  <source media="(prefers-color-scheme: dark)" srcset="frontend/src/assets/hero.png">
  <img src="frontend/src/assets/hero.png" alt="FlickerX hero" width="100%">
</picture>

# FlickerX

AI chat and file intelligence platform. Chat with AI, upload documents, get structured answers instantly.

## Features

- **Smart Chat** — Ask anything, debug errors, brainstorm workflows with AI
- **File Understanding** — Upload images, code, or documents for analysis
- **Slash Commands** — `/fix`, `/explain`, `/summarize` shortcuts
- **User Auth** — Register / login with JWT-based sessions
- **Model Selection** — Choose from multiple AI models via OpenRouter
- **Dark Mode** — Toggle between light and dark themes

## Tech Stack

| Layer     | Tech                                                   |
| --------- | ------------------------------------------------------ |
| Frontend  | React 19, Vite, Tailwind CSS, React Router, Lucide     |
| Backend   | Express 5, Helmet, CORS, Cookie Parser                 |
| Auth      | JWT, bcryptjs, Refresh Tokens                          |
| AI        | OpenRouter API (multi-model)                           |
| Storage   | Cloudinary (file uploads)                              |
| Validation| Zod                                                    |

## Getting Started

```bash
git clone https://github.com/Joey-1123/FlickerX.git
cd FlickerX
```

**Backend**

```bash
cd backend
cp .env.example .env   # fill in your keys
npm install
npm run dev
```

**Frontend**

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

**Root** (runs both concurrently)

```bash
npm install
npm run dev
```

## Environment Variables

Backend `.env`:

| Variable              | Description                        |
| --------------------- | ---------------------------------- |
| `OPENROUTER_API_KEY`  | API key for OpenRouter AI models   |
| `JWT_SECRET`          | Secret for signing JWT tokens      |
| `CLOUD_NAME`          | Cloudinary cloud name              |
| `CLOUDINARY_API_KEY`  | Cloudinary API key                 |
| `CLOUDINARY_API_SECRET`| Cloudinary API secret             |
| `FRONTEND_ORIGIN`     | CORS allowed origin                |
| `BCRYPT_SALT_ROUNDS`  | bcrypt hash rounds (default 12)    |
| `PORT`                | Server port (default 5000)         |

Frontend `.env`:

| Variable         | Description                |
| ---------------- | -------------------------- |
| `VITE_API_BASE`  | Backend API URL            |

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
│   ├── middleware/      # Rate limiting, auth
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
│   └── public/          # Static assets
└── package.json         # Root workspace scripts
```

## License

ISC
