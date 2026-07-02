# How to Build Your First AI Project with the Novicado Stack (Zed, DeepSeek, GitHub, fly.io, Supabase)

You've been watching AI tutorials for weeks. You've bookmarked a dozen "build an AI app in 10 minutes" videos. But when you sit down to actually build something real, you freeze.

I've been there. That's exactly why I built Novicado Materials — to give developers like you a clear, project-based path from tutorial paralysis to a deployed AI project you can show off.

In this guide, I'll walk you through building your first AI project using the exact same stack I teach in the Novicado curriculum: **Zed, DeepSeek, GitHub, fly.io, and Supabase**. By the time you finish reading, you'll understand how each tool fits together, and you'll have a blueprint for your own project.

Let's build something real.

## Why This Stack? A Quick Tour of the Novicado Tools

Before we dive into code, let me explain why I chose each tool in this stack. When you're trying to **learn AI coding for beginners**, the last thing you need is a dozen complex tools fighting each other.

### Zed: The AI-First Editor

Zed is a code editor built from the ground up for AI-assisted development. Unlike VS Code, which added AI features as an afterthought, Zed has AI baked into its DNA. You get inline completions, natural language commands, and seamless integration with models like DeepSeek.

**Why I chose it:** It's fast, free, and designed for the way we build in 2025 — with AI as a pair programmer, not a separate tool.

### DeepSeek: Your Coding Copilot

DeepSeek is a powerful open-source AI model that excels at code generation and reasoning. It's one of the best **AI development tools 2025** has to offer, and it's surprisingly affordable compared to alternatives.

**Why I chose it:** DeepSeek understands context deeply. When you're building your first project, having an AI that can explain its reasoning as well as generate code is invaluable.

### GitHub: Version Control and Portfolio

GitHub is non-negotiable for any developer. But in the Novicado stack, it serves double duty: version control for your project and a living portfolio of your work.

**Why I chose it:** Your **AI project portfolio** matters more than your resume. Every project you push to GitHub becomes proof of what you can build.

### fly.io: Free Hosting That Scales

fly.io offers a generous free tier that lets you **deploy full stack app free** — no credit card required for most use cases. It runs your app on servers close to your users, and it handles Docker containers effortlessly.

**Why I chose it:** Most tutorials stop at "here's how to code it." fly.io lets you actually ship your project to the world without paying a dime.

### Supabase: The Open Source Firebase

Supabase gives you a PostgreSQL database, authentication, real-time subscriptions, and storage — all in one platform. It's the perfect backend for AI projects that need user accounts and data persistence.

**Why I chose it:** It's free to start, uses SQL you already know (or can learn easily), and scales with you. Plus, their **Supabase tutorial** documentation is some of the best in the industry.

## The Project: An AI-Powered Study Buddy

For this walkthrough, we'll build a simple but complete project: an AI study buddy that helps you understand code snippets. Users paste in a piece of code, and the app uses DeepSeek to explain it in plain English.

This project touches every part of the stack and gives you a real, deployable app you can add to your portfolio.

### Step 1: Set Up Your Development Environment with Zed

First, download and install [Zed](https://zed.dev). Once it's open, create a new project folder:

```bash
mkdir ai-study-buddy
cd ai-study-buddy
```

Zed's AI features work out of the box. Press `Cmd+I` to open the AI assistant, and you can start asking questions about your code immediately. For this project, we'll use DeepSeek as our model.

**Pro tip:** In Zed's settings, configure DeepSeek as your default AI provider. You'll get faster responses and better code generation than general-purpose models.

### Step 2: Scaffold Your Project with DeepSeek

Here's where the magic happens. Instead of writing every line from scratch, we'll use DeepSeek to scaffold our project. In Zed's AI panel, type:

```
Create a Next.js project structure for an AI study buddy app. Include:
- A landing page with a code input form
- An API route that calls DeepSeek to explain code
- A results display component
- Tailwind CSS for styling
```

DeepSeek will generate the entire project structure. Accept the suggestions, and within minutes you'll have a working skeleton.

**Why this matters:** This is the **project based learning coding** approach that actually works. You're not copying code blindly — you're reviewing, understanding, and customizing AI-generated code. That's how you learn to build with AI.

### Step 3: Set Up Your Database with Supabase

Head to [Supabase](https://supabase.com) and create a new project. Once it's ready, you'll need to set up a table to store user queries and explanations.

In the SQL editor, run:

```sql
CREATE TABLE explanations (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  code_snippet TEXT NOT NULL,
  explanation TEXT NOT NULL,
  language TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

This table stores every code snippet and its explanation. Later, you can add user authentication to tie explanations to specific users.

**Pro tip:** Supabase's Row Level Security (RLS) lets you control who can read and write data. For your first project, start with public read access and authenticated write access.

### Step 4: Build the Backend API

Create an API route that connects to DeepSeek and stores results in Supabase. Here's a simplified version:

```javascript
// pages/api/explain.js
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL,
  process.env.SUPABASE_SERVICE_KEY
)

export default async function handler(req, res) {
  const { code } = req.body
  
  // Call DeepSeek API
  const response = await fetch('https://api.deepseek.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.DEEPSEEK_API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model: 'deepseek-coder',
      messages: [
        { role: 'system', content: 'You explain code simply.' },
        { role: 'user', content: `Explain this code: ${code}` }
      ]
    })
  })
  
  const data = await response.json()
  const explanation = data.choices[0].message.content
  
  // Store in Supabase
  await supabase.from('explanations').insert({
    code_snippet: code,
    explanation: explanation
  })
  
  res.status(200).json({ explanation })
}
```

This is a **DeepSeek coding** example that shows how to integrate AI into a real application. Notice how simple the integration is — just a single API call.

### Step 5: Build the Frontend

Create a simple React component that lets users paste code and see explanations:

```jsx
// components/CodeExplainer.js
import { useState } from 'react'

