import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <h1 className="text-6xl font-bold text-gray-300">404</h1>
      <p className="mt-4 text-lg text-gray-600">Page not found</p>
      <p className="mt-1 text-sm text-gray-500">
        The page you're looking for doesn't exist.
      </p>
      <Link
        to="/"
        className="mt-6 inline-flex items-center gap-1 text-sm font-medium text-blue-600 hover:text-blue-700"
      >
        &larr; Back to all lessons
      </Link>
    </div>
  );
}
