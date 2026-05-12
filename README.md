# Nutriobox Web

A Next.js 14 + TypeScript + Tailwind CSS starter wired to Supabase for
auth, database, and storage. Includes a landing page, login/signup, a
per-user dashboard with a Recharts line chart, dynamic category pages,
and JSON API routes for both the dashboard and category collections.

## Project layout

```
nutriobox-web/
├── package.json
├── tsconfig.json
├── next.config.js
├── tailwind.config.ts
├── postcss.config.js
├── .env.example
├── supabase/
│   └── schema.sql          # run this once in Supabase SQL editor
└── src/
    ├── middleware.ts        # protects /dashboard routes
    ├── app/
    │   ├── layout.tsx
    │   ├── globals.css
    │   ├── page.tsx                       # landing page
    │   ├── login/page.tsx
    │   ├── signup/page.tsx
    │   ├── dashboard/page.tsx             # per-user dashboard
    │   ├── category/[slug]/page.tsx       # dynamic category pages
    │   └── api/
    │       ├── categories/route.ts        # GET list / POST create
    │       ├── dashboard/route.ts         # GET personalized metrics
    │       └── auth/logout/route.ts
    ├── components/
    │   ├── Navbar.tsx
    │   ├── LogoutButton.tsx
    │   └── DashboardChart.tsx
    └── lib/
        ├── supabase/client.ts             # browser client
        ├── supabase/server.ts             # server client
        └── types.ts
```

## Setup

### 1. Install dependencies

```bash
npm install
```

### 2. Create a Supabase project

1. Go to <https://supabase.com>, create a project.
2. In **SQL Editor**, paste the contents of `supabase/schema.sql` and run it. That creates the `profiles` and `categories` tables, RLS policies, and three seed categories.
3. In **Project Settings → API**, copy your `Project URL` and `anon public` key.

### 3. Configure environment variables

Copy `.env.example` to `.env.local` and fill in:

```
NEXT_PUBLIC_SUPABASE_URL=https://YOUR-PROJECT.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...    # only needed for admin server scripts
```

### 4. Run the dev server

```bash
npm run dev
```

Open <http://localhost:3000>. You can:

- Visit `/` to see the landing page with seeded categories.
- Visit `/signup` to create an account.
- After login you'll be redirected to `/dashboard`.
- Click any category card to hit `/category/[slug]`.

## What's already wired

- **Auth**: email/password via Supabase; signup also creates a row in `profiles`.
- **Route protection**: `src/middleware.ts` redirects unauthenticated visitors away from `/dashboard`.
- **Per-user personalization**: dashboard and category pages read `profiles.segment` and `profiles.preferred_categories` to customize content.
- **API layer**: `GET /api/categories`, `POST /api/categories`, `GET /api/dashboard`, `POST /api/auth/logout`.
- **Charts**: Recharts is preinstalled; the dashboard uses a responsive line chart you can swap data into.

## Next steps

1. Add real data sources behind `/api/dashboard` (replace the demo metrics with `supabase.from(...).select(...)` against your real tables).
2. Build an admin panel to create/edit categories using `POST /api/categories`.
3. Wire up a `preferred_categories` editor in the dashboard so users can pick what they care about.
4. Deploy to Vercel and add your Supabase env vars in the Vercel dashboard.

## Stack

- **Frontend**: Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS
- **Backend**: Next.js Route Handlers (Node.js) + Supabase (PostgreSQL, Auth, Storage)
- **Charts**: Recharts
- **Deploy**: Vercel (recommended) + Supabase cloud
