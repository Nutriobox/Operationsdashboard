// Extract a clean first name from a full name or email.
//   "Mayank Rawat"          -> "Mayank"
//   "mayank@nutriobox.com"  -> "Mayank"
//   null / undefined        -> "there"
export function firstName(value: string | null | undefined): string {
  if (!value) return 'there';
  const trimmed = value.trim();
  if (!trimmed) return 'there';

  if (trimmed.includes('@')) {
    const local = trimmed.split('@')[0].split(/[._+\-]/)[0];
    return local.charAt(0).toUpperCase() + local.slice(1).toLowerCase();
  }

  const first = trimmed.split(/\s+/)[0];
  return first.charAt(0).toUpperCase() + first.slice(1);
}
