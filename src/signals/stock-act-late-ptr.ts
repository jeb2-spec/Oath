/**
 * Periodic Transaction Report filed after the STOCK Act deadline. sg:stock-act-late-ptr:v1.
 *
 * The reference implementation the course named (NEXT.md S.2; PIPELINE.md, Signal contract).
 * It shares no code with src/signals/stock-act-late-ptr.py, which writes the register's
 * Findings; stock-act-late-ptr.test.ts requires the two to agree on every known-answer case in
 * fixtures/stock-act-late-ptr/cases.json and on every Finding and report outcome the register
 * holds, byte for byte, so a disagreement between them fails CI instead of reaching a page.
 *
 * Pure: no file, no network, no clock. Dates are whole days counted from 1970-01-01 in UTC, so
 * no time zone can move one. The definition is docs/signals/stock-act-late-ptr.md; the rule is
 * 5 U.S.C. § 13105(l): the earlier of 30 days after notification and 45 days after the
 * transaction, in calendar days, not moved for a weekend.
 */

export const SLUG = "stock-act-late-ptr";
export const VERSION = 1;
export const SIGNAL_ID = `sg:${SLUG}:v${VERSION}`;
const FORM_TYPE = "House-PTR";
const NOTIFICATION_DAYS = 30;
const TRANSACTION_DAYS = 45;
const CITATION = "5 U.S.C. § 13105(l)";
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

export type RowResult =
  | { state: "not evaluated"; reason: string }
  | {
      state: "on time";
      deadline: string;
      set_by: "notification" | "transaction";
      notification: Notification;
    }
  | {
      state: "after";
      deadline: string;
      set_by: "notification" | "transaction";
      notification: Notification;
      days_after: number;
      weekend: "Saturday" | "Sunday" | null;
      notified_after_limit: boolean;
    };

export interface EvidenceRow {
  id: string;
  transaction_date: unknown;
  notified_date: unknown;
  notification: Notification;
  deadline: string;
  set_by: "notification" | "transaction";
  days_after: number;
  weekend: "Saturday" | "Sunday" | null;
  notified_after_limit: boolean;
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
  superseded_by: null;
  notes: null;
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

function weekend(dayNumber: number): "Saturday" | "Sunday" | null {
  const weekday = new Date(dayNumber * DAY_MS).getUTCDay();
  return weekday === 6 ? "Saturday" : weekday === 0 ? "Sunday" : null;
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
  if (swornAt === null) return { state: "not evaluated", reason: "no swearing-in date recorded" };
  if (traded < swornAt) return { state: "not evaluated", reason: "dated before the swearing-in" };
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
  let setBy: "notification" | "transaction" = "transaction";
  if (notification === "applied" && notified !== null && notified + NOTIFICATION_DAYS < deadline) {
    deadline = notified + NOTIFICATION_DAYS;
    setBy = "notification";
  }
  const daysAfter = filedAt - deadline;
  if (daysAfter <= 0) {
    return { state: "on time", deadline: isoDate(deadline), set_by: setBy, notification };
  }
  return {
    state: "after",
    deadline: isoDate(deadline),
    set_by: setBy,
    notification,
    days_after: daysAfter,
    weekend: weekend(deadline),
    notified_after_limit: notification === "applied" && notified !== null && notified > deadline,
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
        weekend: result.weekend,
        notified_after_limit: result.notified_after_limit,
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

function thousands(n: number): string {
  return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

function those(part: number, whole: number): string {
  if (part === 1 && whole === 1) return "that transaction";
  if (part === whole) return "each of them";
  return `${thousands(part)} of them`;
}

export function describe(filedAt: string, evaluated: number, after: EvidenceRow[]): string {
  const k = after.length;
  const days = after.map((r) => r.days_after);
  const low = Math.min(...days);
  const high = Math.max(...days);
  const span =
    low === high
      ? `${thousands(low)} ${low === 1 ? "day" : "days"}`
      : `${thousands(low)} to ${thousands(high)} days`;
  let which: string;
  if (evaluated === 1) which = "the one transaction on it that this Signal evaluated";
  else if (k === evaluated) {
    which = `each of the ${thousands(evaluated)} transactions on it that this Signal evaluated`;
  } else {
    which = `${thousands(k)} of the ${thousands(evaluated)} transactions on it that this Signal evaluated`;
  }
  let text =
    `The Clerk's index dates this report ${filedAt}, which is later than the deadline the rule ` +
    `sets for ${which}, by ${span}. The deadline is the earlier of 30 days after the notification ` +
    `date the report prints and 45 days after the transaction date (${CITATION}).`;
  const unusable = after.filter((r) => r.notification !== "applied").length;
  if (unusable) {
    text +=
      ` For ${those(unusable, k)} the report prints no usable notification date, so the ` +
      "deadline is 45 days after the transaction.";
  }
  const lateNotice = after.filter((r) => r.notified_after_limit).length;
  if (lateNotice) {
    text +=
      ` For ${those(lateNotice, k)} the report prints a notification date later than 45 days ` +
      "after the transaction, so the deadline had passed before that notification.";
  }
  const weekends = after.filter((r) => r.weekend !== null).length;
  if (weekends) {
    text +=
      ` For ${those(weekends, k)} the deadline fell on a weekend; the House Committee on Ethics ` +
      "states that the date does not move to the next business day.";
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
