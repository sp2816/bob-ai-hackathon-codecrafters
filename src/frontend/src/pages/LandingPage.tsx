import { useEffect, useRef, useState } from "react";
import { 
  Shield, Plane, Activity, CheckCircle2, ChevronRight, 
  TriangleAlert, Wrench, Zap, Cpu, Database, 
  MessageSquare, Radar, Crosshair, Target, Server,
  ArrowRight, ArrowDown, Play
} from "lucide-react";

interface LandingPageProps {
  onEnter: () => void;
}

// ── Intersection Observer Hook for fade-in animations ──
function useFadeIn() {
  const domRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("visible");
            // Optional: observer.unobserve(entry.target); if we only want it to fade in once
          }
        });
      },
      { threshold: 0.15 }
    );
    const { current } = domRef;
    if (current) observer.observe(current);
    return () => {
      if (current) observer.unobserve(current);
    };
  }, []);
  return domRef;
}

// ── FadeInSection Component ──
function FadeInSection({ children, delay = "", className = "" }: { children: React.ReactNode, delay?: string, className?: string }) {
  const ref = useFadeIn();
  return (
    <div ref={ref} className={`fade-in-up ${delay} ${className}`}>
      {children}
    </div>
  );
}

export default function LandingPage({ onEnter }: LandingPageProps) {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    // Force dark mode for landing page
    document.documentElement.setAttribute("data-theme", "dark");
    
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const scrollToSection = (id: string) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <div className="min-h-screen bg-[#0a0f1c] text-[#edf0f7] selection:bg-[#af1763]/30 overflow-x-hidden font-sans">
      
      {/* ── Navigation Bar ── */}
      <nav className={`fixed top-0 w-full z-50 transition-all duration-300 ${scrolled ? "bg-[#0a0f1c]/80 backdrop-blur-md border-b border-white/5 py-3 shadow-lg" : "bg-transparent py-5"}`}>
        <div className="max-w-[1400px] mx-auto px-6 md:px-12 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="text-[#AF1763] h-6 w-6" strokeWidth={2} />
            <span className="font-bold text-xl tracking-tight">AssetSentinel</span>
          </div>
          
          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-white/70">
            <a href="#home" className="nav-link-hf">Home</a>
            <a href="#features" className="nav-link-hf">Features</a>
            <a href="#how-it-works" className="nav-link-hf">How It Works</a>
            <a href="#use-cases" className="nav-link-hf">Use Cases</a>
            <a href="#about" className="nav-link-hf">About</a>
          </div>
          
          <button onClick={onEnter} className="btn-ai-sm px-5 py-2 group">
            Enter Mission Control
            <ChevronRight className="h-4 w-4 btn-icon-hf" />
          </button>
        </div>
      </nav>

      {/* ── Hero Section ── */}
      <section id="home" className="relative min-h-[100vh] flex items-center justify-center pt-24 overflow-hidden bg-aerospace">
        <div className="bg-stars absolute inset-0 z-0"></div>
        <div className="bg-technical-grid absolute inset-0 z-0 opacity-50"></div>
        <div className="bg-earth-glow absolute inset-0 z-0"></div>
        
        {/* Radar Visual */}
        <div className="radar-visual z-0 hidden lg:block">
          <div className="radar-crosshair"></div>
          <div className="radar-crosshair-h"></div>
        </div>

        {/* Static Fighter Jet */}
        <div className="static-jet-container">
          <img src="/jet.jpg" alt="Fighter Jet" className="static-jet-image" />
        </div>

        {/* Full Hero Grid Layout */}
        <div className="relative z-20 w-full max-w-[1400px] mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-8 items-center h-full min-h-[70vh]">
          
          {/* Left HUD Column */}
          <div className="hidden lg:flex flex-col justify-between h-full col-span-3 pt-10 pb-10">
            <div>
              <div className="text-[10px] font-technical text-white/40 uppercase tracking-[0.2em] mb-2 connector-line">Mission Control // Initiating</div>
              <div className="h-[2px] w-32 bg-cyan-900/40 rounded overflow-hidden mb-6">
                <div className="h-full w-2/3 bg-cyan-400/80"></div>
              </div>
              <div className="space-y-1">
                <div className="text-[9px] font-technical text-cyan/70 uppercase tracking-widest">Flight Vector // Active</div>
                <div className="text-[9px] font-technical text-cyan/70 uppercase tracking-widest">Telemetry // Online</div>
                <div className="text-[9px] font-technical text-cyan/70 uppercase tracking-widest">Asset Scan // In Progress</div>
                <div className="text-[9px] font-technical text-cyan/70 uppercase tracking-widest">Predictive Intelligence // Loading</div>
              </div>
            </div>

            <div className="mt-auto border border-cyan-900/30 bg-cyan-900/10 p-4 rounded-sm backdrop-blur-sm inline-block w-40">
              <div className="text-[10px] font-technical text-cyan/90 uppercase tracking-widest mb-1">Assets</div>
              <div className="text-[10px] font-technical text-cyan/60 uppercase tracking-widest mb-1">Predict</div>
              <div className="text-[10px] font-technical text-cyan/60 uppercase tracking-widest mb-1">Detect</div>
              <div className="text-[10px] font-technical text-cyan/60 uppercase tracking-widest">Maintain</div>
              <div className="flex items-end gap-1 mt-3 h-4">
                <div className="w-1.5 h-full bg-cyan-500/50"></div>
                <div className="w-1.5 h-3/4 bg-cyan-500/50"></div>
                <div className="w-1.5 h-1/2 bg-cyan-500/50"></div>
                <div className="w-1.5 h-1/4 bg-cyan-500/50"></div>
              </div>
            </div>
          </div>

          {/* Right Content & HUD Column */}
          <div className="col-span-1 lg:col-span-9 flex flex-col items-end text-right justify-center h-full relative lg:pt-10">
            
            {/* Top Right HUD */}
            <div className="hidden lg:block absolute top-10 right-0 text-[10px] font-technical text-cyan/60 uppercase tracking-widest space-y-1 text-left">
              <div>X: 125.3</div>
              <div>Y: 42.6</div>
              <div>ALT: 28,000 FT</div>
              <div>SPD: MACH 1.2</div>
            </div>
            
            {/* Right Middle HUD */}
            <div className="hidden lg:flex flex-col items-start absolute right-[-40px] top-1/3 border-l border-cyan-900/50 pl-3 space-y-2">
              <div className="text-[9px] font-technical text-cyan/70 uppercase tracking-widest">Intelligence</div>
              <div className="text-[9px] font-technical text-cyan/50 uppercase tracking-widest">Readiness</div>
              <div className="text-[9px] font-technical text-cyan/50 uppercase tracking-widest">Action</div>
            </div>

            <div className="max-w-2xl mt-12 lg:mt-32 pb-10 z-20">
              <div className="inline-flex items-center gap-2 mb-6">
                <span className="text-[10px] font-technical uppercase tracking-[0.2em] text-white/50">Mission Readiness // Activating</span>
                <span className="h-1.5 w-1.5 rounded-full bg-pink shadow-[0_0_8px_#FF2BA6]"></span>
                <div className="w-24 h-[1px] bg-gradient-to-l from-transparent to-pink/50 ml-2 hidden sm:block"></div>
              </div>
              
              <h1 className="text-5xl md:text-7xl font-bold tracking-tight leading-[1] mb-2 drop-shadow-2xl text-white">
                Asset<span className="text-magenta">Sentinel</span>
              </h1>
              
              <h2 className="text-xl md:text-3xl font-medium text-white/90 mb-6 drop-shadow-md">
                Mission Readiness & Predictive Maintenance Copilot
              </h2>
              
              <p className="text-base md:text-lg text-muted-blue leading-relaxed drop-shadow-md mb-8 lg:ml-auto max-w-lg">
                Turn asset telemetry into mission-ready intelligence. Detect risks early, understand readiness, prioritize maintenance, and give operators a clear conversational view of fleet health.
              </p>
              
              <div className="flex flex-col sm:flex-row items-center justify-end gap-4">
                <button onClick={onEnter} className="btn-primary-hf w-full sm:w-auto px-8 py-3.5 text-sm font-bold uppercase tracking-wider rounded-md flex items-center justify-center">
                  Enter Mission Control <ArrowRight className="ml-2 h-4 w-4 btn-icon-hf" />
                </button>
                <a href="#how-it-works" className="btn-secondary-hf w-full sm:w-auto px-8 py-3.5 text-sm font-bold uppercase tracking-wider rounded-md flex items-center justify-center">
                  <Play className="mr-2 h-4 w-4 btn-icon-hf" /> Explore How It Works
                </a>
              </div>
            </div>

            {/* Bottom Right HUD */}
            <div className="hidden lg:block absolute bottom-10 right-0 text-[10px] font-technical text-cyan/50 uppercase tracking-[0.2em] space-y-1 text-left">
              <div className="text-cyan/70">Global Fleet</div>
              <div>Mission Ready</div>
              <div>A Brighter Tomorrow</div>
            </div>
            
            <div className="absolute bottom-4 right-0 text-[8px] font-technical text-white/20 uppercase tracking-[0.3em]">
              Powered by IBM Technology
            </div>
          </div>
        </div>
        
        {/* Bottom fade out */}
        <div className="absolute bottom-0 w-full h-32 bg-gradient-to-t from-[#0a0f1c] to-transparent"></div>
      </section>

      {/* ── Trust Strip ── */}
      <section className="border-y border-white/5 bg-white/[0.02]">
        <div className="max-w-[1400px] mx-auto px-6 py-6 md:py-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6 opacity-70">
            <span className="text-xs font-bold uppercase tracking-[0.2em] text-white/50 text-center md:text-left">Built for Mission-Critical Operations</span>
            <div className="flex flex-wrap justify-center gap-x-8 gap-y-4 text-sm font-medium tracking-wide">
              <span className="flex items-center gap-2"><Activity className="h-4 w-4"/> Fleet Monitoring</span>
              <span className="flex items-center gap-2"><Target className="h-4 w-4"/> Predictive Maintenance</span>
              <span className="flex items-center gap-2"><Radar className="h-4 w-4"/> Anomaly Detection</span>
              <span className="flex items-center gap-2"><Shield className="h-4 w-4"/> Mission Readiness</span>
              <span className="flex items-center gap-2"><Cpu className="h-4 w-4"/> AI-Assisted Operations</span>
            </div>
          </div>
        </div>
      </section>

      {/* ── Problem Section ── */}
      <section id="how-it-works" className="py-24 md:py-32 relative">
        <div className="max-w-[1400px] mx-auto px-6">
          <FadeInSection className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-6">Mission Readiness Shouldn't Require Manual Investigation</h2>
            <p className="text-white/60 text-lg leading-relaxed">
              Operators face a daily struggle of combining sensor readings, asset conditions, failure risks, anomalies, and maintenance history. The challenge is turning fragmented signals into one actionable truth.
            </p>
          </FadeInSection>
          
          <FadeInSection delay="delay-100">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div className="p-6 rounded-2xl bg-white/[0.02] border border-white/5 backdrop-blur-sm card-hf">
                <span className="text-[#AF1763] font-bold text-xl block mb-2">What</span>
                <span className="text-sm text-white/50 uppercase tracking-wider">is at risk?</span>
              </div>
              <div className="p-6 rounded-2xl bg-white/[0.02] border border-white/5 backdrop-blur-sm card-hf">
                <span className="text-[#AF1763] font-bold text-xl block mb-2">Why</span>
                <span className="text-sm text-white/50 uppercase tracking-wider">is it at risk?</span>
              </div>
              <div className="p-6 rounded-2xl bg-white/[0.02] border border-white/5 backdrop-blur-sm card-hf">
                <span className="text-[#AF1763] font-bold text-xl block mb-2">What</span>
                <span className="text-sm text-white/50 uppercase tracking-wider">needs attention?</span>
              </div>
              <div className="p-6 rounded-2xl bg-white/[0.02] border border-white/5 backdrop-blur-sm card-hf">
                <span className="text-[#AF1763] font-bold text-xl block mb-2">Is the asset</span>
                <span className="text-sm text-white/50 uppercase tracking-wider">ready?</span>
              </div>
            </div>
          </FadeInSection>
        </div>
      </section>

      {/* ── Solution Flow ── */}
      <section className="py-24 bg-white/[0.01] border-y border-white/5">
        <div className="max-w-[1400px] mx-auto px-6">
          <FadeInSection className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold">From Raw Telemetry to Mission-Ready Intelligence</h2>
          </FadeInSection>
          
          <div className="flex flex-col md:flex-row items-center justify-between gap-4 md:gap-0 relative">
            <div className="absolute top-1/2 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-[#AF1763]/50 to-transparent hidden md:block"></div>
            
            {[
              { icon: Database, label: "Sensor Data" },
              { icon: Cpu, label: "ML Analysis" },
              { icon: Activity, label: "Failure Risk" },
              { icon: Shield, label: "Readiness" },
              { icon: Wrench, label: "Maintenance" },
              { icon: MessageSquare, label: "AI Explanation" },
            ].map((step, i) => (
              <FadeInSection key={i} delay={`delay-${(i%5)*100}`} className="relative z-10 flex flex-col items-center flex-1 w-full">
                <div className="h-16 w-16 rounded-full bg-[#0a0f1c] border border-[#AF1763]/30 flex items-center justify-center mb-4 shadow-[0_0_15px_rgba(175,23,99,0.2)] card-hf">
                  <step.icon className="h-6 w-6 text-white icon-hf" />
                </div>
                <span className="text-sm font-medium text-center text-white/80">{step.label}</span>
                {i < 5 && <ArrowDown className="h-4 w-4 text-white/20 my-4 md:hidden" />}
              </FadeInSection>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features Section ── */}
      <section id="features" className="py-24 md:py-32">
        <div className="max-w-[1400px] mx-auto px-6">
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            
            <FadeInSection>
              <div className="p-8 rounded-2xl bg-white/[0.02] border border-white/5 h-full group relative overflow-hidden card-hf">
                <div className="absolute inset-0 bg-gradient-to-br from-[#AF1763]/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                <Activity className="h-8 w-8 text-[#AF1763] mb-6 icon-hf" />
                <h3 className="text-xl font-bold mb-2 text-white">Predictive Maintenance</h3>
                <span className="text-xs font-mono uppercase text-[#AF1763] tracking-wider mb-4 block">Random Forest</span>
                <p className="text-white/60 text-sm leading-relaxed">Estimate component failure risk from structured asset and sensor features before they cause downtime.</p>
              </div>
            </FadeInSection>

            <FadeInSection delay="delay-100">
              <div className="p-8 rounded-2xl bg-white/[0.02] border border-white/5 h-full group relative overflow-hidden card-hf">
                <div className="absolute inset-0 bg-gradient-to-br from-[#3b82f6]/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                <Radar className="h-8 w-8 text-[#3b82f6] mb-6 icon-hf" />
                <h3 className="text-xl font-bold mb-2 text-white">Anomaly Detection</h3>
                <span className="text-xs font-mono uppercase text-[#3b82f6] tracking-wider mb-4 block">Isolation Forest</span>
                <p className="text-white/60 text-sm leading-relaxed">Identify unusual sensor behavior that may require investigation, separating signal from noise.</p>
              </div>
            </FadeInSection>

            <FadeInSection delay="delay-200">
              <div className="p-8 rounded-2xl bg-white/[0.02] border border-white/5 h-full group relative overflow-hidden card-hf">
                <div className="absolute inset-0 bg-gradient-to-br from-[#10b981]/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                <Shield className="h-8 w-8 text-[#10b981] mb-6 icon-hf" />
                <h3 className="text-xl font-bold mb-2 text-white">Mission Readiness</h3>
                <span className="text-xs font-mono uppercase text-[#10b981] tracking-wider mb-4 block">Evidence Based</span>
                <p className="text-white/60 text-sm leading-relaxed">Combine operational evidence to determine asset readiness states objectively and traceably.</p>
              </div>
            </FadeInSection>

            <FadeInSection>
              <div className="p-8 rounded-2xl bg-white/[0.02] border border-white/5 h-full group relative overflow-hidden card-hf">
                <div className="absolute inset-0 bg-gradient-to-br from-[#f59e0b]/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                <Wrench className="h-8 w-8 text-[#f59e0b] mb-6 icon-hf" />
                <h3 className="text-xl font-bold mb-2 text-white">Maintenance Prioritization</h3>
                <span className="text-xs font-mono uppercase text-[#f59e0b] tracking-wider mb-4 block">Logic Engine</span>
                <p className="text-white/60 text-sm leading-relaxed">Prioritize maintenance using failure risk, criticality, mission impact, and operational urgency.</p>
              </div>
            </FadeInSection>

            <FadeInSection delay="delay-100">
              <div className="p-8 rounded-2xl bg-white/[0.02] border border-white/5 h-full group relative overflow-hidden card-hf">
                <div className="absolute inset-0 bg-gradient-to-br from-[#a855f7]/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                <MessageSquare className="h-8 w-8 text-[#a855f7] mb-6 icon-hf" />
                <h3 className="text-xl font-bold mb-2 text-white">AI Copilot</h3>
                <span className="text-xs font-mono uppercase text-[#a855f7] tracking-wider mb-4 block">IBM watsonx.ai</span>
                <p className="text-white/60 text-sm leading-relaxed">Ask natural-language questions about fleet health, risks, maintenance, and readiness using AI.</p>
              </div>
            </FadeInSection>

            <FadeInSection delay="delay-200">
              <div className="p-8 rounded-2xl bg-white/[0.02] border border-white/5 h-full group relative overflow-hidden card-hf">
                <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                <Server className="h-8 w-8 text-white mb-6 icon-hf" />
                <h3 className="text-xl font-bold mb-2 text-white">Fleet Intelligence</h3>
                <span className="text-xs font-mono uppercase text-white/50 tracking-wider mb-4 block">Unified Dashboard</span>
                <p className="text-white/60 text-sm leading-relaxed">Monitor assets, components, predictions, anomalies, missions, and maintenance in one unified experience.</p>
              </div>
            </FadeInSection>

          </div>
        </div>
      </section>

      {/* ── Live System Example ── */}
      <section id="use-cases" className="py-24 relative bg-[#060913] border-y border-white/5 overflow-hidden">
        <div className="absolute -left-[20%] top-0 w-[50%] h-full bg-[#AF1763] opacity-[0.02] blur-[120px]"></div>
        <div className="max-w-[1400px] mx-auto px-6">
          <div className="flex flex-col lg:flex-row items-center gap-16">
            
            <div className="lg:w-1/2">
              <FadeInSection>
                <h2 className="text-3xl md:text-4xl font-bold mb-6">Actionable Intelligence <br/>in Real Time</h2>
                <p className="text-white/60 text-lg leading-relaxed mb-8">
                  See exactly how raw telemetry transforms into a clear operational mandate. Problem detected → Evidence identified → Maintenance action deployed.
                </p>
                <ul className="space-y-4">
                  <li className="flex items-center gap-3 text-sm text-white/80"><CheckCircle2 className="h-5 w-5 text-[#AF1763]" /> Traceable decision logic</li>
                  <li className="flex items-center gap-3 text-sm text-white/80"><CheckCircle2 className="h-5 w-5 text-[#AF1763]" /> Zero black-box readiness scoring</li>
                  <li className="flex items-center gap-3 text-sm text-white/80"><CheckCircle2 className="h-5 w-5 text-[#AF1763]" /> Direct alignment with maintenance</li>
                </ul>
              </FadeInSection>
            </div>

            <div className="lg:w-1/2 w-full">
              <FadeInSection delay="delay-200">
                <div className="rounded-xl border border-white/10 bg-[#0a0f1c] shadow-2xl p-6 relative card-hf">
                  <div className="flex justify-between items-center mb-6 pb-6 border-b border-white/5">
                    <div>
                      <div className="text-xs text-white/40 font-mono mb-1">ASSET_ID</div>
                      <div className="text-xl font-bold">AS-1047</div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs text-white/40 font-mono mb-1">STATUS</div>
                      <div className="inline-flex px-3 py-1 rounded bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-bold tracking-wider">NOT READY</div>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 mb-6">
                    <div className="bg-white/[0.02] rounded-lg p-4 border border-white/5">
                      <div className="text-[10px] text-white/40 mb-1 uppercase tracking-wider">Failure Risk</div>
                      <div className="text-lg font-bold text-red-400">High (90%)</div>
                    </div>
                    <div className="bg-white/[0.02] rounded-lg p-4 border border-white/5">
                      <div className="text-[10px] text-white/40 mb-1 uppercase tracking-wider">Anomaly</div>
                      <div className="text-lg font-bold text-amber-400">High</div>
                    </div>
                    <div className="bg-white/[0.02] rounded-lg p-4 border border-white/5">
                      <div className="text-[10px] text-white/40 mb-1 uppercase tracking-wider">Sensor Origin</div>
                      <div className="text-lg font-bold text-white/90">Vibration</div>
                    </div>
                    <div className="bg-white/[0.02] rounded-lg p-4 border border-white/5 bg-[#AF1763]/5 border-[#AF1763]/20">
                      <div className="text-[10px] text-[#AF1763] mb-1 uppercase tracking-wider">Action</div>
                      <div className="text-sm font-bold text-white/90">Inspect & replace bearing</div>
                    </div>
                  </div>
                </div>
              </FadeInSection>
            </div>

          </div>
        </div>
      </section>

      {/* ── Copilot Preview / AI Section ── */}
      <section className="py-24 md:py-32 bg-radar-grid relative">
        <div className="absolute inset-0 bg-[#0a0f1c]/90"></div>
        <div className="max-w-[1400px] mx-auto px-6 relative z-10">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <FadeInSection>
              <h2 className="text-3xl md:text-4xl font-bold mb-4">Ask Instead of Search</h2>
              <p className="text-white/60 text-lg">Use conversational AI to understand complex operational data without manually navigating multiple pages.</p>
            </FadeInSection>
          </div>

          <div className="max-w-4xl mx-auto">
            <FadeInSection delay="delay-100">
              <div className="rounded-2xl border border-white/10 bg-[#141824] shadow-2xl overflow-hidden flex flex-col terminal-hf">
                <div className="h-12 border-b border-white/5 bg-white/[0.02] flex items-center px-6">
                  <div className="flex gap-2">
                    <div className="w-3 h-3 rounded-full bg-red-500/50"></div>
                    <div className="w-3 h-3 rounded-full bg-amber-500/50"></div>
                    <div className="w-3 h-3 rounded-full bg-green-500/50"></div>
                  </div>
                  <div className="mx-auto text-xs font-mono text-white/30 tracking-widest">IBM BOB MCP TERMINAL</div>
                </div>
                <div className="p-6 md:p-10 space-y-8">
                  {/* Human message */}
                  <div className="flex justify-end">
                    <div className="bg-white/10 rounded-2xl rounded-tr-sm px-6 py-4 max-w-[80%] text-sm">
                      Why is AS-1047 not ready?
                    </div>
                  </div>
                  {/* AI message */}
                  <div className="flex gap-4">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#AF1763] to-purple-600 flex items-center justify-center shrink-0">
                      <MessageSquare className="w-5 h-5 text-white" />
                    </div>
                    <div className="bg-white/[0.03] border border-white/5 rounded-2xl rounded-tl-sm px-6 py-5 text-sm leading-relaxed text-white/80 w-full">
                      <p>AS-1047 is currently not ready because the available evidence indicates elevated component risk and an associated vibration anomaly.</p>
                      <br/>
                      <p>The maintenance priority identifies the bearing for inspection and replacement. Would you like me to pull the maintenance history for this component?</p>
                      <div className="mt-4 pt-4 border-t border-white/5 text-[10px] font-mono text-white/30 uppercase tracking-wider flex items-center gap-2">
                        <Zap className="h-3 w-3" /> Powered by IBM watsonx.ai
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </FadeInSection>
          </div>
        </div>
      </section>

      {/* ── IBM Technology Section ── */}
      <section id="about" className="py-24 border-y border-white/5">
        <div className="max-w-[1400px] mx-auto px-6">
          <FadeInSection className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Built with IBM Technology</h2>
            <p className="text-white/60">AssetSentinel separates ML computation, backend decision logic, and AI explanation—an architectural strength powered by IBM.</p>
          </FadeInSection>

          <div className="grid md:grid-cols-3 gap-6">
            <FadeInSection delay="delay-100">
              <div className="p-8 rounded-xl bg-white/[0.01] border border-white/5 h-full card-hf">
                <h3 className="text-lg font-bold text-white mb-2">IBM watsonx.ai</h3>
                <p className="text-sm text-white/60">Natural-language intelligence and tool calling for the web copilot.</p>
              </div>
            </FadeInSection>
            <FadeInSection delay="delay-200">
              <div className="p-8 rounded-xl bg-white/[0.01] border border-white/5 h-full card-hf">
                <h3 className="text-lg font-bold text-white mb-2">IBM Bob</h3>
                <p className="text-sm text-white/60">AI-assisted development environment natively integrated with MCP.</p>
              </div>
            </FadeInSection>
            <FadeInSection delay="delay-300">
              <div className="p-8 rounded-xl bg-white/[0.01] border border-white/5 h-full card-hf">
                <h3 className="text-lg font-bold text-white mb-2">Model Context Protocol</h3>
                <p className="text-sm text-white/60">Connects IBM Bob securely to AssetSentinel's structured, read-only operational tools.</p>
              </div>
            </FadeInSection>
          </div>
        </div>
      </section>

      {/* ── Final CTA ── */}
      <section className="py-32 relative overflow-hidden">
        <div className="absolute inset-0 bg-radial-glow mix-blend-screen opacity-50"></div>
        <div className="max-w-[1400px] mx-auto px-6 relative z-10 text-center">
          <FadeInSection>
            <h2 className="text-4xl md:text-5xl font-bold mb-6">Ready for Mission Control?</h2>
            <p className="text-xl text-white/60 max-w-2xl mx-auto mb-10">
              Explore your fleet, investigate risk, understand readiness, and turn operational data into actionable maintenance intelligence.
            </p>
            <button onClick={onEnter} className="btn-ai px-8 py-4 text-lg shadow-[0_0_30px_rgba(175,23,99,0.4)]">
              Enter Mission Control <ArrowRight className="ml-2 h-5 w-5 btn-icon-hf" />
            </button>
          </FadeInSection>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-white/5 bg-[#060913] py-12 text-sm text-white/40">
        <div className="max-w-[1400px] mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-white/20" />
            <span className="font-semibold text-white/60">AssetSentinel</span>
          </div>
          <div className="flex gap-6">
            <a href="#features" className="nav-link-hf">Features</a>
            <a href="#how-it-works" className="nav-link-hf">How It Works</a>
            <a href="#use-cases" className="nav-link-hf">Use Cases</a>
          </div>
          <div className="text-xs tracking-wider">
            ML detects. Evidence combines. Readiness decides. Maintenance prioritizes. AI explains.
          </div>
        </div>
      </footer>

    </div>
  );
}
