import { useNavigate } from 'react-router-dom';
import { ArrowRight, BarChart3, Database, FlaskConical, Network, ShieldCheck, Telescope } from 'lucide-react';

const capabilities = [
  {
    icon: BarChart3,
    status: 'Implemented and tested',
    title: 'Reproducible climate result',
    description: 'A pinned NASA GISTEMP v4 snapshot, Mann–Kendall trend test, Sen slope, block-bootstrap interval, endpoint sensitivity check, JSON report, and SVG plot.',
  },
  {
    icon: Database,
    status: 'Prototype',
    title: 'Climate data connectors',
    description: 'The repository contains climate and environmental data-source adapters. Provider availability and data quality still depend on each integration.',
  },
  {
    icon: Telescope,
    status: 'Prototype',
    title: 'Multi-agent research',
    description: 'A deep-research orchestrator coordinates planning, search, debate, and synthesis. It depends on external model and search credentials.',
  },
  {
    icon: Network,
    status: 'Bounded slice',
    title: 'Evidence and hypotheses',
    description: 'Typed records connect two hypotheses, source-attributed evidence, one falsification test, uncertainty, and a report for the GISTEMP case.',
  },
  {
    icon: ShieldCheck,
    status: 'Planned',
    title: 'Project-wide validation',
    description: 'A persistent evidence graph, independent dataset replication, and expert approval gates are not yet integrated across the application.',
  },
];

const LandingPage = () => {
  const navigate = useNavigate();

  return <div className="min-h-screen bg-slate-950 text-white selection:bg-cyan-400 selection:text-black">
    <header className="sticky top-0 z-40 px-6 md:px-10 py-4 flex justify-between items-center border-b border-white/10 bg-slate-950/90 backdrop-blur-xl">
      <button onClick={() => navigate('/')} className="flex items-center gap-3 text-left">
        <span className="flex h-11 w-11 items-center justify-center rounded-xl border border-cyan-300/30 bg-cyan-300/10 text-cyan-200"><FlaskConical size={22}/></span>
        <span><span className="block text-xl font-black tracking-[0.12em]">CLIMATE CREW</span><span className="block text-[9px] uppercase tracking-[0.24em] text-gray-500">Research prototype</span></span>
      </button>
      <button onClick={() => navigate('/app/research')} className="px-4 md:px-6 py-2.5 border border-cyan-400/40 text-cyan-200 hover:bg-cyan-400 hover:text-black transition-all uppercase tracking-[0.14em] text-xs font-bold rounded-lg">Open research</button>
    </header>

    <main>
      <section className="px-6 md:px-10 py-20 md:py-28 border-b border-white/10 bg-[radial-gradient(circle_at_50%_0%,rgba(6,182,212,0.16),transparent_55%)]">
        <div className="max-w-5xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-amber-300/20 bg-amber-300/5 text-amber-200 text-xs uppercase tracking-[0.18em] mb-6">Active climate research prototype</div>
          <h1 className="text-4xl md:text-6xl font-black tracking-tight">Evidence first. <span className="text-cyan-300">Claims kept in scope.</span></h1>
          <p className="mt-6 text-lg text-gray-300 max-w-4xl mx-auto">Climate Crew is a climate and environmental research codebase with specialist agents, data connectors, and a multi-agent research prototype. Its complete application is not yet validated as a scientific workflow.</p>
          <div className="mt-9 flex justify-center gap-3 flex-wrap">
            <button onClick={() => navigate('/app/research')} className="px-6 py-3 bg-cyan-400 text-black font-black uppercase tracking-[0.12em] text-xs md:text-sm rounded-lg flex items-center gap-2">Open research prototype <ArrowRight size={17}/></button>
            <a href="https://github.com/Masterleeaus/Climate-crew" className="px-6 py-3 border border-white/25 text-gray-200 hover:bg-white/10 rounded-lg text-xs md:text-sm font-bold uppercase tracking-[0.12em]">View code and results</a>
          </div>
        </div>
      </section>

      <section className="px-6 md:px-10 py-16 md:py-20">
        <div className="max-w-7xl mx-auto">
          <div className="max-w-3xl mb-10"><p className="text-xs uppercase tracking-[0.24em] text-cyan-300 mb-3">Capability status</p><h2 className="text-3xl md:text-5xl font-black">What the repository supports today</h2><p className="mt-4 text-gray-400">Each label describes the current code and test boundary, not a product-readiness claim.</p></div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
            {capabilities.map(({ icon: Icon, status, title, description }) => <article key={title} className="p-6 rounded-2xl border border-white/10 bg-white/[0.025]">
              <div className="flex items-center justify-between gap-3 mb-5"><span className="w-10 h-10 rounded-xl bg-cyan-400/10 border border-cyan-400/20 flex items-center justify-center"><Icon className="w-5 h-5 text-cyan-300"/></span><span className="text-[10px] uppercase tracking-[0.12em] text-gray-400">{status}</span></div>
              <h3 className="text-lg font-bold mb-3">{title}</h3><p className="text-sm leading-relaxed text-gray-400">{description}</p>
            </article>)}
          </div>
        </div>
      </section>

      <section className="px-6 md:px-10 py-16 border-y border-white/10 bg-white/[0.02]">
        <div className="max-w-5xl mx-auto"><p className="text-xs uppercase tracking-[0.24em] text-cyan-300 mb-3">Reproducible path</p><h2 className="text-3xl md:text-4xl font-black">One result can be rerun without API keys.</h2><p className="mt-5 text-gray-400">The GISTEMP analysis uses a checked-in NASA data snapshot and reports its source, hash, trend test, uncertainty interval, sensitivity check, and limits. CI checks the output and runs offline tests; it does not score model performance.</p><a href="https://github.com/Masterleeaus/Climate-crew/tree/main/analysis" className="mt-6 inline-flex items-center gap-2 text-cyan-200 hover:text-cyan-100 font-semibold">Open the analysis code <ArrowRight size={16}/></a></div>
      </section>

      <section className="px-6 md:px-10 py-20"><div className="max-w-5xl mx-auto text-center"><p className="text-xs uppercase tracking-[0.24em] text-cyan-300 mb-4">Research principle</p><h2 className="text-4xl md:text-5xl font-black">Agreement is not evidence.</h2><p className="mt-6 text-lg text-gray-400 max-w-3xl mx-auto">A useful research system must expose its sources, methods, uncertainty, and remaining gaps so another person can challenge the result.</p></div></section>
    </main>

    <footer className="border-t border-white/10 px-6 md:px-10 py-6 text-xs text-gray-500"><div className="max-w-7xl mx-auto flex flex-col md:flex-row gap-3 md:justify-between"><span>Climate Crew — climate research prototype.</span><span>Inspect the evidence · Reproduce the result · Challenge the limits</span></div></footer>
  </div>;
};

export default LandingPage;
