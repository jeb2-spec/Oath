/**
 * An annual financial disclosure report dated after the latest date an extension could reach.
 *
 * The reference implementation of sg:annual-report-after-extension-limit:v1. It shares no code
 * with src/signals/annual-report-after-extension-limit.py, which writes the register's
 * Findings; a Vitest test holds the two to the same known-answer cases, so neither can drift.
 * Written from docs/signals/annual-report-after-extension-limit.md, in day numbers counted
 * from 1970-01-01 in UTC, so no clock or time zone enters it.
 */

export const SLUG = "annual-report-after-extension-limit";
export const VERSION = 1;
export const SIGNAL_ID = `sg:${SLUG}:v${VERSION}`;
export const FRAME = "Presence in the register is not evidence of wrongdoing.";
const FILING_TYPE = "Annual Report";
const STATUS = "Member";
const EXTENSION_DAYS = 90;
const SERVICE_DAYS = 60;
const FIRST_YEAR = 2025;
const LAST_YEAR = 2025;
const CITATION = "5 U.S.C. § 13103(d), (g)(1)";
const DAY_MS = 86_400_000;

export const REASONS = {
  noYear: "prints no filing year",
  yearUnread: "a filing year whose instructions the register has not read",
  noDate: "a date the register cannot read",
  datesDisagree: "the index date, the printed filing date and the signature date disagree",
  noSwearingIn: "the roster records no swearing-in",
  shortService: "60 days or fewer of service in the filing year, by the swearing-in recorded",
  later: "a later annual report for a filing year for which the register reads an earlier one",
  within: "after the original due date, within the time an extension may cover",
  dayAfter:
    "the day after the latest date, and the register has not established the time zone of the " +
    "printed date",
} as const;

export interface Holder {
  id: string;
  sworn_at?: string | null;
}

export interface Filing {
  id: string;
  officeholder_id: string;
  filed_at?: string | null;
  printed?: Record<string, unknown> | null;
}

export interface Outcome {
  filing_id: string;
  officeholder_id: string;
  filed_at: string | null;
  state: "evaluated";
  rows: number;
  evaluated: number;
  after: number;
  not_evaluated: Record<string, number>;
  finding_id: string | null;
  original_due?: string;
  latest?: string;
}

export interface Finding {
  id: string;
  signal_id: string;
  officeholder_id: string;
  producing_filings: string[];
  description: string;
  evidence: Record<string, unknown>;
  frame: string;
  superseded_by: null;
  notes: null;
}

// ---- days -----------------------------------------------------------------------------------

function day(year: number, month: number, date: number): number {
  return Math.round(Date.UTC(year, month - 1, date) / DAY_MS);
}

export function readDate(value: unknown): number | null {
  if (typeof value !== "string") return null;
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!m) return null;
  const [year, month, date] = [Number(m[1]), Number(m[2]), Number(m[3])];
  const n = day(year, month, date);
  const back = new Date(n * DAY_MS);
  if (back.getUTCMonth() + 1 !== month || back.getUTCDate() !== date) return null;
  return n;
}

export function iso(n: number): string {
  return new Date(n * DAY_MS).toISOString().slice(0, 10);
}

function yearOf(n: number): number {
  return new Date(n * DAY_MS).getUTCFullYear();
}

/** 0 is Sunday, 6 is Saturday, as Date counts them. */
function dow(n: number): number {
  return new Date(n * DAY_MS).getUTCDay();
}

// ---- the federal calendar, 5 U.S.C. § 6103, on the days observed -----------------------------

function nth(year: number, month: number, weekday: number, count: number): number {
  const first = day(year, month, 1);
  return first + ((weekday - dow(first) + 7) % 7) + 7 * (count - 1);
}

function lastOf(year: number, month: number, weekday: number): number {
  const last = day(year, month + 1, 1) - 1;
  return last - ((dow(last) - weekday + 7) % 7);
}

