import { useEffect, useState } from "react";
import { supabase } from "../lib/supabase";
import { lessons as localLessons, type Lesson } from "../data/lessons";
import LessonCard from "./LessonCard";

function SkeletonCard() {
  return (
    <div className="animate-pulse rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <div className="mb-3 h-5 w-20 rounded-full bg-gray-200" />
      <div className="mb-2 h-5 w-3/4 rounded bg-gray-200" />
      <div className="h-4 w-full rounded bg-gray-100" />
      <div className="mt-2 h-4 w-2/3 rounded bg-gray-100" />
    </div>
  );
}

export default function LandingPage() {
  const [lessons, setLessons] = useState<Lesson[] | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    async function fetchLessons() {
      const { data, error: fetchError } = await supabase
        .from("lessons")
        .select("id, title, description, sort_order")
        .order("sort_order", { ascending: true });

      if (fetchError || !data || data.length === 0) {
        setError(true);
        setLessons(localLessons);
      } else {
        setLessons(
          data.map((row) => ({
            id: row.id,
            title: row.title,
            description: row.description,
            sortOrder: row.sort_order,
          })),
        );
      }
    }

    fetchLessons().catch(() => {
      setError(true);
      setLessons(localLessons);
    });
  }, []);

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
        {lessons === null ? (
          <>
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </>
        ) : (
          lessons.map((lesson, index) => (
            <LessonCard
              key={lesson.id}
              title={lesson.title}
              description={lesson.description}
              number={index + 1}
            />
          ))
        )}
      </div>

      {error && lessons !== null && (
        <p className="mt-6 text-center text-sm text-amber-700">
          Using local lesson data — could not reach the server.
        </p>
      )}
    </div>
  );
}
