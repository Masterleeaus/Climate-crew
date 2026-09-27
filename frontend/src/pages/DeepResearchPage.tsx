import React, { useEffect, useRef, useState } from 'react';
import { AlertCircle, ArrowRight, BookOpen, Check, Download, FlaskConical, Globe2, Microscope, Network, Scale, ShieldCheck, Users } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

interface Source { title: string; url: string; type: 'web' | 'file' | 'db'; }
interface ResearchResult { report: string; sources: Source[]; }

const PHASES = [
  { label: 'Frame the research question', icon: Microscope },
  { label: 'Generate competing hypotheses', icon: FlaskConical },
  { label: 'Dispatch independent research agents', icon: Users },
  { label: 'Collect and cross-check evidence', icon: Network },
  { label: 'Adversarial challenge', icon: Scale },
  { label: 'Assess replication and uncertainty', icon: ShieldCheck },
  { label: 'Synthesize findings', icon: BookOpen },
];

const DeepResearchPage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ResearchResult | null>(null);
  const [phase, setPhase] = useState(0);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const reportRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!textareaRef.current) return;
    textareaRef.current.style.height = 'auto';
    textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
  }, [query]);

  const handleResearch = async () => {
    if (!query.trim()) return;
    setLoading(true); setResult(null); setPhase(0);
    let current = 0;
    const timer = window.setInterval(() => {
      current = Math.min(current + 1, PHASES.length - 1);
      setPhase(current);
    }, 6500);
    try {
      const res = await fetch('http://localhost:8000/deep-research/', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query })
      });
      if (!res.ok) throw new Error(`Research request failed: ${res.status}`);
      setResult(await res.json());
    } catch (error) {
      console.error(error);
    } finally {
      window.clearInterval(timer); setPhase(PHASES.length - 1); setLoading(false);
    }
  };

  const handleExportPDF = async () => {
    if (!reportRef.current) return;
    const canvas = await html2canvas(reportRef.current, { scale: 2, backgroundColor: '#ffffff' });
    const img = canvas.toDataURL('image/png');
    const pdf = new jsPDF('p', 'mm', 'a4');
    const width = pdf.internal.pageSize.getWidth();
    const pageHeight = pdf.internal.pageSize.getHeight();
    const height = canvas.height * width / canvas.width;
    let remaining = height;
    let position = 0;
    pdf.addImage(img, 'PNG', 0, position, width, height); remaining -= pageHeight;
    while (remaining > 0) { position = remaining - height; pdf.addPage(); pdf.addImage(img, 'PNG', 0, position, width, height); remaining -= pageHeight; }
    pdf.save(`climate-crew-investigation-${Date.now()}.pdf`);
  };

  if (result || loading) return (
    <div className="w-full h-full overflow-y-auto px-4 py-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <div className="text-xs uppercase tracking-[0.25em] text-cyan-400 mb-2">Climate Crew / Investigation</div>
          <h1 className="text-2xl md:text-3xl font-bold text-white">{query}</h1>
          <p className="text-gray-500 mt-2">A research question is not treated as settled until evidence survives challenge.</p>
        </div>

        {loading && <div className="grid lg:grid-cols-[1fr_320px] gap-6">
          <div className="border border-white/10 bg-white/[0.03] rounded-2xl p-7">
            <h2 className="text-xl font-bold text-white mb-2">Research crew at work</h2>
            <p className="text-gray-400 mb-7">Independent paths are being assembled before synthesis to reduce single-agent anchoring.</p>
            <div className="space-y-3">{PHASES.map((item, index) => {
              const Icon = item.icon; const done = index < phase; const active = index === phase;
              return <div key={item.label} className={`flex items-center gap-4 p-4 rounded-xl border ${active ? 'border-cyan-400/50 bg-cyan-400/5' : 'border-white/5 bg-black/20'}`}>
                <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${done ? 'bg-emerald-400/10 text-emerald-400' : active ? 'bg-cyan-400/10 text-cyan-400' : 'bg-white/5 text-gray-600'}`}>{done ? <Check size={17}/> : <Icon size={17}/>}</div>
                <span className={active ? 'text-white' : done ? 'text-gray-400' : 'text-gray-600'}>{item.label}</span>
              </div>;
            })}</div>
          </div>
          <aside className="space-y-4">
            {[['Independent agents','Multiple research paths before convergence'],['Evidence first','Claims should remain traceable to sources'],['Adversarial pass','Counter-evidence and alternative explanations are required'],['Uncertainty retained','Unknowns remain visible instead of being smoothed away']].map(([a,b]) => <div key={a} className="p-5 border border-white/10 rounded-xl bg-black/30"><div className="text-sm font-semibold text-white">{a}</div><div className="text-xs text-gray-500 mt-1">{b}</div></div>)}
          </aside>
        </div>}

        {result && !loading && <div ref={reportRef} className="space-y-6">
          <div className="grid md:grid-cols-4 gap-3">
            {[['Status','Synthesis complete'],['Evidence',`${result.sources?.length || 0} sources returned`],['Validation','Challenge required'],['Confidence','Evidence-dependent']].map(([a,b]) => <div key={a} className="border border-white/10 rounded-xl p-4 bg-white/[0.03]"><div className="text-[10px] uppercase tracking-widest text-gray-500">{a}</div><div className="text-sm text-white mt-2">{b}</div></div>)}
          </div>

          <section className="border border-white/10 rounded-2xl bg-[#0a0a0a] p-5 md:p-8">
            <div className="flex flex-wrap justify-between gap-3 items-center mb-7">
              <div><div className="text-xs uppercase tracking-widest text-cyan-400">Research synthesis</div><h2 className="text-2xl font-bold text-white mt-1">Current finding</h2></div>
              <button onClick={handleExportPDF} className="flex items-center gap-2 px-3 py-2 border border-cyan-400/30 text-cyan-300 rounded-lg text-xs hover:bg-cyan-400/10"><Download size={14}/> Export investigation</button>
            </div>
            <div className="prose prose-invert max-w-none prose-a:text-cyan-400 prose-headings:text-white prose-strong:text-white text-gray-300"><ReactMarkdown remarkPlugins={[remarkGfm]}>{result.report || ''}</ReactMarkdown></div>
          </section>

          <section className="border border-white/10 rounded-2xl p-5 md:p-8 bg-white/[0.02]">
            <div className="flex items-center gap-2 mb-5"><Network className="text-cyan-400" size={18}/><h2 className="font-bold text-white">Evidence register</h2></div>
            {result.sources?.length ? <div className="grid md:grid-cols-2 gap-3">{result.sources.map((source,i) => <a key={`${source.url}-${i}`} href={source.url} target="_blank" rel="noreferrer" className="p-4 rounded-xl border border-white/10 bg-black/30 hover:border-cyan-400/40"><div className="text-[10px] text-cyan-400 uppercase tracking-wider">Evidence {i+1} · {source.type}</div><div className="text-sm text-white mt-1">{source.title}</div><div className="text-xs text-gray-600 truncate mt-1">{source.url}</div></a>)}</div> : <div className="flex items-center gap-2 text-amber-300 text-sm"><AlertCircle size={15}/> No external sources were returned. Treat this synthesis as unverified.</div>}
          </section>
        </div>}
      </div>
    </div>
  );

  return <div className="h-full w-full overflow-y-auto px-4 py-10">
    <div className="max-w-5xl mx-auto">
      <div className="text-center max-w-3xl mx-auto mb-10">
        <div className="inline-flex items-center gap-2 text-xs uppercase tracking-[0.28em] text-cyan-400 mb-4"><Globe2 size={15}/> Climate Crew Research</div>
        <h1 className="text-4xl md:text-6xl font-black text-white tracking-tight">Start an investigation,<br/><span className="text-cyan-400">not just a search.</span></h1>
        <p className="text-gray-400 text-lg mt-5">Give the crew a climate question, anomaly, proposed intervention, dataset or disputed claim. The system separates hypotheses, evidence and challenge before synthesis.</p>
      </div>

      <div className="border border-white/10 bg-[#0a0a0a] rounded-2xl p-3 shadow-2xl">
        <textarea ref={textareaRef} value={query} onChange={e=>setQuery(e.target.value)} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();handleResearch();}}} placeholder="Example: Could accelerated mineral weathering materially reduce atmospheric CO₂ without creating unacceptable watershed impacts?" rows={3} className="w-full bg-transparent resize-none outline-none text-white text-lg p-4 min-h-[110px]"/>
        <div className="flex flex-wrap justify-between items-center gap-3 border-t border-white/5 pt-3 px-2 pb-1">
          <div className="flex gap-2 text-[10px] uppercase tracking-wider text-gray-500"><span className="px-2 py-1 border border-white/10 rounded">Competing hypotheses</span><span className="px-2 py-1 border border-white/10 rounded">Source traceability</span><span className="px-2 py-1 border border-white/10 rounded">Challenge pass</span></div>
          <button onClick={handleResearch} disabled={!query.trim()} className="flex items-center gap-2 px-5 py-3 bg-cyan-400 text-black font-bold rounded-xl disabled:opacity-30">Begin investigation <ArrowRight size={17}/></button>
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-4 mt-8">
        {[['01','Investigate','Frame the question and deliberately generate alternatives before convergence.'],['02','Challenge','Look for contradictory evidence, confounders and explanations that would falsify the leading claim.'],['03','Accumulate','Preserve sources and findings so future investigations can build on prior evidence rather than restart.']].map(([n,a,b])=><div key={n} className="p-5 border border-white/10 rounded-xl bg-white/[0.02]"><div className="text-cyan-400 font-mono text-xs">{n}</div><div className="text-white font-semibold mt-2">{a}</div><div className="text-gray-500 text-sm mt-2">{b}</div></div>)}
      </div>
    </div>
  </div>;
};

export default DeepResearchPage;
