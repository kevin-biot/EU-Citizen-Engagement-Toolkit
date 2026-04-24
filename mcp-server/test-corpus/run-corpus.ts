import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

type CorpusCase = {
  id: string;
  family?: string;
  priority?: string;
  risk_level?: string;
  tool: string;
  title: string;
  input: Record<string, unknown>;
  expected: Record<string, unknown>;
  notes?: string;
};

type CorpusFile = {
  version: number;
  updated_at: string;
  cases: CorpusCase[];
};

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const corpusPath = path.join(__dirname, "canonical-tool-queries.json");
const mcpRoot = path.resolve(__dirname, "..");
const serverEntry = path.join(mcpRoot, "dist", "index.js");

function loadCorpus() {
  return JSON.parse(readFileSync(corpusPath, "utf8")) as CorpusFile;
}

function textPayloadFromToolResult(result: { content?: Array<{ type: string; text?: string }> }) {
  const textItem = result.content?.find((item) => item.type === "text" && typeof item.text === "string");
  if (!textItem?.text) {
    throw new Error("Tool result did not contain a text payload");
  }
  return JSON.parse(textItem.text) as Record<string, unknown>;
}

function asRecord(value: unknown) {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : null;
}

function asArray(value: unknown) {
  return Array.isArray(value) ? value : [];
}

function getTopMatch(payload: Record<string, unknown>) {
  const matches = asArray(payload.matches);
  return asRecord(matches[0]);
}

function getTopMatchRow(payload: Record<string, unknown>) {
  return asRecord(getTopMatch(payload)?.row);
}

function getRecommendation(payload: Record<string, unknown>) {
  return asRecord(payload.recommendation);
}

function getRecommendationPrimaryTemplateSlug(payload: Record<string, unknown>) {
  return asRecord(getRecommendation(payload)?.primary_template)?.template_slug;
}

function getUseCases(payload: Record<string, unknown>) {
  return asArray(payload.use_cases);
}

function getFirstUseCase(payload: Record<string, unknown>) {
  return asRecord(getUseCases(payload)[0]);
}

function getRecommendations(payload: Record<string, unknown>, key = "recommendations") {
  return asArray(payload[key]);
}

function getContacts(payload: Record<string, unknown>) {
  return asArray(payload.contacts);
}

function getFirstContact(payload: Record<string, unknown>) {
  return asRecord(getContacts(payload)[0]);
}

function getStages(payload: Record<string, unknown>) {
  return asArray(payload.stages);
}

function getFirstStage(payload: Record<string, unknown>) {
  return asRecord(getStages(payload)[0]);
}

function getCurrentStage(payload: Record<string, unknown>) {
  return asRecord(payload.current_stage ?? payload.assessed_stage);
}

function collectTemplateSlugs(entries: unknown[]) {
  const slugs: string[] = [];
  for (const entry of entries) {
    const record = asRecord(entry);
    const template = asRecord(record?.recommended_template);
    const slug = template?.template_slug;
    if (typeof slug === "string") {
      slugs.push(slug);
    }
  }
  return slugs;
}

function assertCase(testCase: CorpusCase, payload: Record<string, unknown>) {
  const failures: string[] = [];
  const expected = testCase.expected;

  for (const [key, value] of Object.entries(expected)) {
    switch (key) {
      case "confidence_band":
      case "suggested_action":
        if (payload[key] !== value) {
          failures.push(`expected ${key}=${String(value)}, got ${String(payload[key])}`);
        }
        break;
      case "authority_rows_min": {
        const count = asArray(payload.authority_rows).length;
        if (count < Number(value)) {
          failures.push(`expected authority_rows >= ${value}, got ${count}`);
        }
        break;
      }
      case "country_matches_found_min": {
        const found = Number(payload.country_matches_found ?? 0);
        if (found < Number(value)) {
          failures.push(`expected country_matches_found >= ${value}, got ${found}`);
        }
        break;
      }
      case "matches_count_max": {
        const count = asArray(payload.matches).length;
        if (count > Number(value)) {
          failures.push(`expected matches <= ${value}, got ${count}`);
        }
        break;
      }
      case "matched_use_cases_min": {
        const count = Number(payload.matched_use_cases ?? 0);
        if (count < Number(value)) {
          failures.push(`expected matched_use_cases >= ${value}, got ${count}`);
        }
        break;
      }
      case "contacts_min": {
        const count = getContacts(payload).length;
        if (count < Number(value)) {
          failures.push(`expected contacts >= ${value}, got ${count}`);
        }
        break;
      }
      case "stages_min": {
        const count = getStages(payload).length;
        if (count < Number(value)) {
          failures.push(`expected stages >= ${value}, got ${count}`);
        }
        break;
      }
      case "first_use_case_key": {
        const actual = getFirstUseCase(payload)?.use_case_key;
        if (actual !== value) {
          failures.push(`expected first use_case_key=${String(value)}, got ${String(actual)}`);
        }
        break;
      }
      case "first_stage_key_any_of": {
        const actual = getFirstStage(payload)?.stage_key;
        const allowed = value as string[];
        if (!allowed.includes(String(actual))) {
          failures.push(`expected first stage key in [${allowed.join(", ")}], got ${String(actual)}`);
        }
        break;
      }
      case "primary_template_slug": {
        const actual = asRecord(getFirstUseCase(payload)?.primary_template)?.template_slug;
        if (actual !== value) {
          failures.push(`expected first primary template slug=${String(value)}, got ${String(actual)}`);
        }
        break;
      }
      case "bundle_label": {
        const actual = String(payload.bundle_label ?? "").toLowerCase();
        const expectedLabel = String(value).toLowerCase();
        if (actual !== expectedLabel) {
          failures.push(`expected bundle_label=${String(value)}, got ${String(payload.bundle_label)}`);
        }
        break;
      }
      case "recommended_template_slug": {
        const actual = getRecommendationPrimaryTemplateSlug(payload);
        if (actual !== value) {
          failures.push(`expected recommendation primary template slug=${String(value)}, got ${String(actual)}`);
        }
        break;
      }
      case "current_stage_key": {
        const actual = getCurrentStage(payload)?.stage_key;
        if (actual !== value) {
          failures.push(`expected current_stage_key=${String(value)}, got ${String(actual)}`);
        }
        break;
      }
      case "top_result_contact_index_any_of": {
        const actual = getTopMatchRow(payload)?.__contact_index;
        const allowed = value as string[];
        if (!allowed.includes(String(actual))) {
          failures.push(`expected top result contact index in [${allowed.join(", ")}], got ${String(actual)}`);
        }
        break;
      }
      case "top_result_organization_any_of": {
        const actual = getTopMatchRow(payload)?.organization;
        const allowed = value as string[];
        if (!allowed.includes(String(actual))) {
          failures.push(`expected top result organization in [${allowed.join(", ")}], got ${String(actual)}`);
        }
        break;
      }
      case "first_contact_organization_any_of": {
        const actual = getFirstContact(payload)?.organization;
        const allowed = value as string[];
        if (!allowed.includes(String(actual))) {
          failures.push(`expected first contact organization in [${allowed.join(", ")}], got ${String(actual)}`);
        }
        break;
      }
      case "recommendation_template_slug_any_of": {
        const actual = collectTemplateSlugs(getRecommendations(payload, "recommendations"));
        const allowed = value as string[];
        if (!actual.some((slug) => allowed.includes(slug))) {
          failures.push(`expected one recommendation template in [${allowed.join(", ")}], got [${actual.join(", ")}]`);
        }
        break;
      }
      case "escalation_option_template_slug_any_of": {
        const actual = collectTemplateSlugs(getRecommendations(payload, "escalation_options"));
        const allowed = value as string[];
        if (!actual.some((slug) => allowed.includes(slug))) {
          failures.push(`expected one escalation template in [${allowed.join(", ")}], got [${actual.join(", ")}]`);
        }
        break;
      }
      default:
        failures.push(`unsupported assertion key: ${key}`);
        break;
    }
  }

  return failures;
}

