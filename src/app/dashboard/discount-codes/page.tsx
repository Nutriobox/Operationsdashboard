// Discount Codes — same iframe-embed pattern as Sales Item Dashboard.
export default function DiscountCodesPage() {
  return (
    <div className="mx-auto max-w-6xl px-4 pb-10">
      <div className="rounded-lg border border-slate-200 bg-white overflow-hidden shadow-sm">
        <iframe
          src="/discount-codes.html"
          title="Discount Codes"
          className="block w-full border-0 bg-white"
          style={{ height: 'calc(100vh - 220px)', minHeight: '720px' }}
        />
      </div>
    </div>
  );
}
