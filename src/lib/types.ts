// Shared TypeScript types for the app.

export type Category = {
  id: string;
  slug: string;
  title: string;
  description: string;
  hero_image_url: string | null;
  created_at: string;
};

export type UserProfile = {
  id: string;
  email: string;
  full_name: string | null;
  segment: 'starter' | 'pro' | 'enterprise';
  preferred_categories: string[];
};

export type DashboardMetric = {
  label: string;
  value: number;
  delta_pct: number;
};

export type TimeseriesPoint = {
  date: string;
  value: number;
};
