import path from "node:path";
import { fileURLToPath } from "node:url";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import {
  buildCatalog,
  getDatasetBySlug,
  getItemBySlug,
  readCsvFile,
  type DatasetSummary,
  type RepoItem,
} from "./catalog.js";
import { filterAuthorities, findRelevantContacts, rankIssueMatches } from "./routing.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot =
  process.env.EU_TOOLKIT_ROOT ?? path.resolve(__dirname, "..", "..");

const catalog = buildCatalog(repoRoot);

function shortItem(item: RepoItem) {
  return {
    slug: item.slug,
    title: item.title,
    summary: item.summary,
    path: item.path,
  };
}

function shortDataset(dataset: DatasetSummary) {
  return {
    slug: dataset.slug,
    title: dataset.title,
    rows: dataset.rows,
    columns: dataset.columns,
    path: dataset.path,
  };
}

function jsonResult(payload: unknown) {
  return {
    content: [
      {
        type: "text" as const,
        text: JSON.stringify(payload, null, 2),
      },
    ],
  };
}

function notFound(kind: string, slug: string) {
  return jsonResult({
    ok: false,
    error: `${kind} not found`,
    slug,
  });
}

const server = new McpServer({
  name: "eu-citizen-engagement-toolkit",
  version: "0.1.0",
});

server.tool(
  "list_playbooks",
  "List citizen digital-issue playbooks available in the toolkit.",
  {},
  async () =>
    jsonResult({
      ok: true,
      repo_root: repoRoot,
      playbooks: catalog.playbooks.map(shortItem),
    }),
);

server.tool(
  "get_playbook",
  "Return one digital-issue playbook by slug.",
  {
    slug: z.string().describe("Playbook slug, for example gdpr-data-rights"),
  },
  async ({ slug }) => {
    const item = getItemBySlug(catalog.playbooks, slug);
    return item
      ? jsonResult({ ok: true, item })
      : notFound("playbook", slug);
  },
);

server.tool(
  "list_templates",
  "List the current filing and correspondence templates exposed by the toolkit.",
  {},
  async () =>
    jsonResult({
      ok: true,
      templates: catalog.templates.map(shortItem),
    }),
);

server.tool(
  "get_template",
  "Return one filing or correspondence template by slug.",
  {
    slug: z
      .string()
      .describe("Template slug, for example foi-request-template"),
  },
  async ({ slug }) => {
    const item = getItemBySlug(catalog.templates, slug);
    return item
      ? jsonResult({ ok: true, item })
      : notFound("template", slug);
  },
);

server.tool(
  "list_email_templates",
  "List starter email templates linked from the digital-issue playbooks.",
  {},
  async () =>
    jsonResult({
      ok: true,
      email_templates: catalog.emailTemplates.map(shortItem),
    }),
);

server.tool(
  "get_email_template",
  "Return one starter email template by slug.",
  {
    slug: z
      .string()
      .describe("Email template slug, for example gdpr-data-rights-email"),
  },
  async ({ slug }) => {
    const item = getItemBySlug(catalog.emailTemplates, slug);
    return item
      ? jsonResult({ ok: true, item })
      : notFound("email template", slug);
  },
);

server.tool(
  "list_datasets",
  "List structured CSV datasets exposed by the toolkit.",
  {},
  async () =>
    jsonResult({
      ok: true,
      datasets: catalog.datasets.map(shortDataset),
    }),
);

server.tool(
  "get_dataset",
  "Return a dataset summary with columns, row count, sample rows, and source path.",
  {
    slug: z
      .string()
      .describe("Dataset slug, for example national-digital-authorities"),
  },
  async ({ slug }) => {
    const dataset = getDatasetBySlug(catalog.datasets, slug);
    return dataset
      ? jsonResult({ ok: true, dataset })
      : notFound("dataset", slug);
  },
);

