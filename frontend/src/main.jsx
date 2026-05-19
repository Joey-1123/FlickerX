import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import "./index.css";
import "./App.css";
import { ClerkProvider } from "@clerk/clerk-react";

// Get the Clerk publishable key from environment variables
const PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

// Render the app wrapped with ClerkProvider for authentication
ReactDOM.createRoot(document.getElementById("root")).render(
  // Provide Clerk authentication context to the entire app
  <ClerkProvider
    publishableKey={PUBLISHABLE_KEY}
    afterSignInUrl="/chat"
    afterSignUpUrl="/chat">
    <App />
  </ClerkProvider>
);
