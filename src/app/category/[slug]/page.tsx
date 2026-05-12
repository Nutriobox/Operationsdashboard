export const dynamic = 'force-dynamic';
export const dynamicParams = true;

export function generateStaticParams() {
  return [];
}

export default function CategoryPage({ params }: { params: { slug: string } }) {
  return (
    <div>
      <h1>Category: {params.slug}</h1>
    </div>
  );
}
