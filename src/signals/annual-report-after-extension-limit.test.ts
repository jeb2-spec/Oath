/**
 * The reference implementation against the known-answer cases, and against the register.
 *
 * RUBRIC.md gate 4: given the Signal's version and the filing a Finding names, the reference
 * implementation regenerates the Finding byte-identically. Tested against the hand-worked cases
 * in fixtures/annual-report-after-extension-limit/cases.json, and, once the Signal's definition
 * is in docs/signals/ and the runner has sealed its record, against every Finding and every
 * report outcome the Python implementation wrote, compared as canonical JSON after setting aside
 * the two fields only a build can give a Finding, fired_at and build_hash. Before the definition
 * lands, the register must hold nothing for it.
 */

import { existsSync, readFileSync } from "node:fs";
import { expect, describe as group, test } from "vitest";
import {
  evaluate,
  type Filing,
  FRAME,
  type Holder,
  readDate,
  SIGNAL_ID,
  SLUG,
  VERSION,
} from "./annual-report-after-extension-limit";

const root = new URL("../../", import.meta.url);
const text = (path: string) => readFileSync(new URL(path, root), "utf8");
const exists = (path: string) => existsSync(new URL(path, root));
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
  officeholder: Holder;
  report: Filing;
  expect: {
    in_scope: boolean;
    fires?: boolean;
    compared?: boolean;
    reason?: string | null;
    due?: string;
    latest?: string;
    days_after_latest?: number;
    days_after_due?: number;
    description?: string;
  };
}

const cases: Case[] = JSON.parse(text(`fixtures/${SLUG}/cases.json`)).cases;

group("the known-answer cases", () => {
  test.each(cases.map((c) => [c.name, c] as const))("%s", (_name, c) => {
    const [findings, outcomes] = evaluate([c.officeholder], [c.report]);
    if (!c.expect.in_scope) {
      expect(outcomes).toEqual([]);
      expect(findings).toEqual([]);
      return;
    }
    expect(outcomes).toHaveLength(1);
    const [outcome] = outcomes;
    // Read, with one row, its date, compared or set aside with the reason: the house shape.
    expect([outcome.state, outcome.rows]).toEqual(["evaluated", 1]);
    expect(outcome.evaluated).toBe(c.expect.compared ? 1 : 0);
    expect(outcome.not_evaluated).toEqual(c.expect.reason ? { [c.expect.reason]: 1 } : {});
    expect(findings.length > 0).toBe(c.expect.fires);
    expect(outcome.after).toBe(c.expect.fires ? 1 : 0);
    if (!c.expect.fires) return;
    const [found] = findings;
    expect(found.id).toBe(outcome.finding_id);
    expect(found.producing_filings).toEqual([c.report.id]);
    expect(found.evidence).toMatchObject({
      due: c.expect.due,
      latest: c.expect.latest,
      days_after_latest: c.expect.days_after_latest,
      days_after_due: c.expect.days_after_due,
    });
    if (c.expect.description) expect(found.description).toBe(c.expect.description);
    expect(found.frame).toBe(FRAME);
  });

  test("only real dates written YYYY-MM-DD are read", () => {
    expect(readDate("2024-02-29")).not.toBeNull();
    for (const value of ["2025-02-29", "2025-02-30", "05/15/2025", "20250515", "", null, 2025]) {
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

/** Where the computed Findings and the sealed ledger disagree, one line each; empty when none.
 * A chain of corrections is compared at its head, apart from the head's own id and notes, and a
 * head recording that the Signal no longer fires is matched by the implementation's silence. */
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
      row.id === id
        ? ["fired_at", "build_hash"]
        : ["fired_at", "build_hash", "id", "notes", "correction"];
    if (canonical(omit(found, drop)) !== canonical(omit(row, drop))) out.push(`${id}: differs`);
  }
  return out;
}

group("the register", () => {
  const holders = ndjson("data/officeholders.ndjson") as unknown as Holder[];
  const filings = ndjson("data/filings.ndjson") as unknown as Filing[];
  const [findings, outcomes] = evaluate(holders, filings);
  const sealed = ndjson("data/findings.ndjson").filter((r) => r.signal_id === SIGNAL_ID);
  const record = `data/signal-runs/${SLUG}-v${VERSION}.ndjson`;
  const defined = exists(`docs/signals/${SLUG}.md`);

  test.runIf(!defined)("before its definition lands, the register holds nothing for it", () => {
    expect(sealed).toEqual([]);
    expect(exists(record)).toBe(false);
  });

  test.runIf(defined)("every Finding the Python sealed, the reference regenerates", () => {
    expect(disagreements(findings as unknown as Record<string, unknown>[], sealed)).toEqual([]);
  });

  test.runIf(defined)("every report outcome the run recorded, the reference regenerates", () => {
    const [summary, ...recorded] = ndjson(record);
    expect(outcomes.map(canonical)).toEqual(recorded.map(canonical));
    expect(summary.reports).toBe(outcomes.length);
  });
});
