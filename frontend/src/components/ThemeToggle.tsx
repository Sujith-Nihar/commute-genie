import { Sun, Moon } from "lucide-react";
import { useTheme } from "@/components/ThemeProvider";
import { cn } from "@/lib/utils";

export default function ThemeToggle() {
  const { resolved, setTheme } = useTheme();
  const isDark = resolved === "dark";

  return (
    <button
      onClick={() => setTheme(isDark ? "light" : "dark")}
      className={cn(
        "relative h-9 w-9 rounded-lg flex items-center justify-center",
        "text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-all duration-200"
      )}
      aria-label={`Switch to ${isDark ? "light" : "dark"} mode`}
    >
      <Sun className={cn("h-4 w-4 absolute transition-all duration-300", isDark ? "opacity-0 rotate-90 scale-0" : "opacity-100 rotate-0 scale-100")} />
      <Moon className={cn("h-4 w-4 absolute transition-all duration-300", isDark ? "opacity-100 rotate-0 scale-100" : "opacity-0 -rotate-90 scale-0")} />
    </button>
  );
}
