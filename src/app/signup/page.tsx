// Public signup is disabled. The 5-6 team users are created manually in
// Supabase Dashboard by an admin. Anyone visiting /signup is sent to /login.
import { redirect } from 'next/navigation';

export default function SignupPage() {
  redirect('/login');
}
