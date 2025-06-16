import React from "react";
import { Link } from "react-router-dom";

const NotFoundPage: React.FC = () => {
    return (
        <div className="flex flex-col items-center justify-center h-full text-center px-6 py-12 bg-gray-900 text-white">
            <div className="bg-gray-800/70 backdrop-blur-sm p-8 md:p-12 rounded-xl shadow-xl max-w-md w-full">
                <h1 className="text-6xl md:text-8xl font-extrabold text-indigo-400 mb-4">
                    404
                </h1>
                <h2 className="text-2xl md:text-3xl font-semibold mb-3 text-white">
                    Page Not Found
                </h2>
                <p className="text-gray-300 mb-8 text-sm md:text-base">
                    Oops! The page you're looking for doesn't seem to exist.
                </p>
                <Link
                    to="/"
                    className="inline-block px-6 py-3 text-base font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900 focus:ring-indigo-500 transition-colors duration-200"
                >
                    Go to Homepage
                </Link>
            </div>
        </div>
    );
};

export default NotFoundPage;
