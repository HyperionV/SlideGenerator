import { useMemo, useState } from "react";

import { composeSlides, generateSlides } from "@/lib/api";
import { SegmentedControl } from "@/components/SegmentedControl";
import { Button } from "./ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Input } from "./ui/input";

export function GenerationPanel() {
  const [mode, setMode] = useState<"compose" | "generate">("compose");
  const [outline, setOutline] = useState("");
  const [prompt, setPrompt] = useState("");
  const [contextFiles, setContextFiles] = useState<File[]>([]);
  const [contextText, setContextText] = useState("");
  const [templateFile, setTemplateFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<string | null>(null);
  const [downloadTargets, setDownloadTargets] = useState<string[]>([]);

  const handleContextFile = async (file?: File | null) => {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".md")) {
      setError("Only .md files are accepted for context");
      return;
    }
    const text = await file.text();
    setContextFiles((prev) => [...prev, file]);
    setContextText((prev) => [prev, text].filter(Boolean).join("\n\n"));
  };

  const handleContextDrop = async (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const files = Array.from(event.dataTransfer.files || []);
    const mdFiles = files.filter((f) => f.name.toLowerCase().endsWith(".md"));
    if (!mdFiles.length) {
      setError("Drop .md files only");
      return;
    }
    for (const file of mdFiles) {
      // eslint-disable-next-line no-await-in-loop
      await handleContextFile(file);
    }
  };

  const contextDisplay = useMemo(
    () => contextFiles.map((f) => f.name).join(", "),
    [contextFiles]
  );

  const collectFilePaths = (data: unknown): string[] => {
    const files: string[] = [];
    if (typeof data === "string") {
      files.push(data);
      return files;
    }
    if (Array.isArray(data)) {
      data.forEach((item) => {
        if (typeof item === "string") files.push(item);
      });
      return files;
    }
    if (data && typeof data === "object") {
      Object.values(data).forEach((val) => {
        if (typeof val === "string") files.push(val);
        if (Array.isArray(val)) {
          val.forEach((item) => {
            if (typeof item === "string") files.push(item);
          });
        }
      });
    }
    return files;
  };

  const handleCompose = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await composeSlides({
        userContext: contextText,
        userPrompt: outline,
      });
      setResult(JSON.stringify(response, null, 2));
      const parsed = typeof response === "string" ? JSON.parse(response) : response;
      setDownloadTargets(collectFilePaths(parsed));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Compose failed");
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    if (!templateFile) {
      setError("Template .pptx is required for generation");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await generateSlides({
        template: templateFile,
        userInput: prompt || "Presentation",
        documents: contextText,
      });
      setResult(JSON.stringify(response, null, 2));
      try {
        const parsed = typeof response === "string" ? JSON.parse(response) : response;
        setDownloadTargets(collectFilePaths(parsed));
      } catch (e) {
        console.error("Failed to parse generate response", e);
        setDownloadTargets([]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generate failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="h-full">
      <CardHeader className="space-y-4">
        <div className="flex flex-col gap-2">
          <CardTitle className="text-2xl">Generation</CardTitle>
          <CardDescription>Switch between compose and generate workflows.</CardDescription>
        </div>
        <SegmentedControl
          options={[
            { value: "compose", label: "Compose", description: "Start from an outline" },
            { value: "generate", label: "Generate", description: "AI-generated slides" },
          ]}
          value={mode}
          onChange={(value) => setMode(value as "compose" | "generate")}
        />
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-4">
            {mode === "compose" ? (
              <div className="space-y-3">
                <label className="text-sm font-medium text-foreground">Outline</label>
                <textarea
                  className="min-h-[160px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  placeholder="List the sections, key bullets, and tone you want."
                  value={outline}
                  onChange={(event) => setOutline(event.target.value)}
                />
                <div className="flex items-center justify-between">
                  <div />
                  <Button size="md" onClick={handleCompose} disabled={!outline.trim() || loading}>
                    {loading ? "Working..." : "Compose slides"}
                  </Button>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-foreground">Prompt</label>
                  <Input
                    placeholder="What should the deck achieve?"
                    value={prompt}
                    onChange={(event) => setPrompt(event.target.value)}
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-foreground">Template (.pptx)</label>
                  <Input
                    type="file"
                    accept=".pptx"
                    onChange={(event) => setTemplateFile(event.target.files?.[0] ?? null)}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div />
                  <Button
                    size="md"
                    onClick={handleGenerate}
                    disabled={loading || !prompt.trim() || !templateFile}
                  >
                    {loading ? "Working..." : "Generate"}
                  </Button>
                </div>
              </div>
            )}
          </div>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-semibold text-foreground">Context</div>
                <div className="text-xs text-muted-foreground">Drop markdown (.md) files only</div>
              </div>
            </div>
            <div
              className="min-h-[220px] w-full rounded-md border border-dashed border-input bg-background/60 px-3 py-4 text-sm shadow-sm transition hover:border-ring hover:bg-background/80"
              onDragOver={(event) => event.preventDefault()}
              onDrop={handleContextDrop}
            >
              {contextFiles.length === 0 ? (
                <div className="text-center text-xs text-muted-foreground">
                  Drop .md files here
                </div>
              ) : (
                <div className="space-y-2">
                  <div className="text-xs font-semibold text-foreground">Context files</div>
                  <ul className="space-y-1 text-xs text-muted-foreground">
                    {contextFiles.map((file) => (
                      <li key={file.name} className="rounded border border-border bg-card/50 px-2 py-1">
                        {file.name}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      </CardContent>
      <CardContent className="space-y-2">
        {error ? <p className="text-sm text-destructive">{error}</p> : null}
        {downloadTargets.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {downloadTargets.map((file) => (
              <Button
                key={file}
                variant="outline"
                size="sm"
                onClick={() => {
                  const url = `${import.meta.env.PUBLIC_API_BASE_URL || "http://localhost:8000"}/files?path=${encodeURIComponent(file)}`;
                  window.open(url, "_blank");
                }}
              >
                Download {file.split("\\").pop() || file.split("/").pop()}
              </Button>
            ))}
          </div>
        ) : null}
        {result ? (
          <pre className="max-h-56 overflow-auto rounded-md border border-border bg-muted/40 p-3 text-xs">
            {result}
          </pre>
        ) : null}
      </CardContent>
    </Card>
  );
}

