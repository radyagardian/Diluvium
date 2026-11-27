import { useState } from 'react';
import { Link } from 'react-router-dom';
import DottedGlowBackground from '../components/DottedGlowBackground';
import { Menu, X, Copy, Check } from 'lucide-react';

// Replace with your Discord OAuth2 Bot Invite URL from Discord Developer Portal
const DISCORD_INVITE_URL ='https://discord.com/oauth2/authorize?client_id=1575412277367275611&permissions=2147502080&integration_type=0&scope=bot+applications.commands';

const NAV_LINKS = [
  { id: 'architecture', label: 'How It Works', href: '#architecture' },
  { id: 'setup', label: 'Bot Setup', href: '#setup' },
  { id: 'siaga', label: 'Siaga Levels', href: '#siaga' },
];

const SLASH_COMMANDS = [
  {
    command: '/cekbanjir',
    arg: 'area_id:31.74.01.1004',
    summary:
      'Detailed flood risk prediction and BMKG rainfall forecast for a specific Kelurahan using its adm4 code (defaults to Tebet if omitted).',
  },
  {
    command: '/pintuair',
    arg: '',
    summary:
      'Live Tinggi Muka Air (TMA) water levels and status for Katulampa, Depok, and Manggarai floodgates.',
  },
  {
    command: '/statusjakarta',
    arg: '',
    summary:
      'City-wide summary of current flood potential and Siaga status across monitored DKI Jakarta areas.',
  },
];

