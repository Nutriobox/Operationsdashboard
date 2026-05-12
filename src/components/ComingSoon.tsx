export default function ComingSoon({ label }: { label: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white">
      <div className="flex flex-col items-center justify-center py-32 text-center">
        <div className="w-16 h-16 rounded-full bg-brand-light flex items-center justify-center mb-4">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="w-8 h-8 text-brand"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12 16 14" />
          </svg>
        </div>
        <h3 className="text-xl font-semibold text-slate-900">{label}</h3>
        <p className="mt-2 text-slate-500 max-w-md">
          This dashboard is coming soon. Tell Claude what you'd like here and we'll wire it up next.
        </p>
      </div>
    </div>
  );
}
