import { useState } from "react";

import { GenerationPanel } from "./GenerationPanel";
import { SlideLibrary } from "./SlideLibrary";

export function App() {
  const tabs = [
    { id: "generation", label: "Generation", sub: "Compose or generate slides" },
    { id: "library", label: "Slide Library", sub: "Browse, search, import" },
  ] as const;

  const [active, setActive] = useState<(typeof tabs)[number]["id"]>("generation");

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="mx-auto flex max-w-6xl flex-col gap-8 px-6 py-10">
        <header className="flex flex-col items-start justify-between gap-3 sm:flex-row sm:items-center">
          <div>
            <p className="text-sm font-semibold text-primary">Slide Agent</p>
            <h1 className="text-3xl font-bold leading-tight">Workspace</h1>
            <p className="text-sm text-muted-foreground">
              Manage your slide library and switch between compose and generate modes.
            </p>
          </div>
          <div className="rounded-full border border-border bg-muted/50 px-3 py-1 text-xs text-muted-foreground">
            Astro · Tailwind · shadcn/ui
          </div>
        </header>

        <main className="space-y-4">
          <div className="flex flex-wrap gap-2 rounded-lg border border-border bg-muted/40 p-2">
            {tabs.map((tab) => {
              const activeTab = tab.id === active;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActive(tab.id)}
                  className={[
                    "flex flex-col rounded-md px-4 py-2 text-left transition",
                    activeTab
                      ? "bg-background shadow-sm ring-1 ring-border"
                      : "text-muted-foreground hover:text-foreground",
                  ].join(" ")}
                >
                  <span className="text-sm font-semibold">{tab.label}</span>
                  <span className="text-xs text-muted-foreground">{tab.sub}</span>
                </button>
              );
            })}
          </div>

          {active === "generation" ? <GenerationPanel /> : <SlideLibrary />}
        </main>
      </div>
    </div>
  );
}

