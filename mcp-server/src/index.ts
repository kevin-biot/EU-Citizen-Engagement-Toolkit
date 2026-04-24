import path from "node:path";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import {
  buildCatalog,
  getDatasetBySlug,
  getItemBySlug,
  readCsvFile,
  type BundleRow,
  type CampaignRuleRow,
  type CampaignStageRow,
  type DatasetSummary,
  type RepoItem,
  type TemplateRegistryRow,
  type TemplateSelectorRow,
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

type ResolvedTemplate = {
  template_slug: string;
  title: string;
  template_family: string;
  template_kind: string;
  primary_target: string;
  jurisdiction_scope: string;
  stage: string;
  tone: string;
  requires_evidence: string;
  best_when: string;
  not_for: string;
  source_path: string;
  mcp_slug: string;
  summary: string;
  body: string;
};

function firstParagraph(text: string) {
  const normalized = text.replace(/\r/g, "");
  const withoutHeading = normalized.replace(/^#.*$/m, "").trim();
  const blocks = withoutHeading
    .split(/\n\s*\n/)
    .map((block) => block.trim().replace(/\n+/g, " "))
    .filter(Boolean);
  return blocks[0] ?? "";
}

function normalizeSelectorValue(value: string) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

function normalizeSearchText(value: string) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9\s]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function slugFromSourcePath(sourcePath: string) {
  return path.basename(sourcePath, path.extname(sourcePath));
}

function scopeMatches(requestedScope?: string, actualScope?: string) {
  if (!requestedScope?.trim() || !actualScope?.trim()) {
    return true;
  }

  const requested = normalizeSearchText(requestedScope);
  const actual = normalizeSearchText(actualScope);
  if (requested === actual) {
    return true;
  }

  if (actual.includes(requested) || requested.includes(actual)) {
    return true;
  }

  const compatibility: Record<string, string[]> = {
    eu: ["eu", "mixed", "eu_or_national", "national_or_cross_border", "eu_cross_border"],
    national: ["national", "mixed", "eu_or_national", "national_or_cross_border"],
    cross_border: ["mixed", "eu_cross_border", "national_or_cross_border", "eu_or_national"],
    mixed: ["mixed", "eu_or_national", "national_or_cross_border", "eu_cross_border"],
  };

  return (compatibility[requested] ?? []).includes(actual);
}

function selectorScore(
  row: TemplateSelectorRow,
  query: string,
  jurisdictionScope?: string,
  targetType?: string,
  stage?: string,
) {
  const normalizedQuery = normalizeSearchText(query);
  const key = normalizeSelectorValue(row.use_case_key ?? "");
  const label = normalizeSearchText(row.use_case_label ?? "");
  const note = normalizeSearchText(row.selector_note ?? "");
  let score = 0;

  if (normalizeSelectorValue(query) === key) {
    score += 14;
  }
  if (label === normalizedQuery) {
    score += 12;
  }
  if (label.includes(normalizedQuery) && normalizedQuery) {
    score += 8;
  }
  if (note.includes(normalizedQuery) && normalizedQuery) {
    score += 4;
  }

  for (const token of tokenizeText(query)) {
    if (token.length < 3) {
      continue;
    }
    if (key.includes(token)) {
      score += 3;
    }
    if (label.includes(token)) {
      score += 2;
    }
    if (note.includes(token)) {
      score += 1;
    }
  }

  if (scopeMatches(jurisdictionScope, row.jurisdiction_scope)) {
    score += jurisdictionScope ? 2 : 0;
  } else if (jurisdictionScope) {
    score -= 2;
  }

  const noteAndLabel = `${label} ${note}`;
  if (targetType?.trim() && noteAndLabel.includes(normalizeSearchText(targetType))) {
    score += 2;
  }
  if (stage?.trim() && noteAndLabel.includes(normalizeSearchText(stage))) {
    score += 1;
  }

  return score;
}

function registryRowForSlug(templateSlug: string) {
  const normalized = normalizeSelectorValue(templateSlug);
  return catalog.templateRegistry.find(
    (row) =>
      normalizeSelectorValue(row.template_slug ?? "") === normalized ||
      normalizeSelectorValue(slugFromSourcePath(row.source_path ?? "")) === normalized,
  );
}

function resolveTemplate(row?: TemplateRegistryRow) {
  if (!row) {
    return null;
  }

  const sourcePath = path.join(repoRoot, row.source_path);
  const body = readFileSync(sourcePath, "utf8");
  return {
    template_slug: row.template_slug,
    title: row.title,
    template_family: row.template_family,
    template_kind: row.template_kind,
    primary_target: row.primary_target,
    jurisdiction_scope: row.jurisdiction_scope,
    stage: row.stage,
    tone: row.tone,
    requires_evidence: row.requires_evidence,
    best_when: row.best_when,
    not_for: row.not_for,
    source_path: sourcePath,
    mcp_slug: slugFromSourcePath(row.source_path),
    summary: firstParagraph(body),
    body,
  } satisfies ResolvedTemplate;
}

function registeredTemplates() {
  return catalog.templateRegistry
    .map((row) => resolveTemplate(row))
    .filter((item): item is ResolvedTemplate => Boolean(item))
    .sort((a, b) => a.title.localeCompare(b.title));
}

function useCaseMatches(row: TemplateSelectorRow, useCase?: string) {
  if (!useCase?.trim()) {
    return true;
  }

  const normalized = normalizeSearchText(useCase);
  const key = normalizeSelectorValue(row.use_case_key ?? "");
  const label = normalizeSearchText(row.use_case_label ?? "");
  return (
    normalizeSelectorValue(useCase) === key ||
    label.includes(normalized) ||
    normalizeSearchText(row.selector_note ?? "").includes(normalized)
  );
}

function selectorEntry(row: TemplateSelectorRow) {
  const primaryTemplate = resolveTemplate(registryRowForSlug(row.primary_template_slug ?? ""));
  const fallbackTemplate = resolveTemplate(
    registryRowForSlug(row.fallback_template_slug ?? ""),
  );

  return {
    use_case_key: row.use_case_key,
    use_case_label: row.use_case_label,
    jurisdiction_scope: row.jurisdiction_scope,
    selector_note: row.selector_note,
    not_for: row.not_for,
    primary_template: primaryTemplate,
    fallback_template: fallbackTemplate,
  };
}

type CampaignSignals = {
  controller_contacted: boolean;
  dpa_complaint_filed: boolean;
  cross_border_dimension: boolean;
  systemic_pattern: boolean;
  regulator_silent: boolean;
  need_public_pressure: boolean;
  want_media_route: boolean;
  want_ngo_support: boolean;
};

function parseSignalList(value: string) {
  return value
    .split(";")
    .map((part) => part.trim())
    .filter(Boolean);
}

function campaignStageRows(campaignSlug: string) {
  return catalog.campaignStages.filter((row) => row.campaign_slug === campaignSlug);
}

function campaignRuleRows(campaignSlug: string) {
  return catalog.campaignRules.filter((row) => row.campaign_slug === campaignSlug);
}

function matchSignals(signals: CampaignSignals, required: string, excluded: string) {
  const requiredSignals = parseSignalList(required);
  const excludedSignals = parseSignalList(excluded);

  return (
    requiredSignals.every((signal) => signals[signal as keyof CampaignSignals]) &&
    excludedSignals.every((signal) => !signals[signal as keyof CampaignSignals])
  );
}

function campaignStageScore(stage: CampaignStageRow, signals: CampaignSignals) {
  const reasons: string[] = [];
  let score = 0;

  switch (stage.stage_key) {
    case "individual_rights_complaint":
      if (!signals.systemic_pattern) {
        score += 3;
        reasons.push("No strong systemic-pattern signal.");
      }
      if (!signals.cross_border_dimension) {
        score += 3;
        reasons.push("No clear cross-border dimension.");
      }
      if (!signals.regulator_silent) {
        score += 2;
      }
      if (!signals.need_public_pressure) {
        score += 2;
      }
      if (!signals.dpa_complaint_filed) {
        score += 1;
      }
      if (signals.regulator_silent) {
        score -= 3;
      }
      break;
    case "systemic_company_abuse":
      if (signals.systemic_pattern) {
        score += 6;
        reasons.push("Repeat-pattern or broader company abuse is indicated.");
      }
      if (signals.want_ngo_support) {
        score += 2;
      }
      if (signals.need_public_pressure) {
        score += 1;
      }
      break;
    case "cross_border_enforcement_pressure":
      if (signals.cross_border_dimension) {
        score += 6;
        reasons.push("Cross-border or lead-authority considerations are present.");
      }
      if (signals.dpa_complaint_filed) {
        score += 2;
      }
      if (signals.want_ngo_support) {
        score += 1;
      }
      break;
    case "regulator_delay_under_enforcement":
      if (signals.regulator_silent) {
        score += 8;
        reasons.push("Regulator silence or under-enforcement is now central.");
      }
      if (signals.dpa_complaint_filed) {
        score += 3;
      }
      if (signals.need_public_pressure) {
        score += 2;
      }
      if (signals.want_media_route) {
        score += 1;
      }
      break;
    default:
      break;
  }

  return { score, reasons };
}

function resolveDataset(slug?: string) {
  if (!slug) {
    return null;
  }
  const dataset = getDatasetBySlug(catalog.datasets, slug);
  return dataset ? shortDataset(dataset) : null;
}

function stageEntry(row: CampaignStageRow) {
  return {
    campaign_slug: row.campaign_slug,
    stage_key: row.stage_key,
    stage_label: row.stage_label,
    description: row.description,
    entry_signals: row.entry_signals,
    primary_goal: row.primary_goal,
    preferred_templates: parseSignalList(row.preferred_templates).map((slug) =>
      resolveTemplate(registryRowForSlug(slug)),
    ),
    preferred_routes: parseSignalList(row.preferred_routes),
    exit_signal: row.exit_signal,
    not_for: row.not_for,
  };
}

function assessedCampaignStage(campaignSlug: string, signals: CampaignSignals) {
  const ranked = campaignStageRows(campaignSlug)
    .map((row) => {
      const scored = campaignStageScore(row, signals);
      return {
        row,
        score: scored.score,
        reasons: scored.reasons,
      };
    })
    .sort((a, b) => {
      if (a.score !== b.score) {
        return b.score - a.score;
      }
      return a.row.stage_label.localeCompare(b.row.stage_label);
    });

  return {
    best: ranked[0] ?? null,
    ranked,
  };
}

function ruleEntry(rule: CampaignRuleRow) {
  return {
    campaign_slug: rule.campaign_slug,
    rule_key: rule.rule_key,
    stage_key: rule.stage_key,
    recommended_next_step: rule.recommended_next_step,
    recommended_template: resolveTemplate(
      registryRowForSlug(rule.recommended_template_slug ?? ""),
    ),
    recommended_bundle_slug: rule.recommended_bundle_slug || null,
    recommended_dataset: resolveDataset(rule.recommended_dataset_slug || ""),
    recommended_contact_type: rule.recommended_contact_type,
    recommended_stage_after: rule.recommended_stage_after,
    escalation_level: rule.escalation_level,
    note: rule.note,
  };
}

function matchedCampaignRules(
  campaignSlug: string,
  stageKey: string,
  signals: CampaignSignals,
  minimumEscalation?: "low" | "medium" | "high",
) {
  const escalationRank: Record<string, number> = { low: 1, medium: 2, high: 3 };
  const minimumRank = minimumEscalation ? escalationRank[minimumEscalation] : 0;

  return campaignRuleRows(campaignSlug)
    .filter((rule) => rule.stage_key === stageKey)
    .filter((rule) => matchSignals(signals, rule.required_signals ?? "", rule.excluded_signals ?? ""))
    .filter((rule) => (escalationRank[rule.escalation_level] ?? 0) >= minimumRank)
    .map(ruleEntry);
}

type CommissionProjectGroupMember = {
  role: string;
  name: string;
  portfolio: string;
};

type CommissionProjectGroup = {
  group_name: string;
  decision_date: string;
  official_decision_url: string;
  last_verified: string;
  chairs: CommissionProjectGroupMember[];
  members: CommissionProjectGroupMember[];
  member_count: number;
};

function tokenizeText(value: string) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter(Boolean);
}

