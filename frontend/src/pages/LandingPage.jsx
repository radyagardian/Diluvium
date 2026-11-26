import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Waves, Menu, X, ExternalLink } from 'lucide-react';
import DottedGlowBackground from '../components/DottedGlowBackground';

const NAV_LINKS = [
  { id: 'architecture', label: 'How It Works', href: '#architecture' },
  { id: 'setup', label: 'Bot Setup', href: '#setup' },
  { id: 'siaga', label: 'Siaga Levels', href: '#siaga' },
];

const SIAGA_LEVELS = [
  {
    level: 'Siaga 4',
    status: 'Normal',
    dot: 'bg-emerald-400',
    manggarai: '< 650 cm',
    katulampa: '< 80 cm',
    desc: 'Safe water discharge. Routine BMKG and BPBD telemetry polling active.',
  },
  {
    level: 'Siaga 3',
    status: 'Waspada',
    dot: 'bg-amber-400',
    manggarai: '650 – 749 cm',
    katulampa: '80 – 149 cm',
    desc: 'Elevated upstream flow. Early heads-up sent to subscribed river-basin Kelurahan.',
  },
  {
    level: 'Siaga 2',
    status: 'Siaga',
    dot: 'bg-orange-400',
    manggarai: '750 – 849 cm',
    katulampa: '150 – 199 cm',
    desc: 'High flood probability. Arrival ETA and depth projections broadcast across channels.',
  },
  {
    level: 'Siaga 1',
    status: 'Awas',
    dot: 'bg-red-500',
    manggarai: '≥ 850 cm',
    katulampa: '≥ 200 cm',
    desc: 'Critical flood hazard. Immediate evacuation advisories with non-AI fallback redundancy.',
  },
];

