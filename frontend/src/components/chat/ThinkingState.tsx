import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Bot, Search, MapPin, Brain, ShieldCheck, Sparkles, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";

const THINKING_STEPS = [
  { label: "Understanding your question", icon: Search, duration: 1800 },
  { label: "Checking transport signals", icon: MapPin, duration: 2200 },
  { label: "Reviewing commute context", icon: Brain, duration: 2000 },
  { label: "Coordinating specialist agents", icon: Sparkles, duration: 2400 },
  { label: "Validating the response", icon: ShieldCheck, duration: 1600 },
];

export default function ThinkingState() {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    if (activeStep >= THINKING_STEPS.length) return;
    const timer = setTimeout(() => {
      setActiveStep((s) => Math.min(s + 1, THINKING_STEPS.length));
    }, THINKING_STEPS[activeStep].duration);
    return () => clearTimeout(timer);
  }, [activeStep]);

  return (
    <div className="flex gap-3 max-w-3xl">
      <div className="flex-shrink-0 h-8 w-8 rounded-full bg-primary/15 flex items-center justify-center mt-1">
        <Bot className="h-4 w-4 text-primary animate-pulse-soft" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="glass rounded-2xl rounded-bl-md p-5">
          {/* Header */}
          <div className="flex items-center gap-2 mb-4">
            <div className="relative h-2 w-2">
              <span className="absolute inset-0 rounded-full bg-primary animate-ping opacity-75" />
              <span className="relative block h-2 w-2 rounded-full bg-primary" />
            </div>
            <span className="text-sm font-medium text-foreground">Working on it…</span>
          </div>

          {/* Steps timeline */}
          <div className="space-y-1">
            <AnimatePresence mode="popLayout">
              {THINKING_STEPS.map((step, i) => {
                const completed = i < activeStep;
                const active = i === activeStep;
                const StepIcon = step.icon;

                if (i > activeStep) return null;

                return (
                  <motion.div
                    key={step.label}
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    transition={{ duration: 0.3, ease: "easeOut" }}
                    className="overflow-hidden"
                  >
                    <div className={cn(
                      "flex items-center gap-3 py-2 px-3 rounded-lg transition-colors duration-300",
                      active && "bg-primary/5"
                    )}>
                      <div className={cn(
                        "h-6 w-6 rounded-md flex items-center justify-center transition-all duration-300 flex-shrink-0",
                        completed
                          ? "bg-primary/15 text-primary"
                          : active
                            ? "bg-primary/10 text-primary"
                            : "bg-muted text-muted-foreground"
                      )}>
                        {completed ? (
                          <CheckCircle2 className="h-3.5 w-3.5" />
                        ) : (
                          <StepIcon className={cn("h-3.5 w-3.5", active && "animate-pulse-soft")} />
                        )}
                      </div>
                      <span className={cn(
                        "text-sm transition-colors duration-300",
                        completed
                          ? "text-muted-foreground"
                          : active
                            ? "text-foreground font-medium"
                            : "text-muted-foreground"
                      )}>
                        {step.label}
                      </span>
                      {active && (
                        <motion.div
                          className="ml-auto flex gap-1"
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                        >
                          {[0, 1, 2].map((d) => (
                            <motion.span
                              key={d}
                              className="h-1 w-1 rounded-full bg-primary"
                              animate={{ opacity: [0.3, 1, 0.3] }}
                              transition={{ duration: 1, repeat: Infinity, delay: d * 0.2 }}
                            />
                          ))}
                        </motion.div>
                      )}
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  );
}
