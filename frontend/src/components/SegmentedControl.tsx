import { cn } from "@/lib/utils";

type Option = {
  value: string;
  label: string;
  description?: string;
};

type SegmentedControlProps = {
  options: Option[];
  value: string;
  onChange: (value: string) => void;
};

export function SegmentedControl({ options, value, onChange }: SegmentedControlProps) {
  return (
    <div className="inline-flex items-stretch rounded-md border border-border bg-muted p-1 text-sm">
      {options.map((option) => {
        const active = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange(option.value)}
            className={cn(
              "flex min-w-[140px] flex-col items-start gap-0.5 rounded-md px-3 py-2 text-left transition",
              active
                ? "bg-background shadow-sm ring-1 ring-border"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            <span className="font-medium">{option.label}</span>
            {option.description ? (
              <span className="text-xs text-muted-foreground">
                {option.description}
              </span>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}

