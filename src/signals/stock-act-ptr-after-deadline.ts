/**
 * A Periodic Transaction Report dated after the STOCK Act deadline. sg:stock-act-ptr-after-deadline:v1.
 *
 * The reference implementation the course named (NEXT.md S.2; PIPELINE.md, Signal contract).
 * It shares no code with src/signals/stock-act-ptr-after-deadline.py, which writes the
 * register's Findings; stock-act-ptr-after-deadline.test.ts requires the two to agree on every
 * known-answer case in fixtures/stock-act-ptr-after-deadline/cases.json and on every Finding
 * and report outcome the register holds, byte for byte, so a disagreement between them fails
 * CI instead of reaching a page.
 *
 * Pure: no file, no network, no clock. Dates are whole days counted from 1970-01-01 in UTC, so
 * no time zone can move one. The definition is docs/signals/stock-act-ptr-after-deadline.md;
 * the rule is 5 U.S.C. § 13105(l): the earlier of 30 days after notification and 45 days after
 * the transaction, in calendar days, not moved for a weekend or holiday, for the transactions
 * the rule plainly reaches.
 */

export const SLUG = "stock-act-ptr-after-deadline";
export const VERSION = 1;
export const SIGNAL_ID = `sg:${SLUG}:v${VERSION}`;
const FORM_TYPE = "House-PTR";
const NOTIFICATION_DAYS = 30;
const TRANSACTION_DAYS = 45;
const THRESHOLD = 1000;
const CITATION = "5 U.S.C. § 13105(l)";
export const FRAME = "Presence in the register is not evidence of wrongdoing.";
const EVALUATED_CODES = new Set(["CS", "CT", "OP", "ST"]);
const ETF = /\bETF\b/;
const DAY_MS = 86_400_000;

export interface Holder {
  id: string;
  sworn_at?: string | null;
}
export interface Filing {
  id: string;
  officeholder_id: string;
  form_type?: string;
  filed_at?: string | null;
  extraction_confidence?: string | null;
}
export interface Transaction {
  id: string;
  filing_id: string;
  asset?: string;
  asset_code?: string | null;
  amount_range?: { min?: number | null; max?: number | null } | null;
  transaction_date?: unknown;
  notified_date?: unknown;
  filing_status?: string | null;
}

type Notification =
  | "applied"
  | "not printed"
  | "not read"
  | "before the transaction"
  | "after the report";
type SetBy = "notification" | "transaction";

export type RowResult =
  | { state: "not evaluated"; reason: string }
  | { state: "on time"; deadline: string; set_by: SetBy; notification: Notification }
  | {
      state: "after";
      deadline: string;
      set_by: SetBy;
      notification: Notification;
      days_after: number;
      deadline_falls_on: string | null;
      first_business_day_after: string | null;
      notified_after_limit: boolean;
      days_after_notice: number | null;
    };

export interface EvidenceRow {
  id: string;
  transaction_date: unknown;
  notified_date: unknown;
  notification: Notification;
  deadline: string;
  set_by: SetBy;
  days_after: number;
  deadline_falls_on: string | null;
  first_business_day_after: string | null;
  notified_after_limit: boolean;
  days_after_notice: number | null;
}

export interface ReportResult {
  state: "evaluated" | "not read" | "not evaluated";
  rows: number;
  evaluated: number;
  after: number;
  not_evaluated: Record<string, number>;
  results: Record<string, RowResult>;
  after_rows: EvidenceRow[];
}

export interface Outcome {
  filing_id: string;
  officeholder_id: string;
  filed_at: string | null;
  state: ReportResult["state"];
  rows: number;
  evaluated: number;
  after: number;
  not_evaluated: Record<string, number>;
  finding_id: string | null;
}

export interface Finding {
  id: string;
  signal_id: string;
  officeholder_id: string;
  producing_filings: string[];
  producing_rows: { schema: "transaction"; id: string }[];
  description: string;
  evidence: {
    filed_at: string;
    rows_on_report: number;
    evaluated: number;
    after: number;
    not_evaluated: Record<string, number>;
    rows: EvidenceRow[];
  };
  frame: string;
  superseded_by: null;
  notes: null;
}

// ---- days ------------------------------------------------------------------------------------

/** The day number of a calendar date; month is 1 to 12, and day 0 is the month's eve. */
function dayOf(year: number, month: number, day: number): number {
  const date = new Date(0);
  date.setUTCFullYear(year, month - 1, day);
  return Math.round(date.getTime() / DAY_MS);
}

