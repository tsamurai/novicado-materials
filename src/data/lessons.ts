export interface Lesson {
  id: string;
  title: string;
  description: string;
  sortOrder: number;
}

export const lessons: Lesson[] = [
  {
    id: "1",
    title: "GitHub, Zed, DeepSeek & Context Optimization",
    description:
      "Set up your AI dev workspace: Zed editor, DeepSeek API, Git/GitHub, and context optimization. Build and publish your first project.",
    sortOrder: 1,
  },
  {
    id: "2",
    title: "Architecture, Design & AI Agent Team",
    description:
      "Act as Product Owner: generate architecture/spec/plan/team docs, design a UI, and assemble an AI agent team to build Phase 1.",
    sortOrder: 2,
  },
  {
    id: "3",
    title: "Deployment & Databases",
    description:
      "Take your project live on fly.io with a Supabase database and Google sign-in.",
    sortOrder: 3,
  },
  {
    id: "4",
    title: "Autonomous AI Agent with Memory",
    description:
      "Build a 24/7 Telegram AI agent with a second-brain wiki that stores and structures everything it learns.",
    sortOrder: 4,
  },
  {
    id: "5",
    title: "AI Marketing Team",
    description:
      "Create an AI marketing team (CMO, SEO, content writer, Telegram publisher) that produces and schedules content automatically.",
    sortOrder: 5,
  },
  {
    id: "6",
    title: "Diploma Project — Product Presentation",
    description:
      "Prepare and deliver your final presentation: AI-generated slides, pitch script, and live demo.",
    sortOrder: 6,
  },
];
