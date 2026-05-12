-- Run this in Supabase → SQL Editor to set up the database.

-- 1. Profiles (extends auth.users)
create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text not null,
  full_name text,
  segment text not null default 'starter' check (segment in ('starter','pro','enterprise')),
  preferred_categories text[] not null default '{}',
  created_at timestamptz not null default now()
);

-- 2. Categories
create table if not exists public.categories (
  id uuid primary key default gen_random_uuid(),
  slug text unique not null,
  title text not null,
  description text,
  hero_image_url text,
  created_at timestamptz not null default now()
);

-- 3. Row Level Security
alter table public.profiles enable row level security;
alter table public.categories enable row level security;

-- Profiles: each user can read/update their own row.
create policy "profiles_self_read" on public.profiles
  for select using (auth.uid() = id);

create policy "profiles_self_update" on public.profiles
  for update using (auth.uid() = id);

create policy "profiles_self_insert" on public.profiles
  for insert with check (auth.uid() = id);

-- Categories: world-readable, only authed users can write (tighten as needed).
create policy "categories_public_read" on public.categories
  for select using (true);

create policy "categories_authed_write" on public.categories
  for insert with check (auth.role() = 'authenticated');

-- 4. Seed sample categories
insert into public.categories (slug, title, description) values
  ('nutrition-plans', 'Nutrition Plans', 'Tailored meal plans based on dietary goals.'),
  ('reports', 'Reports', 'Weekly and monthly insight reports for your team.'),
  ('coaching', 'Coaching', 'Personalized coaching journeys built on your data.')
on conflict (slug) do nothing;