function holidays(year: number): Map<number, string> {
  const out = new Map<number, string>();
  const fixed: [string, number][] = [
    ["New Year's Day", day(year, 1, 1)],
    ["Juneteenth National Independence Day", day(year, 6, 19)],
    ["Independence Day", day(year, 7, 4)],
    ["Veterans Day", day(year, 11, 11)],
    ["Christmas Day", day(year, 12, 25)],
  ];
  for (const [name, n] of fixed) {
    const shift = dow(n) === 6 ? -1 : dow(n) === 0 ? 1 : 0;
    out.set(n + shift, shift ? `${name} (observed)` : name);
  }
  const moving: [string, number][] = [
    ["Birthday of Martin Luther King, Jr.", nth(year, 1, 1, 3)],
    ["Washington's Birthday", nth(year, 2, 1, 3)],
    ["Memorial Day", lastOf(year, 5, 1)],
    ["Labor Day", nth(year, 9, 1, 1)],
    ["Columbus Day", nth(year, 10, 1, 2)],
    ["Thanksgiving Day", nth(year, 11, 4, 4)],
  ];
  for (const [name, n] of moving) out.set(n, name);
  return out;
}

function notBusiness(n: number): string | null {
  if (dow(n) === 6) return "Saturday";
  if (dow(n) === 0) return "Sunday";
  return holidays(yearOf(n)).get(n) ?? holidays(yearOf(n) + 1).get(n) ?? null;
}

function toBusinessDay(n: number): [number, string | null] {
  const why = notBusiness(n);
  let moved = n;
  while (notBusiness(moved)) moved += 1;
  return [moved, why];
}

// ---- one report -----------------------------------------------------------------------------

interface Result {
  state: "evaluated" | "not evaluated";
  reason: string | null;
  after: boolean;
  year?: number;
  dated?: number;
  due?: number;
  dueMovedFor?: string | null;
  latest?: number;
  latestMovedFor?: string | null;
  cap?: number;
}

/** The two dates the law sets for a filing year, and why either moved, as the Signal takes them;
 * exported so the known answers can hold the calendar for years this version does not read. */
export function datesFor(year: number): Record<string, string | null> {
  const may15 = day(year + 1, 5, 15);
  const [due, dueMovedFor] = toBusinessDay(may15);
  const [latest, latestMovedFor] = toBusinessDay(
    Math.max(may15 + EXTENSION_DAYS, due + EXTENSION_DAYS),
  );
  return {
    original_due: iso(due),
    original_due_moved_for: dueMovedFor,
    latest: iso(latest),
    latest_moved_for: latestMovedFor,
  };
}

export function isAnnual(filing: Filing): boolean {
  const p = filing.printed ?? {};
  return p.filing_type === FILING_TYPE && p.status === STATUS;
}

export function evaluateReport(filing: Filing, swornAt: number | null, later = false): Result {
  const p = filing.printed ?? {};
  const no = (reason: string): Result => ({ state: "not evaluated", reason, after: false });
  const year = p.filing_year;
  if (typeof year !== "number" || !Number.isInteger(year)) return no(REASONS.noYear);
  if (year < FIRST_YEAR || year > LAST_YEAR) return no(REASONS.yearUnread);
  const may15 = day(year + 1, 5, 15);
  const [due, dueMovedFor] = toBusinessDay(may15);
  const cap = Math.max(may15 + EXTENSION_DAYS, due + EXTENSION_DAYS);
  const [latest, latestMovedFor] = toBusinessDay(cap);
  const known = { year, due, dueMovedFor, latest, latestMovedFor, cap };
  const not = (reason: string): Result => ({ ...no(reason), ...known });
  if (later) return not(REASONS.later);
  const dates = [readDate(filing.filed_at), readDate(p.filing_date), readDate(p.signed_on)];
  if (dates.some((d) => d === null)) return not(REASONS.noDate);
  if (new Set(dates).size !== 1) return not(REASONS.datesDisagree);
  if (swornAt === null) return not(REASONS.noSwearingIn);
  const served = day(year, 12, 31) - Math.max(swornAt, day(year, 1, 1)) + 1;
  if (served <= SERVICE_DAYS) return not(REASONS.shortService);
  const dated = dates[0] as number;
  const facts = { ...known, dated };
  if (dated <= due) return { state: "evaluated", reason: null, after: false, ...facts };
  if (dated <= latest) return { ...not(REASONS.within), dated };
  if (dated === latest + 1) return { ...not(REASONS.dayAfter), dated };
  return { state: "evaluated", reason: null, after: true, ...facts };
}

