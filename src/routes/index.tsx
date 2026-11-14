import { useMemo, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import {
  Activity, ArrowDown, ArrowRight, ArrowUp, CalendarDays, Check, ChevronDown, ChevronRight,
  CircleHelp, ClipboardList, Database, FileText, FlaskConical, HeartPulse, Info, LockKeyhole,
  Menu, MessageCircleHeart, MoreHorizontal, Plus, ShieldCheck, SlidersHorizontal, Sparkles,
  Users, X, Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";

type Persona = {
  id: string;
  name: string;
  age: number;
  initials: string;
  visits: number;
  labs: number;
  lastSeen: string;
  amh: number[];
  fsh: number[];
  recorded: string[];
  summary: string;
};

const personas: Persona[] = [
  { id: "demo-001", name: "Alex Morgan", age: 31, initials: "AM", visits: 4, labs: 4, lastSeen: "Mar 2, 2026", amh: [2.8, 2.5, 2.4], fsh: [6.7, 6.9, 7.1], recorded: ["Profile", "Reproductive history", "Lifestyle", "Lab results"], summary: "Cycle notes and selected clinician-entered laboratory results across four visits." },
  { id: "demo-002", name: "Jordan Lee", age: 36, initials: "JL", visits: 3, labs: 0, lastSeen: "Apr 20, 2026", amh: [], fsh: [], recorded: ["Profile", "Reproductive history", "Lifestyle"], summary: "History entered across three visits; laboratory results are not shared." },
  { id: "demo-003", name: "Sam Rivera", age: 29, initials: "SR", visits: 3, labs: 0, lastSeen: "May 11, 2026", amh: [], fsh: [], recorded: ["Profile", "Lifestyle"], summary: "Self-entered lifestyle notes across three visits; no labs recorded." },
  { id: "demo-004", name: "Taylor Chen", age: 34, initials: "TC", visits: 3, labs: 4, lastSeen: "Apr 13, 2026", amh: [], fsh: [6.8, 7.2], recorded: ["Profile", "Reproductive history", "Lab results"], summary: "Two reported hormone results over three visits; other records remain unshared." },
  { id: "demo-005", name: "Casey Patel", age: 32, initials: "CP", visits: 2, labs: 0, lastSeen: "Mar 9, 2026", amh: [], fsh: [], recorded: ["Profile", "Reproductive history"], summary: "Sparse follow-up history with several categories not shared." },
];

const navigation = [
  { label: "Overview", icon: HeartPulse },
  { label: "People", icon: Users },
  { label: "Cohort insights", icon: Activity },
  { label: "Guidelines", icon: FileText },
  { label: "Audit trail", icon: ClipboardList },
];

const categories = ["Profile", "Reproductive history", "Lifestyle", "Conditions", "Lab results", "Device data"];

const guidance = [
  { org: "ASRM", title: "Ovarian reserve testing", year: "2020", url: "https://www.asrm.org/practice-guidance/practice-committee-documents/testing-and-interpreting-measures-of-ovarian-reserve-a-committee-opinion-2020/" },
  { org: "NICE", title: "Fertility problems: assessment & treatment", year: "2026", url: "https://www.nice.org.uk/guidance/ng257" },
  { org: "WHO", title: "Infertility prevention, diagnosis & treatment", year: "2025", url: "https://www.who.int/publications/i/item/9789240115774" },
  { org: "ESHRE", title: "Female fertility preservation", year: "2020", url: "https://www.eshre.eu/Guidelines-and-Legal/Guidelines/Female-Fertility-Preservation" },
];

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Tide | Reproductive health trends" },
      { name: "description", content: "A privacy-first reproductive health monitoring demonstration. Explore synthetic longitudinal trends, transparent data permissions, and cited evidence." },
      { property: "og:title", content: "Tide | Reproductive health trends" },
      { property: "og:description", content: "Synthetic-data prototype for privacy-first reproductive health trend monitoring." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
    links: [
      { rel: "preconnect", href: "https://fonts.googleapis.com" },
      { rel: "preconnect", href: "https://fonts.gstatic.com", crossOrigin: "anonymous" },
      { rel: "stylesheet", href: "https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap" },
    ],
  }),
  component: MonitoringDashboard,
});