/** A real calendar date written YYYY-MM-DD, as a day number; null for anything else. */
export function readDate(value: unknown): number | null {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
  const year = Number(value.slice(0, 4));
  const month = Number(value.slice(5, 7));
  const day = Number(value.slice(8, 10));
  if (year < 1) return null;
  const date = new Date(0);
  date.setUTCFullYear(year, month - 1, day);
  if (
    date.getUTCFullYear() !== year ||
    date.getUTCMonth() !== month - 1 ||
    date.getUTCDate() !== day
  ) {
    return null;
  }
  return Math.round(date.getTime() / DAY_MS);
}

export function isoDate(dayNumber: number): string {
  const date = new Date(dayNumber * DAY_MS);
  const pad = (n: number, width: number) => String(n).padStart(width, "0");
  return `${pad(date.getUTCFullYear(), 4)}-${pad(date.getUTCMonth() + 1, 2)}-${pad(date.getUTCDate(), 2)}`;
}

/** Monday 0 to Sunday 6. */
function weekday(dayNumber: number): number {
  return (new Date(dayNumber * DAY_MS).getUTCDay() + 6) % 7;
}

const RULE_FROM = dayOf(2025, 1, 1);

// ---- the federal calendar, 5 U.S.C. § 6103 ---------------------------------------------------

function nthWeekday(year: number, month: number, day: number, n: number): number {
  const first = dayOf(year, month, 1);
  return first + ((day - weekday(first) + 7) % 7) + 7 * (n - 1);
}

function lastWeekday(year: number, month: number, day: number): number {
  const last = dayOf(year, month + 1, 0);
  return last - ((weekday(last) - day + 7) % 7);
}

function observed(dayNumber: number): number {
  const w = weekday(dayNumber);
  return w === 5 ? dayNumber - 1 : w === 6 ? dayNumber + 1 : dayNumber;
}

const holidayCache = new Map<number, Map<number, string>>();

function federalHolidays(year: number): Map<number, string> {
  const cached = holidayCache.get(year);
  if (cached) return cached;
  const out = new Map<number, string>();
  const fixed: [string, number][] = [
    ["New Year's Day", dayOf(year, 1, 1)],
    ["Independence Day", dayOf(year, 7, 4)],
    ["Veterans Day", dayOf(year, 11, 11)],
    ["Christmas Day", dayOf(year, 12, 25)],
  ];
  if (year >= 2021) fixed.push(["Juneteenth National Independence Day", dayOf(year, 6, 19)]);
  for (const [name, day] of fixed) {
    const on = observed(day);
    out.set(on, on === day ? name : `${name} (observed)`);
  }
  out.set(nthWeekday(year, 1, 0, 3), "Birthday of Martin Luther King, Jr.");
  out.set(nthWeekday(year, 2, 0, 3), "Washington's Birthday");
  out.set(lastWeekday(year, 5, 0), "Memorial Day");
  out.set(nthWeekday(year, 9, 0, 1), "Labor Day");
  out.set(nthWeekday(year, 10, 0, 2), "Columbus Day");
  out.set(nthWeekday(year, 11, 3, 4), "Thanksgiving Day");
  holidayCache.set(year, out);
  return out;
}

function holiday(dayNumber: number): string | null {
  const year = new Date(dayNumber * DAY_MS).getUTCFullYear();
  return federalHolidays(year).get(dayNumber) ?? federalHolidays(year + 1).get(dayNumber) ?? null;
}

function notABusinessDay(dayNumber: number): string | null {
  const w = weekday(dayNumber);
  if (w === 5) return "Saturday";
  if (w === 6) return "Sunday";
  return holiday(dayNumber);
}

function firstBusinessDayAfter(dayNumber: number): number {
  let day = dayNumber + 1;
  while (notABusinessDay(day)) day += 1;
  return day;
}

function holidaysBetween(start: number, end: number): [string, string][] {
  const out: [string, string][] = [];
  for (let day = start + 1; day < end; day += 1) {
    const name = holiday(day);
    if (name && weekday(day) < 5) out.push([isoDate(day), name]);
  }
  return out;
}

// ---- one row, one report ---------------------------------------------------------------------

function outOfScope(row: Transaction): string | null {
  const code = row.asset_code;
  if (!code) return "no asset code printed";
  if (!EVALUATED_CODES.has(code)) return `asset coded ${code}`;
  if (code === "ST" && ETF.test(row.asset ?? "")) return "coded as a stock, named as an ETF";
  const top = row.amount_range?.max;
  if (top !== null && top !== undefined && top <= THRESHOLD) return "$1,000 or less";
  return null;
}