server.tool(
  "query_dataset",
  "Query a structured CSV dataset by slug with simple equals or contains filters.",
  {
    slug: z
      .string()
      .describe("Dataset slug, for example complete_mep_database_topics"),
    filters: z
      .array(
        z.object({
          column: z.string().describe("Dataset column name"),
          equals: z.string().optional().describe("Exact case-insensitive match"),
          contains: z
            .string()
            .optional()
            .describe("Case-insensitive substring match"),
        }),
      )
      .optional()
      .describe("Optional list of filters combined with AND logic"),
    limit: z
      .number()
      .int()
      .min(1)
      .max(200)
      .optional()
      .describe("Maximum number of rows to return, default 50"),
  },
  async ({ slug, filters = [], limit = 50 }) => {
    const dataset = getDatasetBySlug(catalog.datasets, slug);
    if (!dataset) {
      return notFound("dataset", slug);
    }

    const rows = readCsvFile(dataset.path);
    const matchedRows = rows.filter((row) =>
      filters.every((filter) => {
        const value = (row[filter.column] ?? "").toLowerCase();
        if (filter.equals !== undefined) {
          return value === filter.equals.toLowerCase();
        }
        if (filter.contains !== undefined) {
          return value.includes(filter.contains.toLowerCase());
        }
        return true;
      }),
    );

    return jsonResult({
      ok: true,
      dataset: shortDataset(dataset),
      filters,
      matched_rows: matchedRows.length,
      returned_rows: Math.min(limit, matchedRows.length),
      rows: matchedRows.slice(0, limit),
    });
  },
);

server.tool(
  "route_issue",
  "Suggest the closest issue-router entries and playbooks for a short problem description.",
  {
    problem_description: z
      .string()
      .describe("Short natural-language description of the user's problem"),
  },
  async ({ problem_description }) => {
    const matches = rankIssueMatches(catalog, problem_description);
    return jsonResult({
      ok: true,
      problem_description,
      route_matches: matches.routeMatches.map(({ route, score }) => ({
        score,
        ...route,
      })),
      playbook_matches: matches.playbookMatches.map(({ playbook, score }) => ({
        score,
        ...shortItem(playbook),
      })),
    });
  },
);

server.tool(
  "find_contacts",
  "Search public contact datasets for routes relevant to a topic, audience, or country.",
  {
    topic: z.string().describe("Topic or issue, for example AI accountability"),
    audience: z
      .string()
      .optional()
      .describe("Optional audience such as citizens, journalists, or civil society"),
    country: z
      .string()
      .optional()
      .describe("Optional country filter such as France or Poland"),
  },
  async ({ topic, audience, country }) => {
    const result = findRelevantContacts(catalog, topic, audience, country);
    return jsonResult({
      ok: true,
      topic,
      audience,
      country,
      country_filter_mode: country ? "soft_hint_with_diagnostics" : "none",
      country_matches_found: result.countryMatchesFound,
      fallback_strategy: result.fallbackStrategy,
      matches: result.matches.map(({ score, row }) => ({
        score,
        row,
      })),
    });
  },
);

server.tool(
  "get_authorities",
  "Return national digital authority summary data for a country, with optional issue context.",
  {
    country: z.string().describe("Country name as listed in the authority dataset"),
    issue_type: z
      .string()
      .optional()
      .describe("Optional issue label for context, for example dark patterns"),
  },
  async ({ country, issue_type }) =>
    jsonResult({
      ok: true,
      country,
      issue_type,
      authority_rows: filterAuthorities(catalog, country, issue_type),
    }),
);

server.tool(
  "build_draft_packet",
  "Assemble the most relevant local drafting context for a chosen template and user facts. The MCP client model should write the final draft.",
  {
    template_slug: z
      .string()
      .describe("Template slug, for example foi-request-template"),
    user_facts: z
      .string()
      .describe("Short factual summary from the user that should shape the draft"),
    issue_slug: z
      .string()
      .optional()
      .describe("Optional related playbook slug to include alongside the template"),
  },
  async ({ template_slug, user_facts, issue_slug }) => {
    const template = getItemBySlug(catalog.templates, template_slug);
    if (!template) {
      return notFound("template", template_slug);
    }

    const playbook = issue_slug ? getItemBySlug(catalog.playbooks, issue_slug) : undefined;
    return jsonResult({
      ok: true,
      user_facts,
      template: shortItem(template),
      related_playbook: playbook ? shortItem(playbook) : null,
      guidance: [
        "Use the template structure and preserve legal/procedural caveats.",
        "Ground the draft in the user facts and avoid inventing dates, references, or legal claims.",
        "Use the local file paths in this packet for analysis and provenance only, not in the final outward-facing draft.",
      ],
      packet: {
        template_body: template.body,
        playbook_body: playbook?.body ?? null,
      },
    });
  },
);

const transport = new StdioServerTransport();
await server.connect(transport);
