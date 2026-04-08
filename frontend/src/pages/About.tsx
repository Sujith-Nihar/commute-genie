import { motion } from "framer-motion";
import { ArrowRight, Cpu, Users, Layers } from "lucide-react";

const FLOW_STEPS = [
  { label: "User", color: "from-muted to-muted" },
  { label: "Frontend", color: "from-accent/30 to-accent/10" },
  { label: "FastAPI", color: "from-primary/30 to-primary/10" },
  { label: "LangGraph", color: "from-secondary/30 to-secondary/10" },
  { label: "Manager", color: "from-primary/30 to-accent/10" },
  { label: "Transport + Context", color: "from-transit-teal/30 to-transit-amber/10" },
  { label: "Manager Draft", color: "from-primary/30 to-accent/10" },
  { label: "Critic", color: "from-transit-green/30 to-transit-green/10" },
  { label: "Final Answer", color: "from-primary/40 to-accent/20" },
];

const TECH_STACK = [
  { name: "FastAPI", desc: "High-performance async backend" },
  { name: "LangGraph", desc: "Multi-agent orchestration framework" },
  { name: "LangChain", desc: "LLM tooling and chain management" },
  { name: "Gemini", desc: "Google's large language model for reasoning" },
  { name: "LTA DataMall", desc: "Singapore's official transport data API" },
  { name: "Streamlit", desc: "Legacy frontend (being replaced)" },
];

const TEAM = [
  { name: "Sujith Thota", role: "System architecture, Manager Agent, Context Agent, backend orchestration" },
  { name: "Lakshmi Naga Hrishitaa Dharmavarapu", role: "Transport Agent, frontend, documentation" },
  { name: "Shared Work", role: "Critic Agent, testing, prompt refinement, integration" },
];

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: (i: number) => ({
    opacity: 1, y: 0,
    transition: { delay: i * 0.08, duration: 0.4 },
  }),
};

export default function About() {
  return (
    <div className="py-16">
      <div className="container max-w-4xl space-y-24">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl md:text-4xl font-sans font-extrabold tracking-tight">
            How <span className="gradient-text">CommuteGenie</span> Works
          </h1>
          <p className="mt-4 text-muted-foreground max-w-2xl mx-auto">
            A multi-agent AI system that reasons about Singapore's public transport using real-time data and structured reflection.
          </p>
        </div>

        {/* Architecture Flow */}
        <section>
          <div className="flex items-center gap-2 mb-8 justify-center">
            <Layers className="h-5 w-5 text-primary" />
            <h2 className="text-xl font-sans font-bold">System Architecture</h2>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-2">
            {FLOW_STEPS.map((step, i) => (
              <motion.div
                key={step.label}
                className="flex items-center gap-2"
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                variants={fadeUp}
                custom={i}
              >
                <span className={`px-4 py-2.5 rounded-xl glass bg-gradient-to-r ${step.color} text-sm font-medium text-foreground whitespace-nowrap`}>
                  {step.label}
                </span>
                {i < FLOW_STEPS.length - 1 && (
                  <ArrowRight className="h-4 w-4 text-primary/40 flex-shrink-0" />
                )}
              </motion.div>
            ))}
          </div>
        </section>

        {/* Tech Stack */}
        <section>
          <div className="flex items-center gap-2 mb-6">
            <Cpu className="h-5 w-5 text-primary" />
            <h2 className="text-xl font-sans font-bold">Tech Stack</h2>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {TECH_STACK.map((t, i) => (
              <motion.div
                key={t.name}
                className="glass rounded-xl p-5 hover:glow-accent transition-all duration-300"
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                variants={fadeUp}
                custom={i}
              >
                <h3 className="font-sans font-semibold text-foreground">{t.name}</h3>
                <p className="text-sm text-muted-foreground mt-1">{t.desc}</p>
              </motion.div>
            ))}
          </div>
        </section>

        {/* Team */}
        <section>
          <div className="flex items-center gap-2 mb-6">
            <Users className="h-5 w-5 text-primary" />
            <h2 className="text-xl font-sans font-bold">Team</h2>
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            {TEAM.map((m, i) => (
              <motion.div
                key={m.name}
                className="glass rounded-xl p-5 hover:glow-accent transition-all duration-300"
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                variants={fadeUp}
                custom={i}
              >
                <h3 className="font-sans font-semibold text-foreground">{m.name}</h3>
                <p className="text-sm text-muted-foreground mt-2">{m.role}</p>
              </motion.div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
