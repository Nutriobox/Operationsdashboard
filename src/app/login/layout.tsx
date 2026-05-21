// Login uses the root layout directly — no extra wrapping needed.
// Navbar visibility is handled by NavbarWrapper in the root layout.
export default function LoginLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
