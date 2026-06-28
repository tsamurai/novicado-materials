interface LessonCardProps {
  title: string;
  description: string;
  number: number;
}

export default function LessonCard({ title, description, number }: LessonCardProps) {
  return (
    <div className="group rounded-xl border border-gray-200 bg-white p-6 shadow-sm transition-shadow hover:shadow-md">
      <span className="mb-3 inline-block rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold tracking-wide text-blue-700">
        Lesson {number}
      </span>
      <h2 className="mb-2 text-lg font-semibold leading-snug text-gray-900">
        {title}
      </h2>
      <p className="text-sm leading-relaxed text-gray-600">{description}</p>
    </div>
  );
}
