"use client";

export function CardSkeleton() {
  return (
    <div className="card p-4">
      <div className="mx-auto mb-3 h-16 w-16 rounded-full skeleton" />
      <div className="mx-auto mb-2 h-4 w-24 skeleton" />
      <div className="mx-auto mb-2 h-3 w-32 skeleton" />
      <div className="mx-auto h-3 w-16 skeleton" />
    </div>
  );
}

export function SceneCardSkeleton() {
  return (
    <div className="card overflow-hidden p-0">
      <div className="h-32 skeleton rounded-none" />
      <div className="p-3">
        <div className="mb-2 h-3 w-3/4 skeleton" />
        <div className="mb-2 h-3 w-1/2 skeleton" />
        <div className="h-3 w-1/4 skeleton" />
      </div>
    </div>
  );
}

export function ListSkeleton({ count = 4 }: { count?: number }) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
      {Array.from({ length: count }).map((_, i) => (
        <CardSkeleton key={i} />
      ))}
    </div>
  );
}