function TrendChart({ person, period }: { person: Persona; period: string }) {
  const labels = period === "1Y" ? ["Jun '25", "Sep '25", "Dec '25", "Mar '26"] : ["Feb '26", "Mar '26", "Apr '26", "May '26"];
  if (!person.amh.length || !person.fsh.length) {
    return (
      <div className="grid h-[225px] place-items-center rounded border border-dashed border-border bg-surface-raised px-7 text-center">
        <div className="max-w-xs">
          <div className="mx-auto mb-3 grid h-10 w-10 place-items-center rounded-full bg-brand-wash text-primary"><FlaskConical size={18} /></div>
          <p className="text-sm font-semibold">No repeat lab results to chart</p>
          <p className="mt-1 text-xs leading-relaxed text-muted-foreground">This record doesn’t include comparable values over time. Missing data stays visible—not filled in.</p>
        </div>
      </div>
    );
  }
  const paths = useMemo(() => {
    const toCoordinates = (values: number[], min: number, max: number) => values.map((value, index) => ({
      x: 75 + (index * 330) / Math.max(values.length - 1, 1),
      y: 185 - ((value - min) / (max - min)) * 125,
      value,
    }));
    const first = toCoordinates(person.amh, 1.5, 3.5);
    const second = toCoordinates(person.fsh, 5, 9);
    return {
      first,
      second,
      firstPath: first.map((point, index) => `${index ? "L" : "M"} ${point.x} ${point.y}`).join(" "),
      secondPath: second.map((point, index) => `${index ? "L" : "M"} ${point.x} ${point.y}`).join(" "),
    };
  }, [person]);
  return (
    <div className="min-w-0">
      <svg className="chart-area" role="img" aria-label={`AMH and FSH recorded over time for ${person.name}; showing historical direction only, not a fertility prediction.`} viewBox="0 0 450 232" preserveAspectRatio="none">
        {[35, 85, 135, 185].map((y, index) => <g key={y}><line className="chart-grid-line" x1="49" x2="428" y1={y} y2={y} /><text x="10" y={y + 3}>{index === 0 ? "Higher" : index === 3 ? "Lower" : ""}</text></g>)}
        <text x="3" y="17">REPORTED VALUES · NOT RISK</text>
        <path className="chart-line-primary" d={paths.firstPath} />
        <path className="chart-line-secondary" d={paths.secondPath} />
        {paths.first.map((point, index) => <g key={`a-${index}`}><circle className="chart-point-primary" cx={point.x} cy={point.y} r="4" /><title>{labels[index % labels.length]} · AMH {point.value} ng/mL (reported)</title></g>)}
        {paths.second.map((point, index) => <g key={`f-${index}`}><circle className="chart-point-secondary" cx={point.x} cy={point.y} r="4" /><title>{labels[index % labels.length]} · FSH {point.value} IU/L (reported)</title></g>)}
        {labels.map((label, index) => <text key={label} textAnchor="middle" x={75 + (index * 110)} y="216">{label}</text>)}
      </svg>
      <div className="trend-legend">
        <span className="legend-item"><span className="legend-swatch" /> AMH · ng/mL</span>
        <span className="legend-item"><span className="legend-swatch coral" /> FSH · IU/L</span>
      </div>
    </div>
  );
}

function ConsentDialog({ person, granted, onClose, onSave }: { person: Persona; granted: Set<string>; onClose: () => void; onSave: (next: Set<string>) => void }) {
  const [draft, setDraft] = useState(() => new Set(granted));
  const setOne = (category: string, allowed: boolean) => setDraft((current) => {
    const next = new Set(current);
    if (allowed) next.add(category);
    else next.delete(category);
    return next;
  });
  return (
    <div className="modal-backdrop" role="presentation" onClick={onClose}>
      <section className="modal-panel" role="dialog" aria-modal="true" aria-labelledby="consent-title" onClick={(event) => event.stopPropagation()}>
        <div className="flex items-start justify-between gap-3"><div><p className="eyebrow">DATA PERMISSIONS</p><h2 id="consent-title">You’re in control</h2></div><Button variant="ghost" size="icon" aria-label="Close permissions" onClick={onClose}><X size={16} /></Button></div>
        <p>Grant or revoke each category for {person.name}. Revoking access removes its saved values from this prototype. The demo record shown here is fictional.</p>
        <div className="consent-list">{categories.map((category) => <label className="consent-row" key={category}><span>{category}</span><input type="checkbox" checked={draft.has(category)} onChange={(event) => setOne(category, event.target.checked)} aria-label={`Allow ${category}`} /></label>)}</div>
        <div className="rounded bg-accent-soft p-3 text-xs leading-relaxed"><strong>No employment or insurance use.</strong> Reproductive data must not be used to evaluate hiring, workplace status, coverage, or premiums.</div>
        <div className="mt-4 flex flex-wrap justify-end gap-2"><Button variant="outline" onClick={onClose}>Cancel</Button><Button onClick={() => onSave(draft)}><Check size={15} /> Save permissions</Button></div>
      </section>
    </div>
  );
}

