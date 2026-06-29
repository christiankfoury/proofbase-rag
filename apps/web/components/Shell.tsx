"use client";

import Link from "next/link";
import { BookOpen, Gauge, MessageSquare, ShieldCheck } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import { createContext, useContext, useEffect, useMemo, useRef, useState, useTransition } from "react";
import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import {
  DEMO_USER_CHANGED_EVENT,
  fetchCurrentDemoUser,
  fetchDemoUsers,
  selectedDemoUserId,
  setSelectedDemoUserId,
  syncDemoUserCookie,
} from "@/lib/demoAuth";
import type { DemoUser } from "@/lib/demoAuth";

type NavGroup = {
  title: string;
  icon: LucideIcon;
  links: Array<[string, string]>;
};

const navGroups: NavGroup[] = [
  {
    title: "App",
    icon: MessageSquare,
    links: [
      ["Home", "/"],
      ["Guided Demo", "/demo"],
      ["Project Workspaces", "/projects"],
      ["Chat Demo", "/chat"],
      ["Algorithm Guide", "/algorithm"],
    ],
  },
  {
    title: "Dev & Admin",
    icon: Gauge,
    links: [
      ["Measured Enterprise RAG Progress", "/dev-admin"],
      ["Run Comparison", "/dev-admin/runs"],
      ["Failed Questions", "/dev-admin/failed-questions"],
      ["Algorithm Quality Lab", "/dev-admin/retrieval-playground"],
      ["Permission Demo", "/dev-admin/permission-demo"],
      ["Multi-Document Reasoning", "/dev-admin/multi-doc"],
      ["Observability", "/dev-admin/observability"],
      ["Feedback Overview", "/dev-admin/feedback"],
      ["Audit Log", "/dev-admin/audit"],
    ],
  },
  {
    title: "Deep Evaluation",
    icon: BookOpen,
    links: [
      ["Retrieval Experiments", "/dev-admin/retrieval-experiments"],
      ["Prompt History", "/dev-admin/prompt-experiments"],
    ],
  },
  {
    title: "Security",
    icon: ShieldCheck,
    links: [
      ["Permission Safety", "/dev-admin/permission-safety"],
      ["Memory Evaluation", "/dev-admin/memory-evaluation"],
    ],
  },
];

const navStyles = {
  panel:
    "fixed inset-y-0 left-0 z-30 w-80 max-w-[calc(100vw-2rem)] overflow-y-auto border-r border-stone-300 bg-white shadow-xl transition-transform duration-200 ease-out md:w-96 xl:w-[28rem]",
  chrome: "px-5 py-5 md:px-6 xl:px-7",
  description: "mt-2 text-sm leading-6 text-stone-600 md:text-[15px] xl:text-base",
  nav: "space-y-7 px-5 pb-6 text-[15px] md:px-6 md:text-base xl:px-7 xl:text-[17px]",
  groupLabel: "mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-stone-500 md:text-[13px]",
  linkBase:
    "block whitespace-nowrap rounded border px-3 py-2 font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-moss focus-visible:ring-offset-2 md:px-3.5 md:py-2.5",
  linkActive: "border-moss bg-moss-soft text-moss-dark",
  linkInactive: "border-transparent bg-white text-stone-700 hover:border-stone-300 hover:text-moss-dark",
};

const pageStyles = {
  chrome: "px-4 md:px-6 xl:px-8 2xl:px-10",
  container: "mx-auto w-full max-w-[2400px]",
  headerInner: "mx-auto flex min-h-10 w-full max-w-[2400px] items-center justify-between gap-4",
};

function isActiveNavLink(pathname: string | null, href: string) {
  if (href === "/" || href === "/dev-admin") {
    return pathname === href;
  }
  return pathname === href || pathname?.startsWith(`${href}/`);
}

type ShellHeaderState = {
  title: string | null;
  actions: ReactNode | null;
};

type ShellHeaderContextValue = {
  setHeader: (state: ShellHeaderState) => void;
};

type BreadcrumbItem = {
  label: string;
  href: string | null;
};

const ShellHeaderContext = createContext<ShellHeaderContextValue | null>(null);

export function useShellHeader() {
  return useContext(ShellHeaderContext);
}

