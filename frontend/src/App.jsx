import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import Chat from "./pages/Chat";
import Working from "./pages/Working";
import About from "./pages/About";
import Contact from "./pages/Contact";
import ProtectedRoute from "./components/ProtectedRoute";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} /> {/* Home page */}

        {/* lets understand working */}
        <Route path="/working" element={<Working />} />

        {/* Protected chat page */}
        <Route
          path="/chat"
          element={
            // Only render Chat if user is authenticated, otherwise redirect to Home
            <ProtectedRoute>
              <Chat />
            </ProtectedRoute>
          }
        />
        {/* Additional routes for about and contact pages */}
        <Route path="/about" element={<About />} />
        <Route path="/contact" element={<Contact />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;