function normalizeCommissionProjectGroupRow(row: Record<string, string>) {
  let groupName = row.project_group?.trim() ?? "";
  let groupRole = row.group_role?.trim().toLowerCase() ?? "";
  let memberName = row.member_name?.trim() ?? "";
  let memberPortfolio = row.member_portfolio?.trim() ?? "";

  if (!["chair", "member"].includes(groupRole) && ["chair", "member"].includes(memberName.toLowerCase())) {
    groupName = [groupName, row.group_role?.trim()].filter(Boolean).join(", ");
    groupRole = memberName.toLowerCase();
    const splitAt = memberPortfolio.indexOf(", ");
    if (splitAt > 0) {
      memberName = memberPortfolio.slice(0, splitAt).trim();
      memberPortfolio = memberPortfolio.slice(splitAt + 2).trim();
    }
  }

  return {
    group_name: groupName,
    group_role: groupRole,
    member_name: memberName,
    member_portfolio: memberPortfolio,
    decision_date: row.decision_date ?? "",
    official_decision_url: row.official_decision_url ?? "",
    last_verified: row.last_verified ?? "",
  };
}

function loadCommissionProjectGroups() {
  const rows = readCsvFile(
    path.join(repoRoot, "data", "commission-reference", "commission-project-groups.csv"),
  ).map(normalizeCommissionProjectGroupRow);

  const grouped = new Map<string, CommissionProjectGroup>();
  for (const row of rows) {
    if (!row.group_name) {
      continue;
    }
    const group =
      grouped.get(row.group_name) ??
      {
        group_name: row.group_name,
        decision_date: row.decision_date,
        official_decision_url: row.official_decision_url,
        last_verified: row.last_verified,
        chairs: [],
        members: [],
        member_count: 0,
      };

    const member = {
      role: row.group_role,
      name: row.member_name,
      portfolio: row.member_portfolio,
    };
    if (row.group_role === "chair") {
      group.chairs.push(member);
    } else {
      group.members.push(member);
    }
    group.member_count += 1;

    if (!group.decision_date) {
      group.decision_date = row.decision_date;
    }
    if (!group.official_decision_url) {
      group.official_decision_url = row.official_decision_url;
    }
    if (!group.last_verified) {
      group.last_verified = row.last_verified;
    }

    grouped.set(row.group_name, group);
  }

  return [...grouped.values()].sort((a, b) => a.group_name.localeCompare(b.group_name));
}

