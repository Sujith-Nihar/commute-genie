import { Link, useLocation } from "react-router-dom";
import { useState } from "react";
import { Menu, X, Train } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import ThemeToggle from "@/components/ThemeToggle";

const navLinks = [
  { to: "/", label: "Home" },
  { to: "/chat", label: "Chat" },
  { to: "/about", label: "About" },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const { pathname } = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="min-h-screen flex flex-col">
      <header className="sticky top-0 z-50 glass-strong">
        <div className="container flex h-16 items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5 font-sans font-bold text-lg">
            <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center">
              <Train className="h-4 w-4 text-primary-foreground" />
            </div>
            <span className="gradient-text">CommuteGenie</span>
          </Link>

          <nav className="hidden md:flex items-center gap-1">
            {navLinks.map((l) => (
              <Link
                key={l.to}
                to={l.to}
                className={cn(
                  "px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200",
                  pathname === l.to
                    ? "bg-primary/15 text-primary"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                )}
              >
                {l.label}
              </Link>
            ))}
          </nav>

          <div className="hidden md:flex items-center gap-2">
            <ThemeToggle />
            <Button asChild size="sm" className="bg-gradient-to-r from-primary to-accent text-primary-foreground hover:opacity-90 transition-opacity border-0">
              <Link to="/chat">Start Chatting</Link>
            </Button>
          </div>

          <div className="flex md:hidden items-center gap-1">
            <ThemeToggle />
            <button
              className="p-2 text-muted-foreground"
              onClick={() => setMobileOpen(!mobileOpen)}
              aria-label="Toggle menu"
            >
              {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>

        {mobileOpen && (
          <div className="md:hidden border-t border-glass-border/50 glass p-4 space-y-2">
            {navLinks.map((l) => (
              <Link
                key={l.to}
                to={l.to}
                onClick={() => setMobileOpen(false)}
                className={cn(
                  "block px-4 py-2 rounded-lg text-sm font-medium",
                  pathname === l.to ? "bg-primary/15 text-primary" : "text-muted-foreground"
                )}
              >
                {l.label}
              </Link>
            ))}
          </div>
        )}
      </header>

      <main className="flex-1">{children}</main>

      <footer className="border-t border-glass-border/30 py-8">
        <div className="container text-center text-sm text-muted-foreground">
          <p>© 2025 CommuteGenie Singapore. Built with multi-agent AI for smarter commutes.</p>
        </div>
      </footer>
    </div>
  );
}
