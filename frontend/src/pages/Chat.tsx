import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Loader2, AlertCircle, Bot, User, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { askQuestion, type AskResponse } from "@/lib/api";
import { cn } from "@/lib/utils";
import AssistantMessage from "@/components/chat/AssistantMessage";
import ThinkingState from "@/components/chat/ThinkingState";

interface Message {
  role: "user" | "assistant";
  content: string;
  response?: AskResponse;
  timestamp?: Date;
}

const EXAMPLE_PROMPTS = [
  "When is the next bus arriving at stop 83139?",
  "Find bus stop code for Lucky Plaza",
  "Any MRT disruption right now?",
  "Any traffic incidents now?",
  "Are taxis available right now?",
  "Will rush hour affect travel now?",
];

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [userId, setUserId] = useState("u_demo");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastQuestion, setLastQuestion] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async (question?: string) => {
    const q = (question || input).trim();
    if (!q || loading) return;
    setInput("");
    setError(null);
    setLastQuestion(q);

    const userMsg: Message = { role: "user", content: q, timestamp: new Date() };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await askQuestion({ question: q, user_id: userId });
      const assistantMsg: Message = {
        role: "assistant",
        content: res.answer,
        response: res,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Something went wrong.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = () => {
    if (lastQuestion) {
      setError(null);
      handleSend(lastQuestion);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      <div className="flex-1 overflow-y-auto">
        <div className="container max-w-3xl py-6 space-y-6">
          {/* Empty state */}
          {messages.length === 0 && !loading && (
            <div className="text-center py-20">
              <div className="h-16 w-16 mx-auto rounded-2xl bg-gradient-to-br from-primary/20 to-accent/10 flex items-center justify-center mb-5">
                <Bot className="h-8 w-8 text-primary" />
              </div>
              <h2 className="text-xl font-sans font-semibold text-foreground mb-2">
                Ask CommuteGenie anything
              </h2>
              <p className="text-muted-foreground text-sm mb-10 max-w-md mx-auto">
                Get real-time transit information for Singapore — buses, MRT, traffic, and more.
              </p>
              <div className="flex flex-wrap justify-center gap-2 max-w-lg mx-auto">
                {EXAMPLE_PROMPTS.map((p) => (
                  <button
                    key={p}
                    onClick={() => handleSend(p)}
                    className="px-3.5 py-2 rounded-xl text-xs font-medium glass border-primary/10 text-primary hover:bg-primary/10 transition-all"
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Messages */}
          <AnimatePresence>
            {messages.map((msg, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                {msg.role === "user" ? (
                  <div className="flex gap-3 max-w-3xl justify-end">
                    <div className="bg-gradient-to-r from-primary to-accent text-primary-foreground rounded-2xl rounded-br-md px-4 py-3 max-w-md">
                      <p className="text-sm">{msg.content}</p>
                    </div>
                    <div className="flex-shrink-0 h-8 w-8 rounded-full bg-muted flex items-center justify-center mt-1">
                      <User className="h-4 w-4 text-muted-foreground" />
                    </div>
                  </div>
                ) : (
                  <AssistantMessage msg={msg} />
                )}
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Thinking state */}
          {loading && (
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              <ThinkingState />
            </motion.div>
          )}

          {/* Error with retry */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-start gap-3 p-4 rounded-xl glass border-destructive/20 max-w-3xl"
            >
              <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0 text-destructive" />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-destructive">{error}</p>
              </div>
              <Button
                size="sm"
                variant="ghost"
                onClick={handleRetry}
                className="flex-shrink-0 text-xs gap-1.5 text-muted-foreground hover:text-foreground"
              >
                <RotateCcw className="h-3 w-3" /> Retry
              </Button>
            </motion.div>
          )}

          <div ref={endRef} />
        </div>
      </div>

      {/* Input area */}
      <div className="border-t border-glass-border/30 glass-strong">
        <div className="container max-w-3xl py-4">
          <div className="flex items-center gap-2 mb-2">
            <label className="text-xs text-muted-foreground">User ID:</label>
            <Input
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              className="h-7 w-32 text-xs bg-muted/50 border-glass-border/50"
            />
          </div>
          <form
            onSubmit={(e) => { e.preventDefault(); handleSend(); }}
            className="flex gap-2"
          >
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about buses, MRT, traffic, taxis…"
              disabled={loading}
              className="flex-1 bg-muted/50 border-glass-border/50 focus:border-primary/50"
            />
            <Button
              type="submit"
              disabled={loading || !input.trim()}
              size="icon"
              className={cn(
                "bg-gradient-to-r from-primary to-accent text-primary-foreground hover:opacity-90 border-0",
                "disabled:opacity-40"
              )}
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