async function main() {
  const corpus = loadCorpus();
  const requestedIds = new Set(process.argv.slice(2));
  const cases =
    requestedIds.size > 0
      ? corpus.cases.filter((item) => requestedIds.has(item.id))
      : corpus.cases;

  if (cases.length === 0) {
    throw new Error("No matching corpus cases selected");
  }

  const client = new Client({
    name: "eu-citizen-engagement-toolkit-corpus-runner",
    version: "0.1.0",
  });

  const transport = new StdioClientTransport({
    command: "node",
    args: [serverEntry],
    cwd: mcpRoot,
    stderr: "pipe",
  });

  transport.stderr?.on("data", (chunk) => {
    const text = chunk.toString().trim();
    if (text) {
      process.stderr.write(`[mcp-server] ${text}\n`);
    }
  });

  await client.connect(transport);

  let passed = 0;
  const failures: Array<{ id: string; title: string; failures: string[] }> = [];
  const countsByTool = new Map<string, { passed: number; failed: number }>();
  const countsByFamily = new Map<string, { passed: number; failed: number }>();

  const incrementCounter = (
    map: Map<string, { passed: number; failed: number }>,
    key: string,
    outcome: "passed" | "failed",
  ) => {
    const current = map.get(key) ?? { passed: 0, failed: 0 };
    current[outcome] += 1;
    map.set(key, current);
  };

  try {
    for (const testCase of cases) {
      const result = await client.callTool({
        name: testCase.tool,
        arguments: testCase.input,
      });
      const payload = textPayloadFromToolResult(result);
      const caseFailures = assertCase(testCase, payload);

      if (caseFailures.length === 0) {
        passed += 1;
        incrementCounter(countsByTool, testCase.tool, "passed");
        incrementCounter(countsByFamily, testCase.family ?? "unclassified", "passed");
        console.log(`PASS ${testCase.id} - ${testCase.title}`);
      } else {
        incrementCounter(countsByTool, testCase.tool, "failed");
        incrementCounter(countsByFamily, testCase.family ?? "unclassified", "failed");
        failures.push({
          id: testCase.id,
          title: testCase.title,
          failures: caseFailures,
        });
        console.log(`FAIL ${testCase.id} - ${testCase.title}`);
        for (const failure of caseFailures) {
          console.log(`  - ${failure}`);
        }
      }
    }
  } finally {
    await transport.close();
  }

  console.log(`\nSummary: ${passed}/${cases.length} passed`);
  console.log("\nBy tool:");
  for (const [tool, counts] of [...countsByTool.entries()].sort((a, b) =>
    a[0].localeCompare(b[0]),
  )) {
    console.log(`- ${tool}: ${counts.passed} passed, ${counts.failed} failed`);
  }

  console.log("\nBy family:");
  for (const [family, counts] of [...countsByFamily.entries()].sort((a, b) =>
    a[0].localeCompare(b[0]),
  )) {
    console.log(`- ${family}: ${counts.passed} passed, ${counts.failed} failed`);
  }

  if (failures.length > 0) {
    console.log("\nFailed case ids:");
    for (const failure of failures) {
      console.log(`- ${failure.id}`);
    }
    process.exitCode = 1;
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
