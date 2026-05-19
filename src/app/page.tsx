// Landing page - full-bleed Nutriobox storefront photo as the hero.
// The image lives at public/nutriobox-storefront.jpg.
export default function HomePage() {
  return (
    <div
      style={{
        height: 'calc(100vh - 3.5rem)',
        backgroundImage: "url('/nutriobox-storefront.webp')",
        backgroundColor: '#1a1a1a',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat'
      }}
    />
  );
}
