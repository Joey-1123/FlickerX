import { SignedIn, SignedOut, SignIn } from "@clerk/clerk-react";

// ProtectedRoute component to guard routes that require authentication
export default function ProtectedRoute({ children }) {
    return (
        <>
            <SignedIn>{children}</SignedIn>

            <SignedOut>
                <div className="flex justify-center items-center h-screen">
                    <SignIn redirectUrl="/chat" />
                </div>
            </SignedOut>
        </>
    );
}