function MonitoringDashboard() {
  const [personId, setPersonId] = useState(personas[0].id);
  const [section, setSection] = useState("Overview");
  const [period, setPeriod] = useState("1Y");
  const [showConsent, setShowConsent] = useState(false);
  const [saved, setSaved] = useState(false);
  const [sharing, setSharing] = useState(false);
  const [permissions, setPermissions] = useState<Record<string, Set<string>>>(() => Object.fromEntries(personas.map((person) => [person.id, new Set(person.recorded)])));
  const person = personas.find((entry) => entry.id === personId) ?? personas[0];
  const savedScopes = permissions[person.id] ?? new Set<string>();
  const recordedCount = person.recorded.length;
  const changeScope = (next: Set<string>) => {
    setPermissions((previous) => ({ ...previous, [person.id]: next }));
    setShowConsent(false);
    setSaved(true);
    window.setTimeout(() => setSaved(false), 2400);
  };
  const handleExport = () => {
    setSharing(true);
    const summary = {
      demo_only: true,
      participant: person.name,
      synthetic: true,
      last_entry: person.lastSeen,
      history_note: person.summary,
      recorded_categories: [...savedScopes],
      interpretation: "No diagnosis, fertility score, or pregnancy prediction.",
    };
    const href = URL.createObjectURL(new Blob([JSON.stringify(summary, null, 2)], { type: "application/json" }));
    const link = document.createElement("a");
    link.href = href;
    link.download = `${person.id}-synthetic-summary.json`;
    link.click();
    URL.revokeObjectURL(href);
    window.setTimeout(() => setSharing(false), 2200);
  };

  return (
    <div className="monitor-shell">
      <aside className="monitor-sidebar" aria-label="Workspace navigation">
        <div className="brand-lockup"><div className="brand-mark"><Activity size={21} strokeWidth={2.2} /></div><div><div className="brand-name">tide</div><div className="brand-caption">REPRODUCTIVE HEALTH</div></div></div>
        <div className="nav-section-label">WORKSPACE</div>
        <nav className="dashboard-nav">{navigation.map((item) => <button key={item.label} type="button" onClick={() => setSection(item.label)} aria-current={section === item.label ? "page" : undefined}><item.icon size={16} />{item.label}{item.label === "People" && <span className="ml-auto rounded-full bg-brand-wash px-2 py-0.5 text-[9px] text-primary">05</span>}</button>)}</nav>
        <div className="sidebar-persona"><div className="nav-section-label !m-0 !mb-2">SELECTED RECORD</div><select className="sidebar-select" value={personId} onChange={(event) => setPersonId(event.target.value)} aria-label="Selected synthetic patient">{personas.map((candidate) => <option value={candidate.id} key={candidate.id}>{candidate.name} · {candidate.age}</option>)}</select><div className="persona-status"><span className="status-dot" /> Fictional demo profile</div></div>
        <div className="sidebar-bottom"><div className="local-status"><div className="local-status-top"><LockKeyhole size={13} className="text-primary" /> Local-only preview</div><p>Synthetic records only. Health data never leaves your device in the Python demo.</p></div><div className="avatar-row"><div className="avatar-circle">DR</div><div className="avatar-copy">Clinician view<span>Research prototype</span></div><MoreHorizontal size={17} className="ml-auto text-muted-foreground" /></div></div>
      </aside>

      <main className="monitor-main">
        <header className="topbar"><div className="breadcrumb"><span>Workspace</span><ChevronRight size={13} /><strong>{section}</strong><ChevronRight size={13} /><span>{person.name}</span></div><div className="topbar-actions"><span className="local-pill"><span className="status-dot" /> Synthetic demo</span><Button variant="outline" size="sm" onClick={() => setShowConsent(true)}><SlidersHorizontal size={14} /> Permissions</Button></div></header>
        <div className="main-content">
          {section === "Overview" ? (
            <>
              <div className="page-heading"><div><p className="eyebrow">LONGITUDINAL MONITORING · SYNTHETIC DATA</p><h1>{person.name}<span className="ml-3 align-middle rounded-full bg-brand-wash px-2.5 py-1 font-sans text-[10px] font-semibold text-primary">DEMO PROFILE</span></h1><p>{person.age} years · {person.summary}</p></div><div className="heading-actions"><Button variant="outline" onClick={() => setShowConsent(true)}><ShieldCheck size={15} /> Consent settings</Button><Button onClick={handleExport}><Plus size={15} />{sharing ? "Preparing" : "Export summary"}</Button></div></div>

              <div className="safety-banner"><ShieldCheck size={16} /><p><strong>Demonstration only.</strong> No real patient information is present. This prototype shows recorded changes, never a fertility score or diagnosis. A clinician should interpret results in context.</p></div>

              <div className="metric-grid">
                <MetricCard icon={<CalendarDays size={15} />} label="AGE AT LAST ENTRY" value={`${person.age}`} unit="years" detail="Age is a context—not a prediction" />
                <MetricCard icon={<ClipboardList size={15} />} label="RECORDED VISITS" value={`${person.visits}`} unit="visits" detail={`Most recent · ${person.lastSeen}`} />
                <MetricCard icon={<FlaskConical size={15} />} label="LAB ENTRIES" value={`${person.labs}`} unit="results" detail="Reported values · lab context varies" />
                <MetricCard icon={<ShieldCheck size={15} />} label="SHARED CATEGORIES" value={`${savedScopes.size}`} unit={`of ${categories.length}`} detail="You choose what is included" />
              </div>

              <div className="content-grid">
                <section className="panel" aria-labelledby="trend-heading"><div className="panel-heading"><div><div className="panel-title" id="trend-heading">Direction of change</div><div className="panel-subtitle">Reported labs over time · descriptive, not predictive</div></div><div className="period-tabs" aria-label="Chart date range">{["6M", "1Y", "ALL"].map((value) => <button type="button" key={value} aria-pressed={period === value} onClick={() => setPeriod(value)}>{value}</button>)}</div></div><div className="panel-content"><TrendChart person={person} period={period} /><p className="chart-footnote">Values are shown as entered. Different lab methods, units and collection timing can affect interpretation. AMH alone cannot predict an individual's reproductive potential.</p></div></section>

                <section className="panel" aria-labelledby="missing-heading"><div className="panel-heading"><div><div className="panel-title" id="missing-heading">What’s on record</div><div className="panel-subtitle">Missing data stays visible</div></div><Button variant="ghost" size="icon" aria-label="Open record permissions" onClick={() => setShowConsent(true)}><MoreHorizontal size={17} /></Button></div><div className="panel-content"><div className="confidence-note"><Info size={14} /><p><strong>Interpretation is limited.</strong> Records are partial, and dates, lab methods and context may be missing.</p></div><div className="completeness-list">{categories.map((category) => { const present = savedScopes.has(category) && person.recorded.includes(category); return <div key={category} className="completeness-row"><span className="completeness-label">{present ? <Check size={12} className="text-success" /> : <span className="h-3 w-3 rounded-full border border-border" />}{category}</span><span className={`completeness-state ${present ? "present" : ""}`}>{present ? "Recorded" : "Not shared"}</span></div>; })}</div></div></section>
              </div>

              <div className="section-heading"><div><h2>Factor categories</h2><p>Distinguish potential choices from factors that cannot be changed</p></div><CircleHelp size={16} className="text-muted-foreground" /></div>
              <div className="factor-grid"><section className="panel factor-panel"><div className="factor-title"><span className="factor-tag">MODIFIABLE</span> Lifestyle factors <Info size={13} className="text-muted-foreground" /></div><div className="factor-chip-list">{["Smoking", "Alcohol", "Sleep", "Activity", "Nutrition"].map((factor) => <span className="factor-chip" key={factor}>{factor}</span>)}</div><p className="factor-footnote">General health topics only. These do not guarantee changes in fertility; choose discussion with a clinician, without blame or pressure.</p></section><section className="panel factor-panel"><div className="factor-title"><span className="factor-tag fixed">NON-MODIFIABLE</span> Other context <Info size={13} className="text-muted-foreground" /></div><div className="factor-chip-list">{["Age", "Past history", "Some conditions"].map((factor) => <span className="factor-chip" key={factor}>{factor}</span>)}</div><p className="factor-footnote">This describes context, not an individual outcome. No countdown, deterministic prediction, or risk category is assigned.</p></section></div>

              <div className="section-heading"><div><h2>Possible topics to discuss</h2><p>Options for a conversation—not automated clinical instructions</p></div><span className="flex items-center gap-1 text-[10px] text-muted-foreground"><Sparkles size={13} className="text-primary" /> Non-diagnostic</span></div>
              <div className="recommendations-grid">{[
                { icon: Zap, text: "Lifestyle optimization" }, { icon: FlaskConical, text: "Testing discussion" }, { icon: MessageCircleHeart, text: "Preconception counselling" }, { icon: Database, text: "Fertility-preservation discussion" }, { icon: ArrowRight, text: "Specialist referral" },
              ].map((option) => <div className="recommendation-option" key={option.text}><option.icon size={17} /><span>{option.text}</span></div>)}</div>
              <div className="recommendation-note"><Info size={13} /> No treatment recommendation is generated. Availability and appropriateness depend on an individual clinical conversation.</div>

              <section className="panel activity-panel" aria-labelledby="reference-heading"><div className="panel-heading"><div><div className="panel-title" id="reference-heading">Evidence & reference sources</div><div className="panel-subtitle">Official guidance · named references · verify for updates</div></div><Button variant="ghost" size="sm" onClick={() => setSection("Guidelines")}>See all <ArrowRight size={13} /></Button></div><div className="panel-content"><table className="activity-table"><thead><tr><th>ORGANIZATION</th><th>REFERENCE</th><th>DATE</th><th>STATUS</th></tr></thead><tbody>{guidance.slice(0, 3).map((item) => <tr key={item.org}><td className="font-semibold">{item.org}</td><td><a className="text-foreground underline decoration-border underline-offset-2 hover:text-primary" href={item.url} target="_blank" rel="noreferrer">{item.title}</a></td><td className="text-muted-foreground">{item.year}</td><td><span className="table-status"><Check size={11} /> Cited</span></td></tr>)}</tbody></table><div className="citations"><a className="citation-link" href={guidance[3].url} target="_blank" rel="noreferrer">ESHRE · preservation <ArrowRight size={10} /></a><a className="citation-link" href="https://www.asrm.org/practice-guidance/practice-committee-documents/fertility-evaluation-of-infertile-women-a-committee-opinion-2026/" target="_blank" rel="noreferrer">ASRM · evaluation <ArrowRight size={10} /></a></div></div></section>

              <div className="bottom-note"><ShieldCheck size={15} /> <span><strong className="text-foreground">Responsible use:</strong> demo content is fictional. This tool cannot diagnose, predict individual fertility, estimate pregnancy odds, or recommend treatments. Never use reproductive data for hiring, insurance, premiums, or workplace decisions.</span></div>
            </>
          ) : <DashboardSection name={section} person={person} onOpenConsent={() => setShowConsent(true)} />}
        </div>
      </main>
      {showConsent && <ConsentDialog person={person} granted={savedScopes} onClose={() => setShowConsent(false)} onSave={changeScope} />}
      {saved && <div className="success-toast" role="status"><Check size={15} className="text-success" /> Preferences updated for this preview</div>}
    </div>
  );
}

