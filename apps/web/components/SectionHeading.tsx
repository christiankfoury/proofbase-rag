export function SectionHeading({
  title,
  description,
  className = "",
}: {
  title: string;
  description?: string;
  className?: string;
}) {
  return (
    <div className={`mb-3 ${className}`}>
      <h3 className="text-xl font-semibold text-ink">{title}</h3>
      {description ? <p className="mt-1 text-sm text-stone-600">{description}</p> : null}
    </div>
  );
}
