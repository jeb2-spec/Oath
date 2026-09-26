/**
 * The reference implementation against the known-answer cases, and against the register.
 *
 * RUBRIC.md gate 4: given the Signal's version and the filings a Finding names, the reference
 * implementation regenerates the Finding byte-identically. Here that is tested twice: against
 * the hand-worked cases in fixtures/stock-act-late-ptr/cases.json, and against every Finding
 * and every report outcome the Python implementation sealed into data/, compared as canonical
 * JSON (keys sorted, no spaces) after setting aside the two fields only a build can give a
 * Finding, fired_at and build_hash. A chain of corrections is followed to its current row, as
 * the runner follows it (src/signals/run.py): a correction must say what the implementation
 * says, apart from its own id and its notes, and a correction recording that the Signal no
 * longer fires is matched by the implementation's silence.
 */

import { readFileSync } from "node:fs";
import { expect, describe as group, test } from "vitest";
import {
  evaluate,
  evaluateReport,
  type Filing,
  type Holder,
  readDate,
  SIGNAL_ID,
  type Transaction,
} from "./stock-act-late-ptr";

const root = new URL("../../", import.meta.url);
const text = (path: string) => readFileSync(new URL(path, root), "utf8");
const ndjson = (path: string): Record<string, unknown>[] =>
  text(path)
    .split("\n")
    .filter((line) => line.trim())
    .map((line) => JSON.parse(line));

/** The serialisation the Python writer uses: keys sorted, separators without spaces. */
function canonical(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (value && typeof value === "object") {
    const entries = Object.keys(value as object)
      .sort()
      .map((k) => `${JSON.stringify(k)}:${canonical((value as Record<string, unknown>)[k])}`);
    return `{${entries.join(",")}}`;
  }
  return JSON.stringify(value);
}

interface Case {
  name: string;
  officeholder: { id: string; sworn_at: string | null };
  report: { id: string; filed_at: string | null; read: boolean };
  rows: {
    id: string;
    transaction_date: string;
    notified_date: string | null;
    filing_status: string | null;
    expect: Record<string, unknown>;
  }[];
  expect: {
    fires: boolean;
    state?: string;
    evaluated: number;
    after?: string[];
    not_evaluated?: Record<string, number>;
    description?: string;
  };
}

const cases: Case[] = JSON.parse(text("fixtures/stock-act-late-ptr/cases.json")).cases;

function rowsOf(c: Case): { holders: Holder[]; filings: Filing[]; transactions: Transaction[] } {
  return {
    holders: [{ id: c.officeholder.id, sworn_at: c.officeholder.sworn_at }],
    filings: [
      {
        id: c.report.id,
        officeholder_id: c.officeholder.id,
        form_type: "House-PTR",
        filed_at: c.report.filed_at,
        extraction_confidence: c.report.read ? "structured" : null,
      },
    ],
    transactions: c.rows.map((r) => ({
      id: r.id,
      filing_id: c.report.id,
      transaction_date: r.transaction_date,
      notified_date: r.notified_date,
      filing_status: r.filing_status,
    })),
  };
}

group("the known-answer cases", () => {
  test.each(cases.map((c) => [c.name, c] as const))("%s", (_name, c) => {
    const { holders, filings, transactions } = rowsOf(c);
    const result = evaluateReport(filings[0], transactions, readDate(holders[0].sworn_at));
    for (const row of c.rows) expect(result.results[row.id]).toEqual(row.expect);

    const { findings, outcomes } = evaluate(holders, filings, transactions);
    expect(findings.length > 0).toBe(c.expect.fires);
    expect(outcomes[0].evaluated).toBe(c.expect.evaluated);
    if (c.expect.state) expect(outcomes[0].state).toBe(c.expect.state);
    if (c.expect.not_evaluated) expect(outcomes[0].not_evaluated).toEqual(c.expect.not_evaluated);
    if (c.expect.fires) {
      expect(findings[0].producing_rows.map((r) => r.id)).toEqual(c.expect.after);
      if (c.expect.description) expect(findings[0].description).toBe(c.expect.description);
    }
  });

  test("only real dates written YYYY-MM-DD are read", () => {
    expect(readDate("2024-02-29")).not.toBeNull();
    for (const value of [
      "2025-02-29",
      "2025-02-30",
      "05/15/2025",
      "20250515",
      "0000-01-01",
      "",
      null,
      20250515,
    ]) {
      expect(readDate(value)).toBeNull();
    }
  });
});

