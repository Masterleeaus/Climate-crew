import { useNavigate } from 'react-router-dom';
import { ArrowRight, Database, FlaskConical, Globe2, Microscope, Network, SearchCheck, ShieldCheck } from 'lucide-react';

const capabilities = [
  [Microscope, 'Specialist Research Crew', 'Coordinate climate, Earth-system and research-method agents around shared scientific questions.'],
  [Network, 'Evidence Graph', 'Connect claims to sources, datasets, observations, methods, assumptions, contradictions and replication history.'],
  [SearchCheck, 'Adversarial Validation', 'Challenge findings through competing explanations, falsification, replication, uncertainty and novelty review.'],
  [Globe2, 'Earth Observatory', 'Bring live and historical Earth-observation data into the same workspace as literature, models and simulations.'],
  [Database, 'Research Memory', 'Preserve hypotheses, evidence, rejected explanations and unresolved questions across long-running projects.'],
  [ShieldCheck, 'Traceable Discovery', 'Advance findings only with visible provenance, uncertainty, replication and validation history.'],
] as const;

const LandingPage = () => {
  const navigate = useNavigate();

  return <div className="min-h-screen bg-black text-white selection:bg-cyan-400 selection:text-black">
    <header className="sticky top-0 z-40 px-6 md:px-10 py-5 flex justify-between items-center border-b border-white/10 bg-black/80 backdrop-blur-xl">
      <button onClick={() => navigate('/')} className="flex items-center gap-3 text-left">
        <div className="w-10 h-10 rounded-xl border border-cyan-400/30 bg-cyan-400/10 flex items-center justify-center"><Globe2 className="text-cyan-300" /></div>
        <div><div className="text-xl md:text-2xl font-black tracking-[0.12em]">CLIMATE <span className="text-cyan-300">CREW</span></div><div className="text-[9px] uppercase tracking-[0.28em] text-gray-500">Climate Research Agent Team</div></div>
      </button>
      <button onClick={() => navigate('/app/research')} className="px-4 md:px-6 py-2.5 border border-cyan-400/40 text-cyan-200 hover:bg-cyan-400 hover:text-black transition-all uppercase tracking-[0.18em] text-[10px] md:text-xs font-bold rounded-lg">Open Research</button>
    </header>

    <main>
      <section className="px-6 md:px-10 py-20 md:py-28 bg-[radial-gradient(circle_at_50%_0%,rgba(6,182,212,0.14),transparent_40%)]">
        <div className="max-w-7xl mx-auto grid lg:grid-cols-[1.1fr_.9fr] gap-14 items-center">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-cyan-400/20 bg-cyan-400/5 text-cyan-200 text-xs uppercase tracking-[0.18em] mb-7"><FlaskConical size={14}/> Evidence-driven multi-agent research</div>
            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-black tracking-tight leading-[0.95]">From data and questions to <span className="text-cyan-300">validated climate discovery.</span></h1>
            <p className="mt-7 text-lg md:text-xl text-gray-300 max-w-3xl leading-relaxed">Climate Crew coordinates specialised research agents, Earth observations, literature, datasets, models and simulations through a process built for independent investigation, transparent evidence, open challenge and reproducible validation.</p>
            <p className="mt-4 text-gray-500">Agreement is not evidence. Scientific claims advance because the supporting evidence survives scrutiny.</p>
            <div className="mt-9 flex flex-wrap gap-4"><button onClick={() => navigate('/app/research')} className="px-7 py-4 bg-cyan-400 text-black font-black uppercase tracking-[0.12em] text-sm rounded-lg flex items-center gap-3">Start Research <ArrowRight size={18}/></button><button onClick={() => navigate('/app/globe')} className="px-7 py-4 border border-white/15 bg-white/[0.03] font-bold uppercase tracking-[0.12em] text-sm rounded-lg">Earth Observatory</button></div>
          </div>
          <img src="/docs/images/climate-crew-architecture-dark.jpg" alt="Climate Crew research engine, agent team, Earth Observatory, discovery scouts, adversarial truth-seeking and discovery lifecycle" className="w-full rounded-2xl border border-cyan-400/20 shadow-[0_0_70px_rgba(34,211,238,0.12)]" />
        </div>
      </section>

      <section className="border-y border-white/10 bg-white/[0.02] px-6 md:px-10 py-20">
        <div className="max-w-7xl mx-auto">
          <div className="max-w-3xl mb-10"><p className="text-xs uppercase tracking-[0.24em] text-cyan-300 mb-3">System architecture</p><h2 className="text-3xl md:text-5xl font-black">The whole research system at a glance.</h2><p className="mt-5 text-gray-400 text-lg">The platform connects the research lifecycle, specialist crew, Evidence Graph, Earth Observatory, Discovery Scouts and validation gates into one scientific workflow.</p></div>
          <img src="/docs/images/climate-crew-architecture-light.jpg" alt="Climate Crew platform architecture overview" className="w-full rounded-2xl border border-white/10 bg-white shadow-2xl" />
        </div>
      </section>

      <section className="px-6 md:px-10 py-20">
        <div className="max-w-7xl mx-auto"><div className="max-w-3xl mb-12"><p className="text-xs uppercase tracking-[0.24em] text-cyan-300 mb-3">Research architecture</p><h2 className="text-3xl md:text-5xl font-black">A research system, not a chatbot.</h2></div><div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">{capabilities.map(([Icon,title,description]) => <article key={title} className="p-6 rounded-2xl border border-white/10 bg-white/[0.025]"><div className="w-10 h-10 rounded-xl bg-cyan-400/10 border border-cyan-400/20 flex items-center justify-center mb-5"><Icon className="w-5 h-5 text-cyan-300"/></div><h3 className="text-lg font-bold mb-3">{title}</h3><p className="text-sm leading-relaxed text-gray-400">{description}</p></article>)}</div></div>
      </section>

      <section className="px-6 md:px-10 py-24 border-t border-white/10"><div className="max-w-5xl mx-auto text-center"><p className="text-xs uppercase tracking-[0.24em] text-cyan-300 mb-4">From investigation to discovery</p><h2 className="text-4xl md:text-6xl font-black">Discover carefully.</h2><p className="mt-6 text-lg text-gray-400 max-w-3xl mx-auto">Preserve disagreement, expose uncertainty and keep the path from observation to externally validated discovery auditable.</p><button onClick={() => navigate('/app/research')} className="mt-10 inline-flex items-center gap-3 px-8 py-4 border border-cyan-400/40 text-cyan-200 hover:bg-cyan-400 hover:text-black rounded-lg font-bold uppercase tracking-[0.14em] text-sm">Enter Climate Crew <ArrowRight size={18}/></button></div></section>
    </main>

    <footer className="border-t border-white/10 px-6 md:px-10 py-6 text-xs text-gray-500"><div className="max-w-7xl mx-auto flex flex-col md:flex-row gap-3 md:justify-between"><span>Climate Crew — evidence-driven multi-agent climate research and discovery.</span><span>Investigate independently · Challenge aggressively · Preserve the evidence · Discover carefully</span></div></footer>
  </div>;
};

export default LandingPage;
