import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import {
  Bus, TrainFront, Car, Clock, BrainCircuit, ArrowRight, Sparkles,
} from "lucide-react";
import TransitMapHero from "@/components/TransitMapHero";

const features = [
  {
    icon: Bus,
    title: "Bus Arrival Intelligence",
    desc: "Real-time bus arrival predictions powered by LTA DataMall with contextual delays.",
    gradient: "from-primary/20 to-accent/10",
  },
  {
    icon: TrainFront,
    title: "MRT Disruption Awareness",
    desc: "Instant alerts on MRT disruptions, service changes, and alternative routes.",
    gradient: "from-secondary/20 to-primary/10",
  },
  {
    icon: Car,
    title: "Traffic & Taxi Signals",
    desc: "Live traffic incidents and taxi availability across Singapore.",
    gradient: "from-accent/20 to-secondary/10",
  },
  {
    icon: Clock,
    title: "Rush Hour & Holiday Context",
    desc: "Smart awareness of peak hours, public holidays, and special events.",
    gradient: "from-transit-amber/20 to-primary/10",
  },
  {
    icon: BrainCircuit,
    title: "Multi-Agent AI Reasoning",
    desc: "Manager–Worker–Critic architecture ensures accurate, validated answers.",
    gradient: "from-secondary/20 to-accent/10",
  },
];

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1, duration: 0.5, ease: "easeOut" },
  }),
};

export default function Landing() {
  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden py-28 md:py-40">
        <TransitMapHero />
        <div className="container relative text-center max-w-3xl mx-auto">
          <motion.div initial="hidden" animate="visible" variants={fadeUp} custom={0}>
            <span className="inline-flex items-center gap-1.5 mb-6 px-4 py-1.5 rounded-full text-xs font-semibold glass border border-primary/20 text-primary tracking-wide uppercase">
              <Sparkles className="h-3 w-3" />
              Powered by Multi-Agent AI
            </span>
          </motion.div>
          <motion.h1
            className="text-4xl md:text-6xl lg:text-7xl font-sans font-extrabold tracking-tight leading-[1.1]"
            initial="hidden" animate="visible" variants={fadeUp} custom={1}
          >
            <span className="text-foreground">Commute</span>
            <span className="gradient-text">Genie</span>
            <br />
            <span className="text-foreground text-3xl md:text-5xl lg:text-5xl font-bold">Singapore</span>
          </motion.h1>
          <motion.p
            className="mt-6 text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed"
            initial="hidden" animate="visible" variants={fadeUp} custom={2}
          >
            Your intelligent multi-agent public transportation assistant. Ask anything about buses, MRT, traffic, and taxis — get grounded, real-time answers.
          </motion.p>
          <motion.div
            className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4"
            initial="hidden" animate="visible" variants={fadeUp} custom={3}
          >
            <Button asChild size="lg" className="gap-2 px-8 text-base bg-gradient-to-r from-primary to-accent text-primary-foreground hover:opacity-90 border-0 glow-primary">
              <Link to="/chat">
                Start Chatting <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg" className="px-8 text-base glass border-glass-border/50 text-foreground hover:bg-muted/50">
              <Link to="/about">Learn More</Link>
            </Button>
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section className="py-24">
        <div className="container max-w-5xl">
          <motion.h2
            className="text-2xl md:text-3xl font-sans font-bold text-center mb-4"
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
          >
            What CommuteGenie Can Do
          </motion.h2>
          <motion.p
            className="text-muted-foreground text-center mb-14 max-w-xl mx-auto"
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
          >
            Five intelligent capabilities working together to keep you moving.
          </motion.p>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {features.map((f, i) => (
              <motion.div
                key={f.title}
                className="glass rounded-xl p-6 hover:glow-accent transition-all duration-300 group"
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true, margin: "-50px" }}
                variants={fadeUp}
                custom={i}
              >
                <div className={`h-11 w-11 rounded-xl bg-gradient-to-br ${f.gradient} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                  <f.icon className="h-5 w-5 text-primary" />
                </div>
                <h3 className="font-sans font-semibold text-foreground mb-2">{f.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24">
        <div className="container text-center max-w-2xl">
          <div className="glass rounded-2xl p-12 glow-primary">
            <h2 className="text-2xl md:text-3xl font-sans font-bold mb-4">Ready to commute smarter?</h2>
            <p className="text-muted-foreground mb-8">
              Ask your first question and experience AI-powered transit intelligence.
            </p>
            <Button asChild size="lg" className="px-10 text-base gap-2 bg-gradient-to-r from-primary to-accent text-primary-foreground hover:opacity-90 border-0">
              <Link to="/chat">
                Try It Now <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
          </div>
        </div>
      </section>
    </div>
  );
}