export function evaluateRow(
  row: Transaction,
  filedAt: number | null,
  swornAt: number | null,
): RowResult {
  const status = (row.filing_status ?? "").trim();
  if (!status) return { state: "not evaluated", reason: "no filing status printed" };
  if (status.toLowerCase() !== "new") return { state: "not evaluated", reason: `marked ${status}` };
  if (filedAt === null) return { state: "not evaluated", reason: "report date not read" };
  const traded = readDate(row.transaction_date);
  if (traded === null) return { state: "not evaluated", reason: "transaction date not read" };
  const scope = outOfScope(row);
  if (scope) return { state: "not evaluated", reason: scope };
  if (swornAt === null) return { state: "not evaluated", reason: "no swearing-in date recorded" };
  if (traded < swornAt) {
    return { state: "not evaluated", reason: "dated before this Congress's swearing-in" };
  }
  if (traded > filedAt) {
    return { state: "not evaluated", reason: "transaction dated after the report" };
  }

  const printed = row.notified_date;
  const notified = readDate(printed);
  let notification: Notification;
  if (printed === null || printed === undefined || printed === "") notification = "not printed";
  else if (notified === null) notification = "not read";
  else if (notified < traded) notification = "before the transaction";
  else if (notified > filedAt) notification = "after the report";
  else notification = "applied";

  let deadline = traded + TRANSACTION_DAYS;
  let setBy: SetBy = "transaction";
  if (notification === "applied" && notified !== null && notified + NOTIFICATION_DAYS < deadline) {
    deadline = notified + NOTIFICATION_DAYS;
    setBy = "notification";
  }
  if (deadline < RULE_FROM) return { state: "not evaluated", reason: "deadline before 2025" };
  const daysAfter = filedAt - deadline;
  if (daysAfter <= 0) {
    return { state: "on time", deadline: isoDate(deadline), set_by: setBy, notification };
  }
  const fallsOn = notABusinessDay(deadline);
  return {
    state: "after",
    deadline: isoDate(deadline),
    set_by: setBy,
    notification,
    days_after: daysAfter,
    deadline_falls_on: fallsOn,
    first_business_day_after: fallsOn ? isoDate(firstBusinessDayAfter(deadline)) : null,
    notified_after_limit: notification === "applied" && notified !== null && notified > deadline,
    days_after_notice: notification === "applied" && notified !== null ? filedAt - notified : null,
  };
}

export function evaluateReport(
  report: Filing,
  rows: Transaction[],
  swornAt: number | null,
): ReportResult {
  const results: Record<string, RowResult> = {};
  let state: ReportResult["state"];
  if (report.extraction_confidence !== "structured") {
    state = "not read";
  } else {
    const filedAt = readDate(report.filed_at);
    state = filedAt === null ? "not evaluated" : "evaluated";
    for (const row of rows) results[row.id] = evaluateRow(row, filedAt, swornAt);
  }
  const notEvaluated: Record<string, number> = {};
  let evaluated = 0;
  for (const result of Object.values(results)) {
    if (result.state === "not evaluated") {
      notEvaluated[result.reason] = (notEvaluated[result.reason] ?? 0) + 1;
    } else {
      evaluated += 1;
    }
  }
  const afterRows: EvidenceRow[] = [];
  for (const row of rows) {
    const result = results[row.id];
    if (result?.state === "after") {
      afterRows.push({
        id: row.id,
        transaction_date: row.transaction_date ?? null,
        notified_date: row.notified_date ?? null,
        notification: result.notification,
        deadline: result.deadline,
        set_by: result.set_by,
        days_after: result.days_after,
        deadline_falls_on: result.deadline_falls_on,
        first_business_day_after: result.first_business_day_after,
        notified_after_limit: result.notified_after_limit,
        days_after_notice: result.days_after_notice,
      });
    }
  }
  return {
    state,
    rows: rows.length,
    evaluated,
    after: afterRows.length,
    not_evaluated: notEvaluated,
    results,
    after_rows: afterRows,
  };
}

// ---- the words -------------------------------------------------------------------------------