const routeLabels: Array<[RegExp, BreadcrumbItem[]]> = [
  [/^\/$/, [{ label: "Home", href: "/" }]],
  [/^\/demo$/, [{ label: "Home", href: "/" }, { label: "Guided Demo", href: "/demo" }]],
  [/^\/projects$/, [{ label: "Home", href: "/" }, { label: "Project Workspaces", href: "/projects" }]],
  [/^\/algorithm$/, [{ label: "Home", href: "/" }, { label: "Algorithm Guide", href: "/algorithm" }]],
  [
    /^\/projects\/([^/]+)$/,
    [
      { label: "Home", href: "/" },
      { label: "Project Workspaces", href: "/projects" },
      { label: "Project Workspace", href: null },
    ],
  ],
  [
    /^\/projects\/([^/]+)\/departments\/([^/]+)$/,
    [
      { label: "Home", href: "/" },
      { label: "Project Workspaces", href: "/projects" },
      { label: "Project Workspace", href: null },
      { label: "Department Workspace", href: null },
    ],
  ],
  [/^\/chat$/, [{ label: "Home", href: "/" }, { label: "Chat Demo", href: "/chat" }]],
  [/^\/dev-admin$/, [{ label: "Home", href: "/" }, { label: "Dev & Admin", href: "/dev-admin" }, { label: "Measured Enterprise RAG Progress", href: "/dev-admin" }]],
  [/^\/dev-admin\/runs$/, [{ label: "Home", href: "/" }, { label: "Dev & Admin", href: "/dev-admin" }, { label: "Run Comparison", href: "/dev-admin/runs" }]],
  [
    /^\/dev-admin\/evaluation\/runs\/[^/]+$/,
    [
      { label: "Home", href: "/" },
      { label: "Dev & Admin", href: "/dev-admin" },
      { label: "Run Comparison", href: "/dev-admin/runs" },
      { label: "Evaluation Run Detail", href: null },
    ],
  ],
  [
    /^\/dev-admin\/failed-questions$/,
    [{ label: "Home", href: "/" }, { label: "Dev & Admin", href: "/dev-admin" }, { label: "Failed Questions", href: "/dev-admin/failed-questions" }],
  ],
  [
    /^\/dev-admin\/retrieval-playground$/,
    [{ label: "Home", href: "/" }, { label: "Dev & Admin", href: "/dev-admin" }, { label: "Algorithm Quality Lab", href: "/dev-admin/retrieval-playground" }],
  ],
  [
    /^\/dev-admin\/permission-demo$/,
    [{ label: "Home", href: "/" }, { label: "Dev & Admin", href: "/dev-admin" }, { label: "Permission Demo", href: "/dev-admin/permission-demo" }],
  ],
  [/^\/dev-admin\/multi-doc$/, [{ label: "Home", href: "/" }, { label: "Dev & Admin", href: "/dev-admin" }, { label: "Multi-Document Reasoning", href: "/dev-admin/multi-doc" }]],
  [
    /^\/dev-admin\/observability$/,
    [{ label: "Home", href: "/" }, { label: "Dev & Admin", href: "/dev-admin" }, { label: "Observability", href: "/dev-admin/observability" }],
  ],
  [/^\/dev-admin\/feedback$/, [{ label: "Home", href: "/" }, { label: "Dev & Admin", href: "/dev-admin" }, { label: "Feedback Overview", href: "/dev-admin/feedback" }]],
  [/^\/dev-admin\/audit$/, [{ label: "Home", href: "/" }, { label: "Dev & Admin", href: "/dev-admin" }, { label: "Audit Log", href: "/dev-admin/audit" }]],
  [
    /^\/dev-admin\/retrieval-experiments$/,
    [{ label: "Home", href: "/" }, { label: "Dev & Admin", href: "/dev-admin" }, { label: "Retrieval Experiments", href: "/dev-admin/retrieval-experiments" }],
  ],
  [
    /^\/dev-admin\/prompt-experiments$/,
    [{ label: "Home", href: "/" }, { label: "Dev & Admin", href: "/dev-admin" }, { label: "Prompt History", href: "/dev-admin/prompt-experiments" }],
  ],
  [
    /^\/dev-admin\/permission-safety$/,
    [{ label: "Home", href: "/" }, { label: "Dev & Admin", href: "/dev-admin" }, { label: "Permission Safety", href: "/dev-admin/permission-safety" }],
  ],
  [
    /^\/dev-admin\/memory-evaluation$/,
    [{ label: "Home", href: "/" }, { label: "Dev & Admin", href: "/dev-admin" }, { label: "Memory Evaluation", href: "/dev-admin/memory-evaluation" }],
  ],
];

