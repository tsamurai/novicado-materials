import { lessons } from "../data/lessons";
import LessonCard from "./LessonCard";

export default function LandingPage() {
  return (
    <div>
      <div className="mb-10 text-center">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
          Welcome to Novicado
        </h1>
        <p className="mt-3 text-lg text-gray-600">
          AI School lesson materials — access your course content in one place.
        </p>
      </div>

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {lessons.map((lesson, index) => (
          <LessonCard
            key={lesson.id}
            title={lesson.title}
            description={lesson.description}
            number={index + 1}
          />
        ))}
      </div>
    </div>
  );
}