function thousands(n: number): string {
  return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

function those(part: number, whole: number): string {
  if (part === 1 && whole === 1) return "that transaction";
  if (part === whole) return "each of them";
  return `${thousands(part)} of them`;
}

function daysPhrase(low: number, high: number): string {
  if (low === high) return `${thousands(low)} ${low === 1 ? "day" : "days"}`;
  return `${thousands(low)} to ${thousands(high)} days`;
}

export function describe(filedAt: string, evaluated: number, after: EvidenceRow[]): string {
  const k = after.length;
  const days = after.map((r) => r.days_after);
  let which: string;
  if (evaluated === 1) which = "the one transaction on it that this Signal evaluated";
  else if (k === evaluated) {
    which = `each of the ${thousands(evaluated)} transactions on it that this Signal evaluated`;
  } else {
    which = `${thousands(k)} of the ${thousands(evaluated)} transactions on it that this Signal evaluated`;
  }
  let text =
    `The Clerk's index dates this report ${filedAt}, which is later than the deadline the rule ` +
    `sets for ${which}, by ${daysPhrase(Math.min(...days), Math.max(...days))}. The deadline is ` +
    "the earlier of 30 days after the notification date the report prints and 45 days after " +
    `the transaction date (${CITATION}).`;
  const unusable = after.filter((r) => r.notification !== "applied").length;
  if (unusable) {
    text +=
      ` For ${those(unusable, k)} the report prints no usable notification date, so the ` +
      "deadline is 45 days after the transaction.";
  }
  const late = after.filter((r) => r.notified_after_limit);
  if (late.length) {
    const gap = late.map((r) => r.days_after_notice ?? 0);
    const when =
      Math.max(...gap) === 0
        ? "the same day as that notification"
        : `${daysPhrase(Math.min(...gap), Math.max(...gap))} after it`;
    text +=
      ` For ${those(late.length, k)} the report prints a notification date later than 45 days ` +
      "after the transaction, so the deadline had passed before that notification; the " +
      `Clerk's index dates the report ${when}.`;
  }
  const decided = after.filter(
    (r) =>
      r.deadline_falls_on !== null &&
      r.first_business_day_after !== null &&
      filedAt <= r.first_business_day_after,
  );
  if (decided.length) {
    const kinds = [...new Set(decided.map((r) => r.deadline_falls_on))];
    const only = kinds.length === 1 ? kinds[0] : null;
    const kind =
      only === "Saturday" || only === "Sunday"
        ? `a ${only}`
        : only
          ? `${only}, a federal holiday`
          : "a weekend or a federal holiday";
    const nextDays = [...new Set(decided.map((r) => r.first_business_day_after))];
    const nextDay = nextDays.length === 1 ? nextDays[0] : null;
    const between = new Map<string, [string, string]>();
    for (const r of decided) {
      const start = readDate(r.deadline);
      const end = readDate(r.first_business_day_after);
      if (start === null || end === null) continue;
      for (const pair of holidaysBetween(start, end)) between.set(pair.join("|"), pair);
    }
    const held = [...between.values()]
      .sort((a, b) => (a[0] + a[1] < b[0] + b[1] ? -1 : a[0] + a[1] > b[0] + b[1] ? 1 : 0))
      .map(([day, name]) => `${name}, ${day}, was a federal holiday`)
      .join("; ");
    text +=
      ` For ${those(decided.length, k)} the deadline fell on ${kind}, and the Clerk's index ` +
      "dates the report on or before the first business day after it" +
      (nextDay ? `, ${nextDay}` : "") +
      (held ? ` (${held})` : "") +
      "; the Committee's instructions for these reports state that a due date on a weekend or " +
      "holiday does not move.";
  }
  return text;
}

export function finding(report: Filing, result: ReportResult): Finding | null {
  const after = result.after_rows;
  if (!after.length || typeof report.filed_at !== "string") return null;
  return {
    id: `fn:${SIGNAL_ID}:${report.id}`,
    signal_id: SIGNAL_ID,
    officeholder_id: report.officeholder_id,
    producing_filings: [report.id],
    producing_rows: after.map((r) => ({ schema: "transaction", id: r.id })),
    description: describe(report.filed_at, result.evaluated, after),
    evidence: {
      filed_at: report.filed_at,
      rows_on_report: result.rows,
      evaluated: result.evaluated,
      after: result.after,
      not_evaluated: result.not_evaluated,
      rows: after,
    },
    frame: FRAME,
    superseded_by: null,
    notes: null,
  };
}

const byId = <T extends { id: string }>(a: T, b: T) => (a.id < b.id ? -1 : a.id > b.id ? 1 : 0);

/** Every House transaction report, in id order: the Findings and one outcome per report. */
export function evaluate(
  holders: Holder[],
  filings: Filing[],
  transactions: Transaction[],
): { findings: Finding[]; outcomes: Outcome[] } {
  const sworn = new Map(holders.map((h) => [h.id, readDate(h.sworn_at)]));
  const byReport = new Map<string, Transaction[]>();
  for (const row of transactions) {
    const list = byReport.get(row.filing_id) ?? [];
    list.push(row);
    byReport.set(row.filing_id, list);
  }
  const findings: Finding[] = [];
  const outcomes: Outcome[] = [];
  const reports = filings.filter((f) => f.form_type === FORM_TYPE).sort(byId);
  for (const report of reports) {
    const rows = [...(byReport.get(report.id) ?? [])].sort(byId);
    const result = evaluateReport(report, rows, sworn.get(report.officeholder_id) ?? null);
    const found = finding(report, result);
    if (found) findings.push(found);
    outcomes.push({
      filing_id: report.id,
      officeholder_id: report.officeholder_id,
      filed_at: report.filed_at ?? null,
      state: result.state,
      rows: result.rows,
      evaluated: result.evaluated,
      after: result.after,
      not_evaluated: result.not_evaluated,
      finding_id: found ? found.id : null,
    });
  }
  return { findings, outcomes };
}
