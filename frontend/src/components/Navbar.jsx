import { Link } from "react-router-dom";
import {
    SignedIn,
    SignedOut,
    SignInButton,
    SignUpButton,
    UserButton,
} from "@clerk/clerk-react";
import {
    Sparkles,
    Home,
    Info,
    Phone,
    LogIn,
    UserPlus,
    LayoutDashboard,
    Trash2
} from "lucide-react";

// Navbar component with Clerk authentication integration
export default function ChatNavbar({ clearChat }) {
    return (
        <nav className="sticky top-0 z-50 bg-white/70 backdrop-blur-xl border-b border-gray-200/50 px-6 py-4 flex items-center justify-between shadow-sm">
            {/* Logo */}
            <div className="flex items-center gap-3 select-none">
                <div className="h-8 w-8 rounded-xl bg-blue-600 flex items-center justify-center text-white font-bold shadow-sm">
                    F
                </div>
                <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                    FlickerX
                    <Sparkles className="h-4 w-4 text-blue-500 animate-pulse" />
                </h1>
            </div>

            {/* Center Links */}
            <div className="hidden md:flex items-center gap-8 text-sm font-medium text-gray-600">
                <Link
                    to="/about"
                    className="flex items-center gap-2 hover:text-blue-600 transition-all duration-300 group"
                >
                    <Info className="h-4 w-4 group-hover:text-blue-600 text-gray-400" />
                    About
                </Link>
                <Link
                    to="/contact"
                    className="flex items-center gap-2 hover:text-blue-600 transition-all duration-300 group"
                >
                    <Phone className="h-4 w-4 group-hover:text-blue-600 text-gray-400" />
                    Contact
                </Link>
            </div>

            {/* Right Side */}
            <div className="flex items-center gap-4">
                {/* When NOT logged in */}
                <SignedOut>
                    <SignInButton mode="modal">
                        <button className="px-4 py-2 text-sm font-medium rounded-xl border border-gray-300 bg-white/80 text-gray-700 hover:bg-gray-50 hover:text-gray-900 transition-all duration-300 flex items-center gap-2 shadow-sm">
                            <LogIn className="h-4 w-4" />
                            Login
                        </button>
                    </SignInButton>

                    <SignUpButton mode="modal">
                        <button className="px-4 py-2 text-sm font-medium rounded-xl bg-blue-600 text-white hover:bg-blue-700 transition-all duration-300 flex items-center gap-2 shadow-sm">
                            <UserPlus className="h-4 w-4" />
                            Sign Up
                        </button>
                    </SignUpButton>
                </SignedOut>
                <button
                    onClick={clearChat}
                    className="text-xs px-3.5 py-2 rounded-xl border border-red-200 bg-red-50/70 text-red-600 hover:bg-red-50 hover:text-red-700 transition-all duration-200 flex items-center gap-2 shadow-sm font-medium"
                >
                    <Trash2 className="h-4 w-4" />
                    Clear Chat
                </button>

                {/* When logged in */}
                <SignedIn>
                    <div className="flex items-center gap-4">

                        <div className="ring-2 ring-blue-500/20 rounded-full p-0.5 bg-white">
                            <UserButton afterSignOutUrl="/" />
                        </div>
                    </div>
                </SignedIn>
            </div>
        </nav>
    );
}