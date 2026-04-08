import { useState } from "react";
import { motion } from "framer-motion";
import {
  Bot, CheckCircle2, XCircle, ChevronDown, Clock,
  Shield, Cpu, Radio, Code2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";
import type { AskResponse } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  response?: AskResponse;
  timestamp?: Date;
}

const AGENT_META: Record<string, { color: string; label: string }> = {
  manager: { color: "bg-primary/15 text-primary border-primary/20", label: "Manager" },
  transport: { color: "bg-transit-teal/15 text-transit-teal border-transit-teal/20", label: "Transport" },
  context: { color: "bg-transit-amber/15 text-transit-amber border-transit-amber/20", label: "Context" },
  critic: { color: "bg-transit-green/15 text-transit-green border-transit-green/20", label: "Critic" },
};

function AgentChip({ agent }: { agent: string }) {
  const meta = AGENT_META[agent];
  return (
    <span className={cn("px-2.5 py-0.5 rounded-full text-xs font-medium capitalize border", meta?.color || "bg-muted text-muted-foreground border-border")}>
      {meta?.label || agent}
    </span>
  );
}

function ReasoningSummary({ response }: { response: AskResponse }) {
  const [open, setOpen] = useState(false);

  const signals = response.used_agents.filter((a) => a !== "manager" && a !== "critic");
  const wasValidated = response.used_agents.includes("critic");

  return (
    <div className="border border-glass-border/40 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 text-sm font-medium text-muted-foreground hover:bg-muted/30 transition-colors"
      >
        <span className="flex items-center gap-2">
          <Cpu className="h-3.5 w-3.5" />
          How this answer was produced
        </span>
        <ChevronDown className={cn("h-3.5 w-3.5 transition-transform duration-200", open && "rotate-180")} />
      </button>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="px-4 pb-4 space-y-3 border-t border-glass-border/30"
        >
          <div className="pt-3 grid gap-3 sm:grid-cols-2">
            {/* Signals */}
            <div className="flex items-start gap-2.5">
              <Radio className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-xs font-medium text-foreground">Signals checked</p>
                <p className="text-xs text-muted-foreground mt-0.5 capitalize">
                  {signals.length > 0 ? signals.join(", ") : "General reasoning"}
                </p>
              </div>
            </div>
            {/* Agents */}
            <div className="flex items-start gap-2.5">
              <Cpu className="h-4 w-4 text-accent mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-xs font-medium text-foreground">Agents involved</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {response.used_agents.length} specialist{response.used_agents.length !== 1 ? "s" : ""}
                </p>
              </div>
            </div>
            {/* Validation */}
            <div className="flex items-start gap-2.5">
              <Shield className="h-4 w-4 text-transit-green mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-xs font-medium text-foreground">Validation</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {wasValidated
                    ? response.approved ? "Critic approved" : "Critic flagged for review"
                    : "Not validated"}
                </p>
              </div>
            </div>
            {/* Context */}
            <div className="flex items-start gap-2.5">
              <Clock className="h-4 w-4 text-transit-amber mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-xs font-medium text-foreground">Context considered</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {response.used_agents.includes("context")
                    ? "Time, rush hour & holiday signals"
                    : "Standard reasoning"}
                </p>
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}

function DebugTrace({ trace }: { trace: Record<string, unknown> }) {
  const [open, setOpen] = useState(false);
  if (!trace || Object.keys(trace).length === 0) return null;

  return (
    <div className="border border-glass-border/30 rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-2 text-xs font-medium text-muted-foreground/70 hover:bg-muted/20 transition-colors"
      >
        <span className="flex items-center gap-1.5">
          <Code2 className="h-3 w-3" />
          Developer trace
        </span>
        <ChevronDown className={cn("h-3 w-3 transition-transform duration-200", open && "rotate-180")} />
      </button>
      {open && (
        <pre className="px-4 py-3 text-xs bg-muted/20 overflow-x-auto max-h-64 overflow-y-auto border-t border-glass-border/30 text-muted-foreground font-mono">
          {JSON.stringify(trace, null, 2)}
        </pre>
      )}
    </div>
  );
}

export default function AssistantMessage({ msg }: { msg: Message }) {
  const r = msg.response;
  const time = msg.timestamp
    ? msg.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    : null;

  return (
    <div className="flex gap-3 max-w-3xl">
      <div className="flex-shrink-0 h-8 w-8 rounded-full bg-primary/15 flex items-center justify-center mt-1">
        <Bot className="h-4 w-4 text-primary" />
      </div>
      <div className="flex-1 min-w-0 space-y-2">
        {/* Main answer card */}
        <div className="glass rounded-2xl rounded-bl-md p-5">
          <div className="prose prose-sm dark:prose-invert max-w-none text-foreground">
            <ReactMarkdown>{msg.content}</ReactMarkdown>
          </div>

          {r && (
            <div className="mt-4 pt-3 border-t border-glass-border/30">
              {/* Badges row */}
              <div className="flex flex-wrap items-center gap-2">
                {r.approved ? (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-transit-green/10 text-transit-green border border-transit-green/20">
                    <CheckCircle2 className="h-3 w-3" /> Verified
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-transit-amber/10 text-transit-amber border border-transit-amber/20">
                    <XCircle className="h-3 w-3" /> Needs Review
                  </span>
                )}
                <span className="text-glass-border/60">·</span>
                {r.used_agents.map((a) => (
                  <AgentChip key={a} agent={a} />
                ))}
                {time && (
                  <>
                    <span className="text-glass-border/60">·</span>
                    <span className="text-xs text-muted-foreground/60">{time}</span>
                  </>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Reasoning summary — user-safe */}
        {r && <ReasoningSummary response={r} />}

        {/* Debug trace — developer-facing */}
        {r?.trace && <DebugTrace trace={r.trace} />}
      </div>
    </div>
  );
}