export default function LandingPage() {
  const [activeNav, setActiveNav] = useState('architecture');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [setupTab, setSetupTab] = useState('discord');

  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-100 antialiased selection:bg-sky-500/25">
      {/* Minimalist Underline Navbar */}
      <header className="sticky top-0 z-50 border-b border-white/10 bg-[#09090b]/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          {/* Brand — no "DKI JAKARTA EWS" box */}
          <a href="#" className="flex items-center gap-2.5 text-white">
            <Waves className="h-5 w-5 text-sky-400" />
            <span className="text-base font-semibold tracking-tight">Diluvium</span>
          </a>

          {/* Center Nav Links with Underline Indicator */}
          <nav className="hidden h-full items-center gap-8 md:flex">
            {NAV_LINKS.map((item) => {
              const isActive = activeNav === item.id;
              return (
                <a
                  key={item.id}
                  href={item.href}
                  onClick={() => setActiveNav(item.id)}
                  className={`group relative flex h-full items-center text-sm font-medium transition-colors ${
                    isActive ? 'text-white' : 'text-zinc-400 hover:text-zinc-100'
                  }`}
                >
                  {item.label}
                  <span
                    className={`absolute bottom-0 left-0 right-0 h-[2px] bg-white transition-transform duration-300 origin-left ${
                      isActive ? 'scale-x-100' : 'scale-x-0 group-hover:scale-x-100'
                    }`}
                  />
                </a>
              );
            })}
          </nav>

          {/* Right Action */}
          <div className="hidden w-20 items-center md:block">
          </div>

          {/* Mobile Menu Toggle */}
          <button
            onClick={() => setMobileMenuOpen((prev) => !prev)}
            className="text-zinc-400 hover:text-white md:hidden"
            aria-label="Toggle Menu"
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>

        {/* Mobile Drawer */}
        {mobileMenuOpen && (
          <div className="border-t border-white/10 bg-[#09090b] px-6 py-4 md:hidden">
            <div className="flex flex-col gap-4">
              {NAV_LINKS.map((item) => (
                <a
                  key={item.id}
                  href={item.href}
                  onClick={() => {
                    setActiveNav(item.id);
                    setMobileMenuOpen(false);
                  }}
                  className="text-sm font-medium text-zinc-300 hover:text-white"
                >
                  {item.label}
                </a>
              ))}
              <Link
                to="/admin"
                onClick={() => setMobileMenuOpen(false)}
                className="border-t border-white/10 pt-4 text-sm font-medium text-white"
              >
                Admin Login
              </Link>
            </div>
          </div>
        )}
      </header>

      {/* Hero Section with Dotted Glow Background */}
      <section className="relative overflow-hidden border-b border-white/10">
        <DottedGlowBackground
          className="[mask-image:radial-gradient(ellipse_at_center,black_45%,transparent_88%)]"
          gap={18}
          radius={1.3}
          color="rgba(255, 255, 255, 0.22)"
          glowColor="rgba(56, 189, 248, 0.9)"
          opacity={0.75}
        />

        <div className="relative z-10 mx-auto grid max-w-6xl items-center gap-16 px-6 py-24 lg:grid-cols-12 lg:py-32">
          <div className="lg:col-span-7">
            <h1 className="text-4xl font-semibold tracking-tight text-white sm:text-5xl lg:text-6xl leading-[1.08]">
              Hyper-local flood warnings for Jakarta,{' '}
              <span className="text-sky-400">hours before impact.</span>
            </h1>

            <p className="mt-6 max-w-xl text-base leading-relaxed text-zinc-400 sm:text-lg">
              Diluvium monitors upstream river gates (Katulampa, Depok, Manggarai) and
              Kelurahan-level BMKG rainfall, computes projected arrival time and depth, and
              delivers verified <span className="text-zinc-200">Siaga 1–4</span> alerts to
              Discord and Telegram.
            </p>

            {/* Single CTA Button — Uiverse loud-chicken-53 without arrow */}
            <div className="mt-10">
              <a href="#setup" className="invite-btn">
                <span className="circle" />
                <span className="text">Invite Diluvium</span>
              </a>
            </div>
          </div>

          {/* Minimal Live Alert Preview */}
          <div className="lg:col-span-5">
            <div className="rounded-2xl border border-white/10 bg-[#0c0c0f]/90 p-6 backdrop-blur-sm">
              <div className="mb-5 flex items-center justify-between border-b border-white/10 pb-3.5 text-xs">
                <span className="font-medium uppercase tracking-widest text-zinc-500">
                  Verified Dispatch
                </span>
                <span className="flex items-center gap-1.5 font-mono font-semibold text-orange-400">
                  <span className="h-1.5 w-1.5 rounded-full bg-orange-400" />
                  SIAGA 2
                </span>
              </div>

              <div className="space-y-2.5 font-mono text-xs text-zinc-300">
                <div className="flex justify-between">
                  <span className="text-zinc-500">Area</span>
                  <span>Kampung Melayu, Jatinegara</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Manggarai Gate</span>
                  <span>765 cm (+18 cm/hr)</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Rainfall</span>
                  <span>48.2 mm / 3h</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Arrival ETA</span>
                  <span className="text-white">2h 15m</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Projected Depth</span>
                  <span>75 cm • 1.4 km radius</span>
                </div>
              </div>

              <div className="mt-6 grid grid-cols-3 divide-x divide-white/10 border-t border-white/10 pt-4 text-center">
                <div>
                  <div className="text-[11px] text-zinc-500">Katulampa</div>
                  <div className="mt-0.5 font-mono text-sm text-zinc-200">80 cm</div>
                </div>
                <div>
                  <div className="text-[11px] text-zinc-500">Depok</div>
                  <div className="mt-0.5 font-mono text-sm text-zinc-200">180 cm</div>
                </div>
                <div>
                  <div className="text-[11px] text-zinc-500">Manggarai</div>
                  <div className="mt-0.5 font-mono text-sm text-sky-400">760 cm</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="architecture" className="mx-auto max-w-6xl px-6 py-24">
        <div className="max-w-xl">
          <p className="text-xs font-medium uppercase tracking-widest text-zinc-500">
            Pipeline
          </p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-white">
            Deterministic hydrology. AI orchestration.
          </h2>
        </div>

        <div className="mt-14 grid gap-10 md:grid-cols-3">
          {[
            {
              num: '01',
              title: 'Real-Time Ingestion',
              body: 'Polls official BMKG adm4 rainfall forecasts and BPBD DKI Jakarta river gate telemetry with resilient local caching.',
            },
            {
              num: '02',
              title: 'Hydrological Engine',
              body: 'Combines upstream lag times, local rainfall intensity, and Jakarta flood baselines to estimate runoff ETA and depth.',
            },
            {
              num: '03',
              title: 'Verification & Fallback',
              body: 'Audits every alert against official Siaga 1–4 thresholds before dispatch, backed by a deterministic non-AI fallback.',
            },
          ].map((step) => (
            <div key={step.num} className="border-t border-white/10 pt-6">
              <span className="font-mono text-xs text-zinc-500">{step.num}</span>
              <h3 className="mt-3 text-lg font-medium text-white">{step.title}</h3>
              <p className="mt-2.5 text-sm leading-relaxed text-zinc-400">{step.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Setup Guide: Discord & Telegram */}
      <section id="setup" className="border-y border-white/10 py-24">
        <div className="mx-auto max-w-6xl px-6">
          <div className="flex flex-col justify-between gap-6 border-b border-white/10 pb-6 md:flex-row md:items-end">
            <div>
              <p className="text-xs font-medium uppercase tracking-widest text-zinc-500">
                Setup
              </p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight text-white">
                Connect in under 2 minutes.
              </h2>
            </div>

            {/* Minimal Underline Tabs */}
            <div className="flex gap-8">
              {[
                { id: 'discord', label: 'Discord Bot' },
                { id: 'telegram', label: 'Telegram Channel' },
              ].map((tab) => {
                const active = setupTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setSetupTab(tab.id)}
                    className={`relative pb-2 text-sm font-medium transition-colors cursor-pointer ${
                      active ? 'text-white' : 'text-zinc-500 hover:text-zinc-200'
                    }`}
                  >
                    {tab.label}
                    <span
                      className={`absolute bottom-0 left-0 right-0 h-[2px] bg-sky-400 transition-transform duration-300 origin-left ${
                        active ? 'scale-x-100' : 'scale-x-0'
                      }`}
                    />
                  </button>
                );
              })}
            </div>
          </div>

          {setupTab === 'discord' ? (
            <div className="mt-12 grid gap-12 lg:grid-cols-12">
              <div className="space-y-8 lg:col-span-7">
                {[
                  {
                    step: '01',
                    title: 'Invite the Diluvium Bot',
                    body: 'Add the bot to your Discord server and grant Send Messages and Embed Links permissions.',
                  },
                  {
                    step: '02',
                    title: 'Pick an Alert Channel',
                    body: 'Create a dedicated #flood-alerts channel or connect a server Webhook under Integrations.',
                  },
                  {
                    step: '03',
                    title: 'Subscribe or Query Live Telemetry',
                    body: 'Use deterministic slash commands to check flood status directly in Python without consuming AI quota.',
                  },
                ].map((item) => (
                  <div key={item.step} className="flex gap-5">
                    <span className="font-mono text-xs text-zinc-500 pt-1">{item.step}</span>
                    <div>
                      <h3 className="text-base font-medium text-white">{item.title}</h3>
                      <p className="mt-1.5 text-sm leading-relaxed text-zinc-400">{item.body}</p>
                    </div>
                  </div>
                ))}

                <div className="pt-2">
                  <a
                    href="#replace-with-discord-invite"
                    className="inline-flex items-center gap-2 rounded-full border border-white/15 px-5 py-2.5 text-sm font-medium text-white transition hover:border-white/40 hover:bg-white/5"
                  >
                    Add to Discord
                    <ExternalLink className="h-3.5 w-3.5 text-zinc-400" />
                  </a>
                </div>
              </div>

              <div className="lg:col-span-5">
                <div className="rounded-2xl border border-white/10 bg-[#0c0c0f] p-6">
                  <p className="text-xs font-medium uppercase tracking-widest text-zinc-500">
                    Slash Commands
                  </p>
                  <div className="mt-5 divide-y divide-white/10 font-mono text-xs">
                    <div className="pb-4">
                      <span className="text-sky-400">/siaga</span>
                      <p className="mt-1 font-sans text-zinc-400">
                        Live Katulampa, Depok, and Manggarai AWLR heights and current Siaga tier.
                      </p>
                    </div>
                    <div className="py-4">
                      <span className="text-sky-400">/cekbanjir</span>{' '}
                      <span className="text-zinc-500">kelurahan:Kampung Melayu</span>
                      <p className="mt-1 font-sans text-zinc-400">
                        BMKG rainfall forecast and predicted flood depth for a specific Kelurahan.
                      </p>
                    </div>
                    <div className="pt-4">
                      <span className="text-sky-400">/subscribe</span>{' '}
                      <span className="text-zinc-500">channel:#flood-alerts</span>
                      <p className="mt-1 font-sans text-zinc-400">
                        Registers the channel for automated Siaga 1–3 threshold broadcasts.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="mt-12 grid gap-12 lg:grid-cols-12">
              <div className="space-y-8 lg:col-span-7">
                {[
                  {
                    step: '01',
                    title: 'Join the Diluvium Telegram Channel',
                    body: 'Subscribe to the broadcast channel for instant push alerts when Jakarta gates cross Siaga 3 or higher.',
                  },
                  {
                    step: '02',
                    title: 'Keep Notifications Enabled',
                    body: 'Unmute the channel so overnight upstream surges from Katulampa reach you immediately.',
                  },
                  {
                    step: '03',
                    title: 'Optional: Query @DiluviumEWSBot',
                    body: 'Send /start to check real-time BMKG rainfall for your Kelurahan on demand.',
                  },
                ].map((item) => (
                  <div key={item.step} className="flex gap-5">
                    <span className="font-mono text-xs text-zinc-500 pt-1">{item.step}</span>
                    <div>
                      <h3 className="text-base font-medium text-white">{item.title}</h3>
                      <p className="mt-1.5 text-sm leading-relaxed text-zinc-400">{item.body}</p>
                    </div>
                  </div>
                ))}

                <div className="pt-2">
                  <a
                    href="#replace-with-telegram-link"
                    className="inline-flex items-center gap-2 rounded-full border border-white/15 px-5 py-2.5 text-sm font-medium text-white transition hover:border-white/40 hover:bg-white/5"
                  >
                    Join Telegram Channel
                    <ExternalLink className="h-3.5 w-3.5 text-zinc-400" />
                  </a>
                </div>
              </div>

              <div className="lg:col-span-5">
                <div className="rounded-2xl border border-white/10 bg-[#0c0c0f] p-6">
                  <p className="text-xs font-medium uppercase tracking-widest text-zinc-500">
                    Channel Highlights
                  </p>
                  <ul className="mt-5 space-y-4 text-sm text-zinc-400">
                    <li className="border-b border-white/10 pb-4">
                      Low-bandwidth delivery during heavy storm network congestion.
                    </li>
                    <li className="border-b border-white/10 pb-4">
                      One-tap subscription with zero bot configuration needed.
                    </li>
                    <li>
                      Verified against BPBD thresholds prior to broadcast.
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Siaga Threshold Reference */}
      <section id="siaga" className="mx-auto max-w-6xl px-6 py-24">
        <div className="max-w-xl">
          <p className="text-xs font-medium uppercase tracking-widest text-zinc-500">
            Thresholds
          </p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-white">
            Jakarta Siaga 1–4 Reference
          </h2>
        </div>

        <div className="mt-12 grid gap-px overflow-hidden rounded-2xl border border-white/10 bg-white/10 sm:grid-cols-2 lg:grid-cols-4">
          {SIAGA_LEVELS.map((tier) => (
            <div key={tier.level} className="bg-[#09090b] p-6">
              <div className="flex items-center justify-between">
                <span className="text-base font-medium text-white">{tier.level}</span>
                <span className="flex items-center gap-1.5 text-xs text-zinc-400">
                  <span className={`h-2 w-2 rounded-full ${tier.dot}`} />
                  {tier.status}
                </span>
              </div>

              <div className="mt-5 space-y-1.5 border-y border-white/10 py-3 font-mono text-xs text-zinc-300">
                <div className="flex justify-between">
                  <span className="text-zinc-500">Manggarai</span>
                  <span>{tier.manggarai}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Katulampa</span>
                  <span>{tier.katulampa}</span>
                </div>
              </div>

              <p className="mt-4 text-xs leading-relaxed text-zinc-400">{tier.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Minimal Footer */}
      <footer className="border-t border-white/10 py-10">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 text-xs text-zinc-500 sm:flex-row">
          <span>Diluvium — Flood Early Warning System</span>
          <div className="flex items-center gap-6">
            <a
              href="https://github.com/radyagardian/Diluvium"
              target="_blank"
              rel="noreferrer"
              className="transition hover:text-zinc-200"
            >
              GitHub
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}