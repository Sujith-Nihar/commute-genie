import { motion } from "framer-motion";

// Stylized MRT-inspired route lines as SVG
export default function TransitMapHero() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none" aria-hidden>
      <svg
        className="absolute inset-0 w-full h-full"
        viewBox="0 0 1200 700"
        preserveAspectRatio="xMidYMid slice"
        fill="none"
      >
        {/* Grid dots */}
        {Array.from({ length: 20 }).map((_, i) =>
          Array.from({ length: 12 }).map((_, j) => (
            <circle
              key={`${i}-${j}`}
              cx={60 + i * 60}
              cy={60 + j * 60}
              r="1"
              fill="hsl(174 72% 52% / 0.08)"
            />
          ))
        )}

        {/* Route lines - animated */}
        {[
          { d: "M0 200 Q300 180 500 300 T900 250 T1200 350", color: "hsl(174 72% 52%)", delay: 0 },
          { d: "M0 400 Q200 350 400 420 T700 380 T1200 500", color: "hsl(258 70% 62%)", delay: 0.5 },
          { d: "M100 0 Q150 200 300 350 T500 600 T600 700", color: "hsl(200 80% 55%)", delay: 1 },
          { d: "M800 0 Q850 150 900 300 T1000 500 T1100 700", color: "hsl(38 92% 55%)", delay: 1.5 },
        ].map((route, i) => (
          <motion.path
            key={i}
            d={route.d}
            stroke={route.color}
            strokeWidth="2"
            strokeDasharray="8 12"
            opacity="0.15"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 0.15 }}
            transition={{ duration: 3, delay: route.delay, ease: "easeInOut" }}
          />
        ))}

        {/* Station nodes */}
        {[
          { cx: 300, cy: 240, color: "hsl(174 72% 52%)", delay: 1 },
          { cx: 500, cy: 300, color: "hsl(174 72% 52%)", delay: 1.2 },
          { cx: 750, cy: 270, color: "hsl(174 72% 52%)", delay: 1.4 },
          { cx: 400, cy: 400, color: "hsl(258 70% 62%)", delay: 1.6 },
          { cx: 600, cy: 390, color: "hsl(258 70% 62%)", delay: 1.8 },
          { cx: 300, cy: 350, color: "hsl(200 80% 55%)", delay: 2 },
          { cx: 900, cy: 300, color: "hsl(38 92% 55%)", delay: 2.2 },
        ].map((station, i) => (
          <motion.circle
            key={i}
            cx={station.cx}
            cy={station.cy}
            r="4"
            fill={station.color}
            opacity="0"
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 0.4, scale: 1 }}
            transition={{ delay: station.delay, duration: 0.5 }}
          />
        ))}
      </svg>

      {/* Gradient overlays */}
      <div className="absolute inset-0 bg-gradient-to-b from-background via-transparent to-background" />
      <div className="absolute inset-0 bg-gradient-to-r from-background/80 via-transparent to-background/80" />
    </div>
  );
}