function rankCommissionProjectGroup(group: CommissionProjectGroup, topic?: string) {
  if (!topic?.trim()) {
    return 0;
  }

  const normalizedTopic = topic.toLowerCase().trim();
  const haystack = [
    group.group_name,
    ...group.chairs.map((chair) => `${chair.name} ${chair.portfolio}`),
    ...group.members.map((member) => `${member.name} ${member.portfolio}`),
  ]
    .join(" ")
    .toLowerCase();

  let score = haystack.includes(normalizedTopic) ? 8 : 0;
  for (const token of tokenizeText(topic)) {
    if (haystack.includes(token)) {
      score += token.length >= 6 ? 2 : 1;
    }
  }
  return score;
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

function normalizeCountry(value: string) {
  const normalized = value
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  const aliases: Record<string, string> = {
    "czech republic": "czechia",
    "united kingdom": "uk",
    "great britain": "uk",
  };
  return aliases[normalized] ?? normalized;
}

function bundleScopeRank(scope: string, country?: string) {
  const normalizedScope = normalizeCountry(scope);
  if (country && normalizedScope === normalizeCountry(country)) {
    return 0;
  }
  if (normalizedScope === "eu level" || normalizedScope === "eu_level") {
    return 1;
  }
  return 2;
}

function issueBundleMetadata(rows: BundleRow[]) {
  const grouped = new Map<
    string,
    { bundle_slug: string; bundle_label: string; org_count: number; scopes: Set<string> }
  >();

  for (const row of rows) {
    const existing =
      grouped.get(row.bundle_slug) ??
      {
        bundle_slug: row.bundle_slug,
        bundle_label: row.bundle_label,
        org_count: 0,
        scopes: new Set<string>(),
      };
    existing.org_count += 1;
    if (row.org_scope) {
      existing.scopes.add(row.org_scope);
    }
    grouped.set(row.bundle_slug, existing);
  }

  return [...grouped.values()]
    .map((item) => ({
      bundle_slug: item.bundle_slug,
      bundle_label: item.bundle_label,
      org_count: item.org_count,
      scopes: [...item.scopes].sort(),
    }))
    .sort((a, b) => a.bundle_label.localeCompare(b.bundle_label));
}

function packetWarnings(templateSlug: string, userFacts: string, issueSlug?: string) {
  const warnings: string[] = [];
  const normalizedFacts = userFacts.toLowerCase();
  const looksNational =
    /\bfrance\b|\bgermany\b|\bitaly\b|\bpoland\b|\bspain\b|\bnetherlands\b|\bbelgium\b|\baustria\b|\bcyprus\b|\bbulgaria\b|\bcroatia\b|\bczechia\b|\bczech republic\b|\bministry\b|\btax administration\b|\bmunicipal\b|\bregional\b|\blocal\b|\bnational\b|gouv\.fr|gov\./.test(
      normalizedFacts,
    );
  const looksEuInstitution =
    /\beuropean commission\b|\beuropean parliament\b|\bcouncil of the european union\b|\beu institution\b|\bdg [a-z]+\b|\bcommissioner\b|\bombudsman eu\b/.test(
      normalizedFacts,
    );

  if (
    templateSlug === "ombudsman-complaint-template" &&
    looksNational &&
    !looksEuInstitution
  ) {
    warnings.push(
      "The selected Ombudsman template targets EU institutions. Your facts look national or local, so a national ombudsman, equality body, accessibility body, or sector regulator is likely the primary route.",
    );
    if (issueSlug === "digital-accessibility-failure") {
      warnings.push(
        "For accessibility failures, start with the service provider's accessibility contact and the relevant national accessibility or equality body before framing an EU-level Ombudsman complaint.",
      );
    }
  }

  return warnings;
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
      templates: registeredTemplates().map((template) => ({
        template_slug: template.template_slug,
        mcp_slug: template.mcp_slug,
        title: template.title,
        template_family: template.template_family,
        template_kind: template.template_kind,
        primary_target: template.primary_target,
        jurisdiction_scope: template.jurisdiction_scope,
        stage: template.stage,
        tone: template.tone,
        source_path: template.source_path,
        summary: template.summary,
      })),
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
    const item = resolveTemplate(registryRowForSlug(slug));
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
  "list_templates_by_use_case",
  "List template recommendations by use case from the metadata-driven selector layer.",
  {
    use_case: z
      .string()
      .optional()
      .describe("Optional use-case key or phrase, for example gdpr_rights_request"),
    jurisdiction_scope: z
      .string()
      .optional()
      .describe("Optional scope such as EU, National, Mixed, or EU_cross_border"),
  },
  async ({ use_case, jurisdiction_scope }) => {
    const rows = catalog.templateSelector
      .filter((row) => useCaseMatches(row, use_case))
      .filter((row) => scopeMatches(jurisdiction_scope, row.jurisdiction_scope))
      .sort((a, b) => a.use_case_label.localeCompare(b.use_case_label));

    return jsonResult({
      ok: true,
      use_case: use_case ?? null,
      jurisdiction_scope: jurisdiction_scope ?? null,
      matched_use_cases: rows.length,
      use_cases: rows.map(selectorEntry),
    });
  },
);

server.tool(
  "recommend_template",
  "Recommend the strongest template match for a use case or short problem description using the template selector metadata.",
  {
    use_case: z
      .string()
      .optional()
      .describe("Short use-case key or label, for example dpa_silence_follow_up"),
    problem_description: z
      .string()
      .optional()
      .describe("Optional natural-language description when you do not know the use-case key"),
    jurisdiction_scope: z
      .string()
      .optional()
      .describe("Optional scope such as EU, National, Mixed, or EU_cross_border"),
    target_type: z
      .string()
      .optional()
      .describe("Optional target hint such as MEP office, journalist, or National DPA"),
    stage: z
      .string()
      .optional()
      .describe("Optional stage hint such as initial_contact, regulator_follow_up, or media_outreach"),
  },
  async ({ use_case, problem_description, jurisdiction_scope, target_type, stage }) => {
    const query = [use_case, problem_description].filter(Boolean).join(" ").trim();
    if (!query) {
      return jsonResult({
        ok: false,
        error: "recommend_template needs use_case or problem_description",
      });
    }

    const ranked = catalog.templateSelector
      .map((row) => ({
        row,
        score: selectorScore(row, query, jurisdiction_scope, target_type, stage),
      }))
      .filter((entry) => entry.score > 0)
      .sort((a, b) => {
        if (a.score !== b.score) {
          return b.score - a.score;
        }
        return a.row.use_case_label.localeCompare(b.row.use_case_label);
      });

    const top = ranked[0];
    const alternatives = ranked.slice(1, 4).map(({ row, score }) => ({
      score,
      ...selectorEntry(row),
    }));

    return top
      ? jsonResult({
          ok: true,
          query,
          jurisdiction_scope: jurisdiction_scope ?? null,
          target_type: target_type ?? null,
          stage: stage ?? null,
          recommendation: {
            score: top.score,
            ...selectorEntry(top.row),
          },
          alternatives,
        })
      : jsonResult({
          ok: true,
          query,
          jurisdiction_scope: jurisdiction_scope ?? null,
          target_type: target_type ?? null,
          stage: stage ?? null,
          recommendation: null,
          alternatives: [],
          warning:
            "No template selector row matched strongly enough. Refine the use case or inspect list_templates_by_use_case.",
        });
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
  "list_commission_project_groups",
  "List current European Commission project groups, with optional topic filtering.",
  {
    topic: z
      .string()
      .optional()
      .describe("Optional topic or keyword such as AI, climate, housing, or skills"),
  },
  async ({ topic }) => {
    const groups = loadCommissionProjectGroups()
      .map((group) => ({
        score: rankCommissionProjectGroup(group, topic),
        ...group,
      }))
      .filter((group) => !topic || group.score > 0)
      .sort((a, b) => {
        if (a.score !== b.score) {
          return b.score - a.score;
        }
        return a.group_name.localeCompare(b.group_name);
      });

    return jsonResult({
      ok: true,
      topic: topic ?? null,
      groups_count: groups.length,
      groups: groups.map((group) => ({
        score: group.score,
        group_name: group.group_name,
        chairs: group.chairs,
        member_count: group.member_count,
        decision_date: group.decision_date,
        official_decision_url: group.official_decision_url,
        last_verified: group.last_verified,
      })),
    });
  },
);

server.tool(
  "get_commission_project_group",
  "Return one Commission project group with its chairs, members, and source decision link.",
  {
    group_name: z
      .string()
      .describe("Exact or case-insensitive project-group name, for example Artificial Intelligence"),
  },
  async ({ group_name }) => {
    const group = loadCommissionProjectGroups().find(
      (item) => item.group_name.toLowerCase() === group_name.toLowerCase(),
    );
    return group
      ? jsonResult({ ok: true, group })
      : notFound("Commission project group", group_name);
  },
);

server.tool(
  "list_bundles",
  "List curated issue-specific contact bundles available in the toolkit.",
  {},
  async () =>
    jsonResult({
      ok: true,
      bundles: issueBundleMetadata(catalog.issueBundles),
    }),
);

server.tool(
  "get_bundle",
  "Return one curated issue-specific contact bundle, optionally ordered for a country.",
  {
    slug: z
      .string()
      .describe("Bundle slug, for example privacy_data_protection"),
    country: z
      .string()
      .optional()
      .describe("Optional country to order country-specific rows ahead of EU-level rows"),
  },
  async ({ slug, country }) => {
    const rows = catalog.issueBundles
      .filter((row) => row.bundle_slug === slug)
      .sort((a, b) => {
        const rankDiff = bundleScopeRank(a.org_scope ?? "", country) - bundleScopeRank(b.org_scope ?? "", country);
        if (rankDiff !== 0) {
          return rankDiff;
        }
        return a.organization.localeCompare(b.organization);
      });

    return rows.length > 0
      ? jsonResult({
          ok: true,
          slug,
          country: country ?? null,
          bundle_label: rows[0].bundle_label,
          contacts: rows,
        })
      : notFound("bundle", slug);
  },
);

server.tool(
  "list_campaign_stages",
  "List the configured campaign stages for a campaign selector dataset.",
  {
    campaign_slug: z
      .string()
      .describe("Campaign slug, currently gdpr_complaints"),
  },
  async ({ campaign_slug }) => {
    const rows = campaignStageRows(campaign_slug);
    return rows.length > 0
      ? jsonResult({
          ok: true,
          campaign_slug,
          stages: rows.map(stageEntry),
        })
      : notFound("campaign", campaign_slug);
  },
);

server.tool(
  "assess_campaign_stage",
  "Assess the current campaign stage from explicit signals and return the best stage match.",
  {
    campaign_slug: z
      .string()
      .describe("Campaign slug, currently gdpr_complaints"),
    controller_contacted: z.boolean().default(false),
    dpa_complaint_filed: z.boolean().default(false),
    cross_border_dimension: z.boolean().default(false),
    systemic_pattern: z.boolean().default(false),
    regulator_silent: z.boolean().default(false),
    need_public_pressure: z.boolean().default(false),
    want_media_route: z.boolean().default(false),
    want_ngo_support: z.boolean().default(false),
  },
  async ({ campaign_slug, ...signals }) => {
    const assessed = assessedCampaignStage(campaign_slug, signals);
    return assessed.best
      ? jsonResult({
          ok: true,
          campaign_slug,
          signals,
          current_stage: {
            score: assessed.best.score,
            reasons: assessed.best.reasons,
            ...stageEntry(assessed.best.row),
          },
          alternatives: assessed.ranked.slice(1, 4).map((entry) => ({
            score: entry.score,
            reasons: entry.reasons,
            ...stageEntry(entry.row),
          })),
        })
      : notFound("campaign", campaign_slug);
  },
);

server.tool(
  "recommend_next_step",
  "Recommend the next campaign move for a campaign stage, with templates, bundles, and datasets where available.",
  {
    campaign_slug: z
      .string()
      .describe("Campaign slug, currently gdpr_complaints"),
    controller_contacted: z.boolean().default(false),
    dpa_complaint_filed: z.boolean().default(false),
    cross_border_dimension: z.boolean().default(false),
    systemic_pattern: z.boolean().default(false),
    regulator_silent: z.boolean().default(false),
    need_public_pressure: z.boolean().default(false),
    want_media_route: z.boolean().default(false),
    want_ngo_support: z.boolean().default(false),
  },
  async ({ campaign_slug, ...signals }) => {
    const assessed = assessedCampaignStage(campaign_slug, signals);
    if (!assessed.best) {
      return notFound("campaign", campaign_slug);
    }

    const recommendations = matchedCampaignRules(
      campaign_slug,
      assessed.best.row.stage_key ?? "",
      signals,
    );

    return jsonResult({
      ok: true,
      campaign_slug,
      signals,
      assessed_stage: {
        score: assessed.best.score,
        reasons: assessed.best.reasons,
        ...stageEntry(assessed.best.row),
      },
      recommendations,
      warning:
        recommendations.length === 0
          ? "No next-step rule matched the current signal set. Inspect the stage directly or refine the signals."
          : null,
    });
  },
);

server.tool(
  "recommend_escalation",
  "Recommend only medium- or high-escalation campaign moves for the current stage and signal set.",
  {
    campaign_slug: z
      .string()
      .describe("Campaign slug, currently gdpr_complaints"),
    controller_contacted: z.boolean().default(false),
    dpa_complaint_filed: z.boolean().default(false),
    cross_border_dimension: z.boolean().default(false),
    systemic_pattern: z.boolean().default(false),
    regulator_silent: z.boolean().default(false),
    need_public_pressure: z.boolean().default(false),
    want_media_route: z.boolean().default(false),
    want_ngo_support: z.boolean().default(false),
  },
  async ({ campaign_slug, ...signals }) => {
    const assessed = assessedCampaignStage(campaign_slug, signals);
    if (!assessed.best) {
      return notFound("campaign", campaign_slug);
    }

    const recommendations = matchedCampaignRules(
      campaign_slug,
      assessed.best.row.stage_key ?? "",
      signals,
      "medium",
    );

    return jsonResult({
      ok: true,
      campaign_slug,
      signals,
      assessed_stage: {
        score: assessed.best.score,
        reasons: assessed.best.reasons,
        ...stageEntry(assessed.best.row),
      },
      escalation_options: recommendations,
      warning:
        recommendations.length === 0
          ? "No escalation rule matched the current signal set. That usually means the case is not ready for external pressure yet."
          : null,
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
      audience_filter_mode: audience ? "exact_match_when_available" : "none",
      country_matches_found: result.countryMatchesFound,
      country_matches_total: result.countryMatchesTotal,
      audience_matches_found: result.audienceMatchesFound,
      audience_matches_total: result.audienceMatchesTotal,
      scoped_committee_role_matches_total: result.scopedCommitteeRoleMatchesTotal,
      result_index_diversity: result.resultIndexDiversity,
      confidence_band: result.confidenceBand,
      suggested_action: result.suggestedAction,
      confidence_reason: result.confidenceReason,
      scope_message: result.scopeMessage,
      suppressed_matches: result.suppressedMatches,
      fallback_strategy: result.fallbackStrategy,
      audience_fallback_strategy: result.audienceFallbackStrategy,
      search_warning: result.searchWarning,
      ranking_warning: result.rankingWarning,
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
    const template = resolveTemplate(registryRowForSlug(template_slug));
    if (!template) {
      return notFound("template", template_slug);
    }

    const playbook = issue_slug ? getItemBySlug(catalog.playbooks, issue_slug) : undefined;
    return jsonResult({
      ok: true,
      user_facts,
      template: {
        template_slug: template.template_slug,
        mcp_slug: template.mcp_slug,
        title: template.title,
        summary: template.summary,
        path: template.source_path,
        template_family: template.template_family,
        stage: template.stage,
        jurisdiction_scope: template.jurisdiction_scope,
      },
      related_playbook: playbook ? shortItem(playbook) : null,
      guidance: [
        "Use the template structure and preserve legal/procedural caveats.",
        "Ground the draft in the user facts and avoid inventing dates, references, or legal claims.",
        "Use the local file paths in this packet for analysis and provenance only, not in the final outward-facing draft.",
      ],
      warnings: packetWarnings(template_slug, user_facts, issue_slug),
      packet: {
        template_body: template.body,
        playbook_body: playbook?.body ?? null,
      },
    });
  },
);

const transport = new StdioServerTransport();
await server.connect(transport);