function fallbackBreadcrumb(pathname: string): BreadcrumbItem[] {
  if (pathname === "/") return [{ label: "Home", href: "/" }];
  const segments = pathname.split("/").filter(Boolean);
  return [
    { label: "Home", href: "/" },
    ...segments.map((segment, index) => {
      const href = `/${segments.slice(0, index + 1).join("/")}`;
      return {
        label: segment
          .split("-")
          .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
          .join(" "),
        href,
      };
    }),
  ];
}

function breadcrumbForPath(pathname: string, pageTitle: string | null): BreadcrumbItem[] {
  const labels = routeLabels.find(([pattern]) => pattern.test(pathname))?.[1] ?? fallbackBreadcrumb(pathname);
  const segments = pathname.split("/").filter(Boolean);
  const hydratedLabels = labels.map((item, index) => {
    if (item.href) return item;
    if (pathname.startsWith("/projects/") && index === 2 && segments[1]) {
      return { ...item, href: `/projects/${segments[1]}` };
    }
    if (pathname.startsWith("/projects/") && index === 3 && segments[1] && segments[3]) {
      return { ...item, href: `/projects/${segments[1]}/departments/${segments[3]}` };
    }
    return item;
  });
  if (!pageTitle || pathname === "/") return hydratedLabels;
  return [...hydratedLabels.slice(0, -1), { ...hydratedLabels[hydratedLabels.length - 1], label: pageTitle }];
}

