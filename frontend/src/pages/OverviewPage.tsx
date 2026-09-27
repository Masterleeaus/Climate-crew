import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Activity, AlertTriangle, ArrowRight, BookOpen, Clock, ExternalLink, Globe2, MessageCircle, Microscope, Network, Scale, ShieldCheck, Users } from 'lucide-react';
import { useCachedFetch } from '../hooks/useCachedFetch';
import NewsChatModal from '../components/NewsChatModal';
import { NewsArticle } from '../services/newsApi';

const OverviewPage: React.FC = () => {
  const [selectedArticle, setSelectedArticle] = useState<NewsArticle | null>(null);
  const [isChatModalOpen, setIsChatModalOpen] = useState(false);

  const { data: stats, loading, isFromCache, isRefreshing } = useCachedFetch<any>('http://localhost:8000/global/summary', {
    cacheKey: 'global-summary', maxAge: 2 * 60 * 1000,
  });
  const { data: newsData, loading: newsLoading } = useCachedFetch<NewsArticle[]>('http://localhost:8000/news?limit=6', {
    cacheKey: 'news-articles', maxAge: 5 * 60 * 1000,
    transform: data => Array.isArray(data) ? data : [],
  });

  const metrics = stats?.metrics || [];
  const news = newsData || [];

  const researchStages = [
    ['Question', 'Frame a falsifiable research problem', Microscope],
    ['Hypotheses', 'Generate competing explanations', Network],
    ['Evidence', 'Collect attributable observations and sources', BookOpen],
    ['Challenge', 'Search for contradictions and alternatives', Scale],
    ['Replication', 'Test findings independently', ShieldCheck],
  ] as const;

  const formatDate = (value: string) => {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return 'Recent';
    const hours = Math.floor((Date.now() - date.getTime()) / 3600000);
    if (hours < 1) return 'Just now';
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
  };

  return <div className="p-5 md:p-8 text-white max-w-[1600px] mx-auto space-y-8 animate-fade-in">
    <header className="border-b border-white/10 pb-7 flex flex-col xl:flex-row xl:items-end justify-between gap-6">
      <div className="max-w-3xl">
        <div className="flex items-center gap-2 text-cyan-400 text-xs uppercase tracking-[0.25em] mb-3"><Globe2 size={15}/> Climate Crew Research Command</div>
        <h1 className="text-4xl md:text-6xl font-black tracking-tight">Investigate the planet.<br/><span className="text-cyan-400">Preserve the evidence.</span></h1>
        <p className="text-gray-400 mt-4 max-w-2xl">Coordinate climate research agents, Earth observations, scientific sources, competing hypotheses and validation from one research workspace.</p>
      </div>
      <div className="flex gap-3">
        <Link to="/app/research" className="flex items-center gap-2 px-5 py-3 rounded-xl bg-cyan-400 text-black font-bold">Start investigation <ArrowRight size={16}/></Link>
        <Link to="/app/globe" className="flex items-center gap-2 px-5 py-3 rounded-xl border border-white/15 bg-white/5 text-white">Earth Observatory <Globe2 size={16}/></Link>
      </div>
    </header>

    <section className="grid lg:grid-cols-[1.35fr_.65fr] gap-6">
      <div className="border border-white/10 rounded-2xl bg-white/[0.025] p-6">
        <div className="flex justify-between gap-4 mb-6"><div><div className="text-xs uppercase tracking-widest text-gray-500">Research lifecycle</div><h2 className="text-2xl font-bold mt-1">Evidence before consensus</h2></div><Activity className="text-cyan-400"/></div>
        <div className="grid md:grid-cols-5 gap-3">{researchStages.map(([title,description,Icon],i)=><div key={title} className="border border-white/10 rounded-xl p-4 bg-black/20"><div className="flex justify-between"><Icon size={18} className="text-cyan-400"/><span className="text-[10px] font-mono text-gray-600">0{i+1}</span></div><div className="font-semibold mt-4">{title}</div><div className="text-xs text-gray-500 mt-2 leading-relaxed">{description}</div></div>)}</div>
      </div>
      <div className="border border-white/10 rounded-2xl bg-black/30 p-6">
        <div className="text-xs uppercase tracking-widest text-gray-500">Workspace state</div>
        <div className="space-y-4 mt-5">
          {[['Research crew','Ready',Users],['Earth data',loading && !stats ? 'Connecting' : 'Available',Globe2],['Evidence discipline','Required',BookOpen],['Adversarial validation','Enabled',Scale]].map(([label,value,Icon]:any)=><div key={label} className="flex items-center gap-3 border-b border-white/5 pb-3"><div className="w-9 h-9 rounded-lg bg-cyan-400/10 text-cyan-400 flex items-center justify-center"><Icon size={17}/></div><div className="flex-1"><div className="text-sm text-white">{label}</div><div className="text-xs text-gray-600">{value}</div></div></div>)}
        </div>
        {(isFromCache || isRefreshing) && <div className="text-[10px] text-gray-600 mt-4">Earth observations {isRefreshing ? 'refreshing in background' : 'served from recent cache'}.</div>}
      </div>
    </section>

    <section>
      <div className="flex items-end justify-between mb-4"><div><div className="text-xs uppercase tracking-widest text-gray-500">Earth Observatory</div><h2 className="text-2xl font-bold mt-1">Current environmental signals</h2></div><Link to="/app/globe" className="text-sm text-cyan-400 flex items-center gap-1">Open observatory <ArrowRight size={14}/></Link></div>
      <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-4">{[0,1,2,3].map(i=>{const metric=metrics[i]; return <div key={i} className="border border-white/10 rounded-xl p-5 bg-white/[0.02]"><div className="text-[10px] uppercase tracking-widest text-gray-600">{metric?.location_name || ['Atmosphere','Air quality','Fire conditions','Marine systems'][i]}</div><div className="text-3xl font-black mt-3">{metric?.value ?? '--'}</div><div className="text-xs text-gray-500 mt-2">{metric?.details || 'Awaiting observation data'}</div>{metric?.delta && <div className="text-xs text-cyan-400 mt-3">{metric.delta}</div>}</div>})}</div>
      <p className="text-xs text-gray-600 mt-3">Observational signals are research inputs, not conclusions. Provenance and measurement context should be retained before a signal supports a scientific claim.</p>
    </section>

    <section className="grid xl:grid-cols-[1fr_360px] gap-6">
      <div>
        <div className="flex items-end justify-between mb-4"><div><div className="text-xs uppercase tracking-widest text-gray-500">Research signals</div><h2 className="text-2xl font-bold mt-1">Climate & environmental literature feed</h2></div></div>
        {newsLoading && !news.length ? <div className="border border-white/10 rounded-xl p-6 text-gray-500">Collecting research signals…</div> : <div className="grid md:grid-cols-2 gap-4">{news.slice(0,6).map((article,i)=><article key={`${article.url}-${i}`} className="border border-white/10 rounded-xl p-5 bg-white/[0.02] flex flex-col"><div className="flex justify-between gap-3 text-[10px] uppercase tracking-wider"><span className="text-cyan-400">{article.source}</span><span className="text-gray-600 flex items-center gap-1"><Clock size={11}/>{formatDate(article.published_at)}</span></div><a href={article.url} target="_blank" rel="noreferrer" className="font-semibold text-white mt-3 hover:text-cyan-400">{article.title}</a>{article.summary && <p className="text-sm text-gray-500 mt-2 line-clamp-3">{article.summary.replace(/<[^>]*>/g,'')}</p>}<div className="flex gap-2 mt-auto pt-4"><button onClick={()=>{setSelectedArticle(article);setIsChatModalOpen(true);}} className="text-xs flex items-center gap-1 text-cyan-400"><MessageCircle size={13}/> Investigate</button><a href={article.url} target="_blank" rel="noreferrer" className="text-xs flex items-center gap-1 text-gray-500"><ExternalLink size={13}/> Source</a></div></article>)}</div>}
      </div>
      <aside className="space-y-4">
        <div className="border border-white/10 rounded-2xl p-6 bg-white/[0.02]"><div className="text-xs uppercase tracking-widest text-gray-500">Scientific guardrails</div><div className="space-y-4 mt-5">{[['Source independence','Repeated reporting from one dataset is not independent confirmation.'],['Contradictions','Conflicting evidence remains visible and investigable.'],['Uncertainty','Observed, inferred, modelled and unknown states remain distinct.'],['Human validation','Discovery candidates do not become scientific truth by agent vote.']].map(([a,b])=><div key={a}><div className="text-sm font-semibold">{a}</div><div className="text-xs text-gray-500 mt-1 leading-relaxed">{b}</div></div>)}</div></div>
        <div className="border border-amber-400/20 rounded-xl p-5 bg-amber-400/[0.03]"><div className="flex gap-2 items-center text-amber-300 text-sm font-semibold"><AlertTriangle size={15}/> Research integrity</div><p className="text-xs text-gray-500 mt-2">Synthetic, simulated and fallback information must remain distinguishable from observations throughout the evidence chain.</p></div>
      </aside>
    </section>

    {selectedArticle && <NewsChatModal article={selectedArticle} isOpen={isChatModalOpen} onClose={()=>{setIsChatModalOpen(false);setSelectedArticle(null);}} />}
  </div>;
};

export default OverviewPage;
