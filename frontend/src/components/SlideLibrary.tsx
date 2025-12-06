import type { FormEvent } from "react";
import { useCallback, useEffect, useRef, useState } from "react";

import {
  ingestSlide,
  listSlides,
  searchSlides,
  slideDownloadUrl,
  slidePreviewUrl,
  type SlideLibraryMetadata,
} from "@/lib/api";
import { Button } from "./ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "./ui/card";
import { Input } from "./ui/input";

type SlideItem = {
  id: string;
  description: string;
  subtitle: string;
  updated: string;
  preview?: string | null;
  downloadUrl: string;
};

const FALLBACK_PREVIEW = "https://placehold.co/640x360?text=Slide";

function formatDate(value?: string) {
  if (!value) return "Unknown";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString();
}

function toViewModel(meta: SlideLibraryMetadata): SlideItem {
  return {
    id: meta.slide_id || meta.file_hash,
    description: meta.description || "Slide",
    subtitle: meta.source_presentation
      ? `${meta.source_presentation} · #${(meta.slide_index ?? 0) + 1}`
      : `Slide #${(meta.slide_index ?? 0) + 1}`,
    updated: formatDate(meta.updated_at),
    preview: meta.preview
      ? slidePreviewUrl(meta.slide_id || meta.file_hash)
      : FALLBACK_PREVIEW,
    downloadUrl: slideDownloadUrl(meta.slide_id || meta.file_hash),
  };
}

export function SlideLibrary() {
  const [query, setQuery] = useState("");
  const [slides, setSlides] = useState<SlideItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const fetchSlides = useCallback(async (text: string) => {
    setLoading(true);
    setError(null);
    try {
      if (text.trim()) {
        const results = await searchSlides(text);
        setSlides(results.map(toViewModel));
      } else {
        const { items } = await listSlides({ skip: 0, limit: 50 });
        setSlides(items.map(toViewModel));
      }
    } catch (err) {
      setSlides([]);
      setError(err instanceof Error ? err.message : "Failed to fetch slides");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSlides("");
  }, [fetchSlides]);

  const handleSearch = async (event: FormEvent) => {
    event.preventDefault();
    await fetchSlides(query);
  };

  const handleUpload = async (file?: File | null) => {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      await ingestSlide(file);
      await fetchSlides(query);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    <Card className="h-full">
      <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <CardTitle className="text-2xl">Slide Library</CardTitle>
          <CardDescription>
            Browse, search, and import your slides.
          </CardDescription>
        </div>
        <div className="flex items-center gap-2">
          <input
            ref={fileInputRef}
            type="file"
            accept=".pptx"
            className="hidden"
            onChange={(event) => handleUpload(event.target.files?.[0] ?? null)}
          />
          <Button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
          >
            {uploading ? "Importing..." : "Import slides"}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <form
          className="flex flex-col gap-3 sm:flex-row sm:items-center"
          onSubmit={handleSearch}
        >
          <Input
            placeholder="Search by description or tags"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          <Button
            variant="secondary"
            className="sm:w-auto"
            type="submit"
            disabled={loading}
          >
            Search
          </Button>
        </form>
        {error ? <p className="text-sm text-destructive">{error}</p> : null}
        <p className="text-xs text-muted-foreground">
          {loading
            ? "Loading slides..."
            : `Showing ${slides.length} result${
                slides.length === 1 ? "" : "s"
              }`}
        </p>
        <div className="grid gap-3 md:grid-cols-2">
          {loading ? (
            <div className="rounded-lg border border-border bg-muted/40 p-6 text-center text-sm text-muted-foreground">
              Loading...
            </div>
          ) : slides.length ? (
            slides.map((item) => (
              <div
                key={item.id}
                className="flex flex-col gap-3 rounded-lg border border-border bg-card/60 p-4 shadow-sm"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="text-xs text-muted-foreground">
                      {item.subtitle} · Updated {item.updated}
                    </div>
                  </div>
                  <a
                    href={item.downloadUrl}
                    className="inline-flex h-8 items-center justify-center rounded-md border border-input bg-background px-3 text-xs font-medium shadow-sm transition hover:bg-muted"
                  >
                    Download
                  </a>
                  <Button
                    size="sm"
                    variant="secondary"
                    className="h-8 px-3"
                    onClick={() =>
                      setExpanded((prev) => ({
                        ...prev,
                        [item.id]: !prev[item.id],
                      }))
                    }
                  >
                    {expanded[item.id]
                      ? "Hide description"
                      : "Show description"}
                  </Button>
                </div>
                <div className="overflow-hidden rounded-md border border-border bg-muted/40">
                  <img
                    src={item.preview || FALLBACK_PREVIEW}
                    alt="Slide preview"
                    className="h-auto w-full object-cover"
                    loading="lazy"
                  />
                </div>
                {expanded[item.id] ? (
                  <div className="text-sm text-foreground">
                    {item.description}
                  </div>
                ) : null}
              </div>
            ))
          ) : (
            <div className="rounded-lg border border-dashed border-border bg-muted/40 p-6 text-center text-sm text-muted-foreground">
              No slides match your search. Try a different keyword or import
              more slides.
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