function describe(r: Required<Result>): string {
  return (
    `This is an annual financial disclosure report for calendar year ${r.year}. The Clerk's ` +
    `index dates it ${iso(r.dated)}, the same date the report prints as its filing date and ` +
    `its signature line gives. Its original due date was ${iso(r.due)}. Outside a combat ` +
    `zone the statute lets extensions add at most ${EXTENSION_DAYS} days to it (${CITATION}), ` +
    `so the latest date any such extension could reach was ${iso(r.latest)}. The report ` +
    "is dated " +
    `${r.dated - r.latest} days after that latest date. The register cannot see an extension ` +
    "for service in a combat zone, which 5 U.S.C. § 13103(g)(2) allows beyond 90 days."
  );
}

export function evaluate(holders: Holder[], filings: Filing[]): [Finding[], Outcome[]] {
  const sworn = new Map(holders.map((h) => [h.id, readDate(h.sworn_at)]));
  const findings: Finding[] = [];
  const outcomes: Outcome[] = [];
  const byId = (a: Filing, b: Filing) => (a.id < b.id ? -1 : a.id > b.id ? 1 : 0);
  const reports = filings.filter(isAnnual).sort(byId);
  // The earliest report the index lists for each officeholder and filing year, then by id.
  const yearOf = (f: Filing) => String(f.printed?.filing_year);
  const earliest = new Map<string, string>();
  const byDate = [...reports].sort((a, b) => {
    const [x, y] = [a.filed_at ?? "", b.filed_at ?? ""];
    return x < y ? -1 : x > y ? 1 : byId(a, b);
  });
  for (const f of byDate) {
    const key = `${f.officeholder_id}\u0000${yearOf(f)}`;
    if (!earliest.has(key)) earliest.set(key, f.id);
  }
  for (const report of reports) {
    const later = earliest.get(`${report.officeholder_id}\u0000${yearOf(report)}`) !== report.id;
    const r = evaluateReport(report, sworn.get(report.officeholder_id) ?? null, later);
    let found: Finding | null = null;
    if (r.after) {
      const full = r as Required<Result>;
      found = {
        id: `fn:${SIGNAL_ID}:${report.id}`,
        signal_id: SIGNAL_ID,
        officeholder_id: report.officeholder_id,
        producing_filings: [report.id],
        description: describe(full),
        evidence: {
          after: 1,
          filed_at: report.filed_at,
          filing_year: full.year,
          original_due: iso(full.due),
          latest: iso(full.latest),
          days_after_latest: full.dated - full.latest,
        },
        frame: FRAME,
        superseded_by: null,
        notes: null,
      };
      findings.push(found);
    }
    outcomes.push({
      filing_id: report.id,
      officeholder_id: report.officeholder_id,
      filed_at: report.filed_at ?? null,
      // The house shape: the report is read (its header), and its one row, its own date, is
      // compared or set aside with the reason, as a transaction row is on a transaction report.
      state: "evaluated",
      rows: 1,
      evaluated: r.state === "evaluated" ? 1 : 0,
      after: r.after ? 1 : 0,
      not_evaluated: r.reason ? { [r.reason]: 1 } : {},
      finding_id: found ? found.id : null,
      // The two dates the report is compared with, wherever its filing year gives them.
      ...(r.due !== undefined && r.latest !== undefined
        ? { original_due: iso(r.due), latest: iso(r.latest) }
        : {}),
    });
  }
  return [findings, outcomes];
}