export default function CodeExplainer() {
  const [code, setCode] = useState('')
  const [explanation, setExplanation] = useState('')
  const [loading, setLoading] = useState(false)

  const handleExplain = async () => {
    setLoading(true)
    const res = await fetch('/api/explain', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code })
    })
    const data = await res.json()
    setExplanation(data.explanation)
    setLoading(false)
  }

  return (
    <div className="max-w-2xl mx-auto p-8">
      <h1 className="text-3xl font-bold mb-6">AI Study Buddy</h1>
      <textarea
        className="w-full h-48 p-4 border rounded-lg font-mono"
        placeholder="Paste your code here..."
        value={code}
        onChange={(e) => setCode(e.target.value)}
      />
      <button
        className="mt-4 bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
        onClick={handleExplain}
        disabled={loading}
      >
        {loading ? 'Explaining...' : 'Explain This Code'}
      </button>
      {explanation && (
        <div className="mt-8 p-6 bg-gray-50 rounded-lg">
          <h2 className="text-xl font-semibold mb-4">Explanation</h2>
          <p className="text-gray-700">{explanation}</p>
        </div>
      )}
    </div>
  )
}
```

### Step 6: Deploy to fly.io

Now for the rewarding part — deploying your app to the world. First, install the fly.io CLI:

```bash
curl -L https://fly.io/install.sh | sh
```

Then launch your app:

```bash
fly launch
```

Follow the prompts to set up your app name and region. fly.io will detect your Next.js app and create a Dockerfile automatically.

Set your environment variables:

```bash
fly secrets set DEEPSEEK_API_KEY=your_key_here
fly secrets set SUPABASE_URL=your_supabase_url
fly secrets set SUPABASE_SERVICE_KEY=your_service_key
```

Finally, deploy:

```bash
fly deploy
```

Within minutes, your app will be live at `https://your-app-name.fly.dev`. You've just deployed a full-stack AI application for free.

### Step 7: Push to GitHub and Build Your Portfolio

Initialize your Git repository and push to GitHub:

```bash
git init
git add .
git commit -m "Initial commit: AI Study Buddy"
git remote add origin https://github.com/yourusername/ai-study-buddy.git
git push -u origin main
```

Now you have a **student project showcase** piece you can share with potential employers. Add a detailed README explaining what you built, the tech stack you used, and a link to the live demo.

## What You've Learned

In this single project, you've touched on every major concept from the Novicado curriculum:

- **Lesson 1:** Setting up your development environment with Zed
- **Lesson 2:** Using AI (DeepSeek) to scaffold and generate code
- **Lesson 3:** Building a backend API and connecting to a database
- **Lesson 4:** Deploying a production application
- **Lesson 5:** Version control and portfolio building
- **Lesson 6:** Authentication and user management (add this next!)

This is the **learn AI development course** approach that actually works — building real projects, not just following along with videos.

## Why Project-Based Learning Works

The biggest mistake beginners make is consuming tutorials passively. They watch hours of content, copy code verbatim, and end up with nothing they can call their own.

Project-based learning coding flips that script. When you build this AI study buddy:

- You make decisions about architecture
- You debug real issues
- You understand why each tool exists
- You create something uniquely yours

This is the same approach I use in the full Novicado curriculum. Over six lessons, you'll build six projects, each one adding new skills and tools to your repertoire.

## Next Steps: From This Project to Your AI Developer Career

You've built your first AI project. Now what?

1. **Add authentication** — Use Supabase Auth to let users save their favorite explanations
2. **Add history** — Show users their past queries and explanations
3. **Improve the UI** — Add syntax highlighting and better error handling
4. **Share it** — Post your project on Twitter with #buildinpublic

Each of these improvements teaches you something new. And when you're ready to go deeper, the full Novicado curriculum covers everything from **AI agent tutorial** basics to advanced deployment patterns.

## The Full Learning Path

This guide gives you a taste of what's possible, but it's just the beginning. The complete Novicado Materials curriculum is a 6-lesson program that takes you from zero to deployed AI developer:

- **Lesson 1:** Your AI Development Environment (Zed + DeepSeek)
- **Lesson 2:** Building with AI Assistance
- **Lesson 3:** Databases and Backend Architecture (Supabase)
- **Lesson 4:** AI Agents and Automation
- **Lesson 5:** Deployment and DevOps (fly.io + GitHub)
- **Lesson 6:** Portfolio Building and Career Launch

Each lesson includes video walkthroughs, written guides, starter templates, and real projects you'll build and deploy.

## Ready to Build Your AI Developer Career?

You've seen how the Novicado stack works. You've built a real project. Now it's time to go all in.

The AI industry is growing faster than any other tech sector. Companies are desperate for developers who can build with AI tools — and the best way to learn is by doing.

**Sign in now to access the full Novicado Materials curriculum.** You'll get:

- Complete 6-lesson course with video and written content
- Starter templates for every project
- Community access to ask questions and share your work
- Lifetime updates as the AI landscape evolves

Don't let another tutorial pass you by. Build something real. Start your AI developer journey today.

[Sign In to Access Full Materials →]