const COMMON_AREA_CODES = [
  {
    code: '31.74.01.1004',
    area: 'Tebet',
    region: 'South Jakarta',
    isDefault: true,
  },
  {
    code: '31.75.03.1002',
    area: 'Kampung Melayu, Jatinegara',
    region: 'East Jakarta',
  },
  {
    code: '31.75.03.1003',
    area: 'Bidara Cina, Jatinegara',
    region: 'East Jakarta',
  },
  {
    code: '31.75.04.1004',
    area: 'Cawang, Kramat Jati',
    region: 'East Jakarta',
  },
  {
    code: '31.75.06.1006',
    area: 'Cipinang Melayu, Makasar',
    region: 'East Jakarta',
  },
  {
    code: '31.74.07.1002',
    area: 'Petogogan, Kebayoran Baru',
    region: 'South Jakarta',
  },
  {
    code: '31.71.03.1001',
    area: 'Kemayoran',
    region: 'Central Jakarta',
  },
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
  const [copiedCode, setCopiedCode] = useState(null);

  const handleCopyCode = async (code) => {
    try {
      await navigator.clipboard.writeText(code);
      setCopiedCode(code);
      setTimeout(() => setCopiedCode(null), 1800);
    } catch {
      // Fallback ignored if clipboard permissions are restricted
    }
  };

  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-100 antialiased selection:bg-sky-500/25">
      {/* Minimalist Underline Navbar */}
      <header className="sticky top-0 z-50 border-b border-white/10 bg-[#09090b]/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          <a href="#" className="flex items-center gap-2.5 text-white">
            <img
              src="/diluvium-logo.jpeg"
              alt="Diluvium"
              className="h-8 w-8 rounded-lg object-cover"
            />
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
                    className={`absolute bottom-0 left-0 right-0 h-[2px] origin-left bg-white transition-transform duration-300 ${
                      isActive ? 'scale-x-100' : 'scale-x-0 group-hover:scale-x-100'
                    }`}
                  />
                </a>
              );
            })}
          </nav>

          {/* Right Action */}
          <div className="hidden items-center md:flex">
            <Link
              to="/admin"
              className="group relative py-1 text-sm font-medium text-zinc-300 transition-colors hover:text-white"
            >
              Admin Login
              <span className="absolute bottom-0 left-0 right-0 h-[1px] origin-left scale-x-0 bg-zinc-300 transition-transform duration-300 group-hover:scale-x-100" />
            </Link>
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
            <h1 className="text-4xl font-semibold leading-[1.08] tracking-tight text-white sm:text-5xl lg:text-6xl">
              Hyper-local flood warnings for Jakarta,{' '}
              <span className="text-sky-400">hours before impact.</span>
            </h1>

            <p className="mt-6 max-w-xl text-base leading-relaxed text-zinc-400 sm:text-lg">
              Diluvium monitors upstream river gates (Katulampa, Depok, Manggarai) and
              Kelurahan-level BMKG rainfall, computes projected arrival time and depth, and
              delivers verified <span className="text-zinc-200">Siaga 1–4</span> alerts
              directly to Discord.
            </p>
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

      {/* Setup Guide: Discord Bot & Slash Commands */}
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
                { id: 'commands', label: 'Slash Commands' },
              ].map((tab) => {
                const active = setupTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setSetupTab(tab.id)}
                    className={`relative cursor-pointer pb-2 text-sm font-medium transition-colors ${
                      active ? 'text-white' : 'text-zinc-500 hover:text-zinc-200'
                    }`}
                  >
                    {tab.label}
                    <span
                      className={`absolute bottom-0 left-0 right-0 h-[2px] origin-left bg-sky-400 transition-transform duration-300 ${
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
                    body: 'Add Diluvium EWS to your Discord server and grant Send Messages and Embed Links permissions.',
                  },
                  {
                    step: '02',
                    title: 'Pick an Alert Channel',
                    body: 'Create a dedicated #flood-alerts channel or connect a server Webhook under Integrations.',
                  },
                  {
                    step: '03',
                    title: 'Query Live Telemetry with Slash Commands',
                    body: 'Run /cekbanjir, /pintuair, or /statusjakarta directly in any channel for real-time Jakarta flood telemetry.',
                  },
                ].map((item) => (
                  <div key={item.step} className="flex gap-5">
                    <span className="pt-1 font-mono text-xs text-zinc-500">{item.step}</span>
                    <div>
                      <h3 className="text-base font-medium text-white">{item.title}</h3>
                      <p className="mt-1.5 text-sm leading-relaxed text-zinc-400">{item.body}</p>
                    </div>
                  </div>
                ))}

                {/* Fancy Invite Diluvium CTA (moved from Hero) */}
                <div className="pt-2">
                  <a
                    href={DISCORD_INVITE_URL}
                    target="_blank"
                    rel="noreferrer"
                    className="invite-btn"
                  >
                    <span className="circle" />
                    <span className="text">Invite Diluvium</span>
                  </a>
                </div>
              </div>

              <div className="lg:col-span-5">
                <div className="rounded-2xl border border-white/10 bg-[#0c0c0f] p-6">
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-medium uppercase tracking-widest text-zinc-500">
                      Slash Commands
                    </p>
                    <button
                      onClick={() => setSetupTab('commands')}
                      className="cursor-pointer text-xs text-sky-400 transition hover:text-sky-300"
                    >
                      View Area Codes →
                    </button>
                  </div>
                  <div className="mt-5 divide-y divide-white/10 font-mono text-xs">
                    {SLASH_COMMANDS.map((cmd, index) => (
                      <div
                        key={cmd.command}
                        className={
                          index === 0
                            ? 'pb-4'
                            : index === SLASH_COMMANDS.length - 1
                            ? 'pt-4'
                            : 'py-4'
                        }
                      >
                        <span className="text-sky-400">{cmd.command}</span>
                        {cmd.arg && <span className="ml-2 text-zinc-500">{cmd.arg}</span>}
                        <p className="mt-1 font-sans text-zinc-400">{cmd.summary}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="mt-12 grid gap-12 lg:grid-cols-12">
              {/* Left: Detailed Slash Command Usage */}
              <div className="space-y-8 lg:col-span-6">
                {SLASH_COMMANDS.map((cmd, index) => (
                  <div key={cmd.command} className="flex gap-5">
                    <span className="pt-1 font-mono text-xs text-zinc-500">
                      0{index + 1}
                    </span>
                    <div className="flex-1">
                      <div className="flex flex-wrap items-center gap-2 font-mono text-sm">
                        <span className="font-semibold text-sky-400">{cmd.command}</span>
                        {cmd.arg && (
                          <span className="rounded-md border border-white/10 bg-white/5 px-2 py-0.5 text-xs text-zinc-300">
                            {cmd.arg}
                          </span>
                        )}
                      </div>
                      <p className="mt-2 text-sm leading-relaxed text-zinc-400">
                        {cmd.summary}
                      </p>
                    </div>
                  </div>
                ))}

                <div className="rounded-xl border border-white/10 bg-[#0c0c0f] p-4 text-xs leading-relaxed text-zinc-400">
                  <span className="font-medium text-zinc-200">Tip:</span> Running{' '}
                  <code className="rounded bg-white/5 px-1.5 py-0.5 font-mono text-sky-400">
                    /cekbanjir
                  </code>{' '}
                  without an <code className="font-mono text-zinc-200">area_id</code>{' '}
                  automatically checks <span className="text-zinc-200">Tebet (31.74.01.1004)</span>.
                  Click any code on the right to copy it.
                </div>
              </div>

              {/* Right: Common Jakarta BMKG adm4 Area Codes */}
              <div className="lg:col-span-6">
                <div className="rounded-2xl border border-white/10 bg-[#0c0c0f] p-6">
                  <div className="flex items-center justify-between border-b border-white/10 pb-4">
                    <div>
                      <p className="text-xs font-medium uppercase tracking-widest text-zinc-500">
                        Common BMKG adm4 Area Codes
                      </p>
                      <p className="mt-1 text-xs text-zinc-400">
                        Use with <code className="font-mono text-sky-400">/cekbanjir area_id</code>
                      </p>
                    </div>
                    <span className="font-mono text-[11px] text-zinc-500">DKI Jakarta</span>
                  </div>

                  <div className="mt-2 divide-y divide-white/10">
                    {COMMON_AREA_CODES.map((item) => {
                      const isCopied = copiedCode === item.code;
                      return (
                        <div
                          key={item.code}
                          className="flex items-center justify-between gap-4 py-3"
                        >
                          <div className="min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="truncate text-sm font-medium text-zinc-200">
                                {item.area}
                              </span>
                              {item.isDefault && (
                                <span className="rounded-full border border-sky-400/30 bg-sky-400/10 px-2 py-0.5 text-[10px] font-medium text-sky-400">
                                  Default
                                </span>
                              )}
                            </div>
                            <p className="text-xs text-zinc-500">{item.region}</p>
                          </div>

                          <button
                            onClick={() => handleCopyCode(item.code)}
                            title="Copy adm4 code"
                            className="inline-flex shrink-0 cursor-pointer items-center gap-2 rounded-lg border border-white/10 bg-white/[0.03] px-2.5 py-1.5 font-mono text-xs text-zinc-300 transition hover:border-sky-400/40 hover:text-white"
                          >
                            <span>{item.code}</span>
                            {isCopied ? (
                              <Check className="h-3.5 w-3.5 text-emerald-400" />
                            ) : (
                              <Copy className="h-3.5 w-3.5 text-zinc-500" />
                            )}
                          </button>
                        </div>
                      );
                    })}
                  </div>
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
            <Link to="/admin" className="transition hover:text-zinc-200">
              Admin Login
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}