export function Shell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const breadcrumbListRef = useRef<HTMLOListElement | null>(null);
  const [navOpen, setNavOpen] = useState(false);
  const [header, setHeader] = useState<ShellHeaderState>({ title: null, actions: null });
  const [demoUsers, setDemoUsers] = useState<DemoUser[]>([]);
  const [currentUser, setCurrentUser] = useState<DemoUser | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);
  const [isRouteRefreshPending, startRouteRefresh] = useTransition();
  const [hoveredBreadcrumbIndex, setHoveredBreadcrumbIndex] = useState<number | null>(null);
  const [breadcrumbHighlightWidth, setBreadcrumbHighlightWidth] = useState(0);
  const headerContext = useMemo(() => ({ setHeader }), []);
  const breadcrumbs = useMemo(() => breadcrumbForPath(pathname ?? "/", header.title), [pathname, header.title]);
  const isFullWidthRoute = pathname === "/chat";
  const isDevAdminRoute = Boolean(pathname?.startsWith("/dev-admin"));
  const devAdminChecking = isDevAdminRoute && ((!currentUser && !authError) || isRouteRefreshPending);
  const devAdminBlocked = isDevAdminRoute && currentUser && !currentUser.is_admin;
  const devAdminAuthUnavailable = isDevAdminRoute && authError;

  useEffect(() => {
    let cancelled = false;

    async function loadIdentity() {
      setAuthError(null);
      try {
        syncDemoUserCookie();
        const [users, user] = await Promise.all([fetchDemoUsers(), fetchCurrentDemoUser()]);
        if (cancelled) return;
        setDemoUsers(users);
        setCurrentUser(user);
      } catch (exc) {
        if (!cancelled) setAuthError(exc instanceof Error ? exc.message : "Demo identity unavailable.");
      }
    }

    loadIdentity();

    function onIdentityChanged() {
      setCurrentUser(null);
      loadIdentity();
      startRouteRefresh(() => {
        router.refresh();
      });
    }

    window.addEventListener(DEMO_USER_CHANGED_EVENT, onIdentityChanged);
    window.addEventListener("storage", onIdentityChanged);
    return () => {
      cancelled = true;
      window.removeEventListener(DEMO_USER_CHANGED_EVENT, onIdentityChanged);
      window.removeEventListener("storage", onIdentityChanged);
    };
  }, [router]);

  function toggleNav() {
    setNavOpen((current) => !current);
  }

  useEffect(() => {
    if (hoveredBreadcrumbIndex === null) {
      setBreadcrumbHighlightWidth(0);
      return;
    }

    const list = breadcrumbListRef.current;
    const item = list?.querySelector<HTMLElement>(`[data-breadcrumb-index="${hoveredBreadcrumbIndex}"]`);
    if (!list || !item) return;

    const listRect = list.getBoundingClientRect();
    const itemRect = item.getBoundingClientRect();
    setBreadcrumbHighlightWidth(itemRect.right - listRect.left);
  }, [hoveredBreadcrumbIndex, breadcrumbs]);

  return (
    <ShellHeaderContext.Provider value={headerContext}>
      <main className="min-h-screen bg-paper text-ink">
        <button
          type="button"
          aria-label="Hide navigation"
          onClick={toggleNav}
          className={`fixed inset-0 z-20 bg-ink/35 transition-opacity duration-200 ease-out ${
            navOpen ? "opacity-100" : "pointer-events-none opacity-0"
          }`}
          tabIndex={navOpen ? 0 : -1}
        />
        <aside
          className={`${navStyles.panel} ${
            navOpen ? "translate-x-0" : "pointer-events-none -translate-x-full"
          }`}
          aria-hidden={!navOpen}
        >
          <div className={`flex items-start justify-between gap-4 ${navStyles.chrome}`}>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-rust">Enterprise Knowledge Agent</p>
              <h1 className="mt-1 text-2xl font-semibold md:text-3xl">Knowledge Workspace</h1>
              <p className={navStyles.description}>
                App experience first, with Dev & Admin proof for quality, safety, and operations.
              </p>
            </div>
            <button
              type="button"
              onClick={toggleNav}
              aria-label="Hide navigation"
              aria-controls="primary-navigation"
              title="Hide navigation"
              tabIndex={navOpen ? undefined : -1}
              className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded border border-stone-300 bg-white text-ink shadow-card transition-colors hover:border-moss hover:text-moss-dark focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-moss focus-visible:ring-offset-2"
            >
              <span aria-hidden="true" className="text-lg font-semibold leading-none">
                X
              </span>
            </button>
          </div>
          <nav id="primary-navigation" className={navStyles.nav}>
            {navGroups.map((group) => (
              <div key={group.title}>
                <p className={navStyles.groupLabel}>
                  <group.icon className="h-4 w-4 text-moss-dark" aria-hidden="true" />
                  <span>{group.title}</span>
                </p>
                <div className="space-y-1">
                  {group.links.map(([label, href]) => {
                    const active = isActiveNavLink(pathname, href);
                    return (
                      <Link
                        key={href}
                        href={href}
                        aria-current={active ? "page" : undefined}
                        tabIndex={navOpen ? undefined : -1}
                        className={`${navStyles.linkBase} ${active ? navStyles.linkActive : navStyles.linkInactive}`}
                      >
                        {label}
                      </Link>
                    );
                  })}
                </div>
              </div>
            ))}
          </nav>
        </aside>
        <div className="min-w-0">
          <header className={`border-b border-stone-300 bg-white py-2 ${pageStyles.chrome}`}>
            <div className={isFullWidthRoute ? "flex min-h-10 w-full items-center justify-between gap-4" : pageStyles.headerInner}>
              <div className="flex min-w-0 items-center gap-3">
                <button
                  type="button"
                  onClick={toggleNav}
                  aria-label={navOpen ? "Hide navigation" : "Show navigation"}
                  aria-expanded={navOpen}
                  aria-controls="primary-navigation"
                  title={navOpen ? "Hide navigation" : "Show navigation"}
                  className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded border border-stone-300 bg-white text-ink shadow-card transition-colors hover:border-moss hover:text-moss-dark focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-moss focus-visible:ring-offset-2"
                >
                  <span aria-hidden="true" className="flex flex-col gap-1">
                    <span className="block h-0.5 w-4 rounded bg-current" />
                    <span className="block h-0.5 w-4 rounded bg-current" />
                    <span className="block h-0.5 w-4 rounded bg-current" />
                  </span>
                </button>
              <nav aria-label="Breadcrumb" className="min-w-0">
                <ol ref={breadcrumbListRef} className="relative flex min-w-0 items-center gap-2 text-sm text-stone-600">
                  <span
                    aria-hidden="true"
                    className="pointer-events-none absolute inset-y-0 left-0 rounded bg-moss-soft transition-[width] duration-150 ease-out"
                    style={{ width: breadcrumbHighlightWidth }}
                  />
                  {breadcrumbs.map((item, index) => {
                    const current = index === breadcrumbs.length - 1;
                    const highlighted = hoveredBreadcrumbIndex !== null && index <= hoveredBreadcrumbIndex;
                    const crumbClass = `relative z-10 truncate px-1.5 py-1 transition-colors ${
                      current ? "font-semibold" : ""
                    } ${highlighted ? "text-moss-dark" : current ? "text-ink" : "text-stone-600 hover:text-moss-dark"}`;
                    return (
                      <li
                        key={`${item.label}-${index}`}
                        data-breadcrumb-index={index}
                        className="flex min-w-0 items-center gap-2"
                        onMouseEnter={() => setHoveredBreadcrumbIndex(index)}
                        onMouseLeave={() => setHoveredBreadcrumbIndex(null)}
                        onFocus={() => setHoveredBreadcrumbIndex(index)}
                        onBlur={() => setHoveredBreadcrumbIndex(null)}
                      >
                        {index > 0 ? (
                          <span className={`relative z-10 ${highlighted ? "text-moss-dark" : "text-stone-400"}`}>/</span>
                        ) : null}
                        {item.href ? (
                          <Link href={item.href} aria-current={current ? "page" : undefined} className={crumbClass}>
                            {item.label}
                          </Link>
                        ) : (
                          <span aria-current={current ? "page" : undefined} className={crumbClass}>
                            {item.label}
                          </span>
                        )}
                      </li>
                    );
                  })}
                  </ol>
                </nav>
              </div>
              <div className="flex shrink-0 flex-wrap items-center justify-end gap-2">
                {!devAdminBlocked && !devAdminAuthUnavailable && header.actions ? header.actions : null}
                <label className="flex items-center gap-2 text-xs text-stone-600">
                  <span className="hidden font-semibold uppercase tracking-wide md:inline">Signed in as</span>
                  <select
                    value={currentUser?.id ?? selectedDemoUserId()}
                    onChange={(event) => setSelectedDemoUserId(event.target.value)}
                    className="h-9 max-w-56 rounded border border-stone-300 bg-white px-2 text-sm font-medium text-ink shadow-card focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-moss"
                    aria-label="Signed in as"
                  >
                    {demoUsers.length ? null : <option value={selectedDemoUserId()}>Loading identity...</option>}
                    {demoUsers.map((user) => (
                      <option key={user.id} value={user.id}>
                        {user.display_name} - {user.business_role}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
            </div>
          </header>
          <div className={`py-5 ${pageStyles.chrome}`}>
            <div className={`${pageStyles.container} page-content`}>
              {devAdminChecking ? (
                <div className="card">
                  <p className="font-semibold text-ink">Checking Dev & Admin access</p>
                  <p className="mt-2 text-sm text-stone-600">Loading the local demo identity before showing admin evidence.</p>
                </div>
              ) : devAdminAuthUnavailable ? (
                <div className="card max-w-3xl">
                  <p className="text-xs font-semibold uppercase tracking-wide text-rust">Demo identity unavailable</p>
                  <h2 className="mt-2 text-2xl font-semibold text-ink">Dev & Admin access cannot be verified</h2>
                  <p className="mt-3 text-stone-700">{authError}</p>
                </div>
              ) : devAdminBlocked ? (
                <div className="card max-w-3xl">
                  <p className="text-xs font-semibold uppercase tracking-wide text-rust">Access denied</p>
                  <h2 className="mt-2 text-2xl font-semibold text-ink">Dev & Admin requires Admin access</h2>
                  <p className="mt-3 text-stone-700">
                    {currentUser.display_name} is signed in as {currentUser.business_role}. Switch to Kai Admin to review evaluation runs,
                    audit logs, observability, and admin-only simulation tools.
                  </p>
                </div>
              ) : (
                children
              )}
            </div>
          </div>
        </div>
      </main>
    </ShellHeaderContext.Provider>
  );
}