function MetricCard({ icon, label, value, unit, detail }: { icon: React.ReactNode; label: string; value: string; unit: string; detail: string }) {
  return <div className="metric-card"><div className="metric-top"><span>{label}</span><span className="metric-icon">{icon}</span></div><div className="metric-value">{value}<span className="font-sans text-xs font-medium text-muted-foreground">{unit}</span></div><div className="metric-note">{detail}</div></div>;
}

function DashboardSection({ name, person, onOpenConsent }: { name: string; person: Persona; onOpenConsent: () => void }) {
  if (name === "People") return <><div className="page-heading"><div><p className="eyebrow">PATIENT-CENTERED DATA CONTROL</p><h1>People & permissions</h1><p>Fictional demo records with clear, revocable category settings.</p></div><Button onClick={onOpenConsent}><SlidersHorizontal size={15} /> Manage consent</Button></div><div className="grid gap-3">{personas.map((candidate) => <button key={candidate.id} type="button" className="panel flex items-center gap-4 p-4 text-left transition-colors hover:border-ring" onClick={() => window.dispatchEvent(new CustomEvent("demo-person-select", { detail: candidate.id }))}><div className="avatar-circle h-10 w-10 text-xs">{candidate.initials}</div><div className="min-w-0 flex-1"><div className="font-semibold">{candidate.name}<span className="ml-2 text-[10px] text-primary">Synthetic demo</span></div><div className="mt-1 truncate text-xs text-muted-foreground">{candidate.summary}</div></div><ChevronRight size={16} className="text-muted-foreground" /></button>)}</div></>;
  if (name === "Cohort insights") return <><div className="page-heading"><div><p className="eyebrow">AGGREGATES · SYNTHETIC ONLY</p><h1>Cohort insights</h1><p>Descriptive completeness across five fictional examples. This is not a clinical population study.</p></div><span className="local-pill"><LockKeyhole size={13} /> Small groups suppressed</span></div><div className="metric-grid"><MetricCard icon={<Users size={15} />} label="DEMO RECORDS" value="05" unit="examples" detail="Synthetic people only" /><MetricCard icon={<Database size={15} />} label="MINIMUM COHORT" value="05" unit="records" detail="Smaller groups are hidden" /><MetricCard icon={<ShieldCheck size={15} />} label="REAL PATIENTS" value="00" unit="records" detail="Excluded from this preview" /><MetricCard icon={<Activity size={15} />} label="OUTCOMES" value="00" unit="predictions" detail="No outcome inference" /></div><div className="section-heading"><div><h2>Recorded categories</h2><p>Count of synthetic profiles with this kind of example input</p></div></div><section className="panel"><div className="panel-content">{categories.slice(0, 5).map((category) => { const count = personas.filter((item) => item.recorded.includes(category)).length; return <div className="completeness-row" key={category}><span className="completeness-label">{category}</span><span className="completeness-state">{count} of 5 examples</span></div>; })}<p className="mt-4 text-xs leading-relaxed text-muted-foreground">Counts describe the content of fabricated demo profiles, not prevalence or population-level fertility. No categories below five people are displayed.</p></div></section></>;
  if (name === "Guidelines") return <><div className="page-heading"><div><p className="eyebrow">EVIDENCE LIBRARY · CITED SOURCES</p><h1>Guidelines</h1><p>Public professional references that bound the demo’s educational content.</p></div></div><div className="grid gap-3">{guidance.map((item) => <section className="panel p-5" key={item.org}><div className="flex flex-wrap items-start justify-between gap-4"><div><div className="eyebrow">{item.org} · {item.year}</div><h2 className="m-0 text-base font-bold">{item.title}</h2><p className="mt-2 max-w-3xl text-xs leading-relaxed text-muted-foreground">{item.org === "ASRM" ? "ASRM notes ovarian-reserve markers can inform some clinical decisions but do not independently predict reproductive potential; personal interpretation belongs in a clinician-guided assessment." : item.org === "NICE" ? "NICE NG257 addresses assessment, treatment and fertility preservation for medical indications. The recommendations require professional judgement and individual context." : item.org === "ESHRE" ? "ESHRE guidance addresses information, support, assessment and preservation options. These are discussion topics—not a guarantee or automated recommendation." : "WHO guidance addresses evidence-based infertility prevention, assessment and treatment with person-centred and equitable care. It does not validate a consumer fertility score."}</p><p className="mt-2 text-[10px] text-muted-foreground">Verify the current guidance edition. These summaries are educational and are not patient-specific advice.</p></div><Button variant="outline" size="sm" asChild><a href={item.url} target="_blank" rel="noreferrer">Open official source <ArrowRight size={13} /></a></Button></div></section>)}</div></>;
  if (name === "Audit trail") return <><div className="page-heading"><div><p className="eyebrow">TRANSPARENCY & ACCOUNTABILITY</p><h1>Audit trail</h1><p>This UI preview has no persistent patient records. The local Python demo logs saves, permission changes and blocked purposes.</p></div></div><section className="panel"><div className="panel-content"><div className="confidence-note"><LockKeyhole size={15} /><p><strong>Preview mode.</strong> No real data is stored by this hosted demonstration. The runnable local application keeps a local audit ledger; data-entry content is not written into audit event text.</p></div><div className="completeness-list">{[{ a: "Consent categories", b: "Changes recorded locally" }, { a: "Data purpose", b: "Employment / insurance blocked" }, { a: "Sensitive values", b: "Encrypted in local database" }, { a: "Population metrics", b: "Synthetic only · minimum group 5" }].map((row) => <div className="completeness-row" key={row.a}><span>{row.a}</span><span className="completeness-state">{row.b}</span></div>)}</div></div></section></>;
  return <section className="placeholder-section"><p className="eyebrow">RESEARCH PROTOTYPE</p><h2>{name}</h2><p>{person.name} is a synthetic demonstration profile. Explore category permissions, cited resources and neutral historical trends—no diagnosis, deterministic prediction or fertility score is produced.</p></section>;
}