const CORRECTION = /:c\d+$/;

/** A ledger row that records a firing; a withdrawal carries evidence with no row after. */
function recordsAFiring(row: Record<string, unknown>): boolean {
  const after = ((row.evidence ?? {}) as Record<string, unknown>).after;
  return after === undefined ? true : Boolean(after);
}

function omit(row: Record<string, unknown>, keys: string[]): Record<string, unknown> {
  return Object.fromEntries(Object.entries(row).filter(([k]) => !keys.includes(k)));
}

/** Where the computed Findings and the sealed ledger disagree, one line each; empty when none. */
function disagreements(
  computed: Record<string, unknown>[],
  ledger: Record<string, unknown>[],
): string[] {
  const heads = new Map<string, Record<string, unknown>>();
  for (const row of ledger) {
    if (row.superseded_by === null && recordsAFiring(row)) {
      heads.set(String(row.id).replace(CORRECTION, ""), row);
    }
  }
  const out: string[] = [];
  const made = new Set(computed.map((f) => String(f.id)));
  for (const base of heads.keys()) if (!made.has(base)) out.push(`${base}: sealed, not produced`);
  for (const found of computed) {
    const id = String(found.id);
    const row = heads.get(id);
    if (!row) {
      out.push(`${id}: produced, not sealed`);
      continue;
    }
    const drop =
      row.id === id ? ["fired_at", "build_hash"] : ["fired_at", "build_hash", "id", "notes"];
    if (canonical(omit(found, drop)) !== canonical(omit(row, drop))) out.push(`${id}: differs`);
  }
  return out;
}

group("the ledger comparison", () => {
  const found = {
    id: "fn:x:1",
    description: "d",
    evidence: { after: 1 },
    superseded_by: null,
    notes: null,
  };
  const sealed = { ...found, fired_at: "t", build_hash: "h" };

  test("a plain Finding agrees with its sealed row and nothing else", () => {
    expect(disagreements([found], [sealed])).toEqual([]);
    expect(disagreements([{ ...found, description: "e" }], [sealed])).toEqual(["fn:x:1: differs"]);
    expect(disagreements([], [sealed])).toEqual(["fn:x:1: sealed, not produced"]);
    expect(disagreements([found], [])).toEqual(["fn:x:1: produced, not sealed"]);
  });

  test("a correction is compared at the head of its chain, apart from its id and notes", () => {
    const old = { ...sealed, description: "first", superseded_by: "fn:x:1:c1" };
    const head = { ...sealed, id: "fn:x:1:c1", notes: "why it changed" };
    expect(disagreements([found], [old, head])).toEqual([]);
    expect(disagreements([{ ...found, notes: "x" }], [sealed])).toEqual(["fn:x:1: differs"]);
  });

  test("a correction recording the Signal no longer fires is matched by silence", () => {
    const old = { ...sealed, superseded_by: "fn:x:1:c1" };
    const withdrawn = { ...sealed, id: "fn:x:1:c1", evidence: { after: 0 }, notes: "why" };
    expect(disagreements([], [old, withdrawn])).toEqual([]);
    expect(disagreements([found], [old, withdrawn])).toEqual(["fn:x:1: produced, not sealed"]);
  });
});

group("the register", () => {
  const holders = ndjson("data/officeholders.ndjson") as unknown as Holder[];
  const filings = ndjson("data/filings.ndjson") as unknown as Filing[];
  const transactions = ndjson("data/transactions.ndjson") as unknown as Transaction[];
  const { findings, outcomes } = evaluate(holders, filings, transactions);
  const sealed = ndjson("data/findings.ndjson").filter((r) => r.signal_id === SIGNAL_ID);

  test("every Finding the Python sealed, the reference regenerates byte-identically", () => {
    expect(sealed.length).toBeGreaterThan(0);
    expect(disagreements(findings as unknown as Record<string, unknown>[], sealed)).toEqual([]);
  });

  test("every report outcome the run recorded, the reference regenerates byte-identically", () => {
    const [summary, ...recorded] = ndjson("data/signal-runs/stock-act-late-ptr-v1.ndjson");
    expect(outcomes.map(canonical)).toEqual(recorded.map(canonical));
    expect(summary.reports_with_a_finding).toBe(findings.length);
    expect(summary.reports).toBe(outcomes.length);
  });
});
