import { readFileSync, readdirSync } from "node:fs";
import path from "node:path";

export type RepoItem = {
  slug: string;
  title: string;
  path: string;
  category: string;
  summary: string;
  body: string;
};

export type DatasetSummary = {
  slug: string;
  title: string;
  path: string;
  rows: number;
  columns: string[];
  sample: Record<string, string>[];
};

export type IssueRoute = {
  issue_key: string;
  issue_name: string;
  first_route_type: string;
  possible_eu_layer: string;
  possible_national_layer: string;
  evidence_priority: string;
  notes: string;
};

export type AuthorityRow = Record<string, string>;

export type ContactRow = Record<string, string>;

export type BundleRow = Record<string, string>;

export type Catalog = {
  repoRoot: string;
  playbooks: RepoItem[];
  templates: RepoItem[];
  emailTemplates: RepoItem[];
  datasets: DatasetSummary[];
  issueRoutes: IssueRoute[];
  nationalAuthorities: AuthorityRow[];
  issueBundles: BundleRow[];
  contactRows: ContactRow[];
};

function slugFromFilename(filePath: string): string {
  return path.basename(filePath, path.extname(filePath));
}

function readText(filePath: string): string {
  return readFileSync(filePath, "utf8");
}

function firstMarkdownHeading(text: string): string {
  const match = text.match(/^#\s+(.+)$/m);
  return match ? match[1].trim() : "";
}

function firstParagraph(text: string): string {
  const normalized = text.replace(/\r/g, "");
  const withoutHeading = normalized.replace(/^#.*$/m, "").trim();
  const blocks = withoutHeading
    .split(/\n\s*\n/)
    .map((block) => block.trim().replace(/\n+/g, " "))
    .filter(Boolean);
  return blocks[0] ?? "";
}

function loadMarkdownItems(
  repoRoot: string,
  relativeDir: string,
  category: string,
  options?: { include?: (name: string) => boolean },
): RepoItem[] {
  const absoluteDir = path.join(repoRoot, relativeDir);
  const names = readdirSync(absoluteDir)
    .filter((name: string) => name.endsWith(".md"))
    .filter((name: string) => (options?.include ? options.include(name) : true))
    .sort();

  return names.map((name: string) => {
    const absolutePath = path.join(absoluteDir, name);
    const body = readText(absolutePath);
    return {
      slug: slugFromFilename(name),
      title: firstMarkdownHeading(body) || slugFromFilename(name),
      path: absolutePath,
      category,
      summary: firstParagraph(body),
      body,
    };
  });
}

function parseCsv(text: string): Record<string, string>[] {
  const lines = text.replace(/\r/g, "").split("\n").filter(Boolean);
  if (lines.length === 0) {
    return [];
  }

  const rows: string[][] = [];
  let current = "";
  let row: string[] = [];
  let inQuotes = false;

  const pushCell = () => {
    row.push(current);
    current = "";
  };

  const pushRow = () => {
    rows.push(row);
    row = [];
  };

  const full = text.replace(/\r/g, "");
  for (let i = 0; i < full.length; i += 1) {
    const char = full[i];
    const next = full[i + 1];

    if (char === "\"") {
      if (inQuotes && next === "\"") {
        current += "\"";
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }

    if (char === "," && !inQuotes) {
      pushCell();
      continue;
    }

    if (char === "\n" && !inQuotes) {
      pushCell();
      pushRow();
      continue;
    }

    current += char;
  }

  if (current.length > 0 || row.length > 0) {
    pushCell();
    pushRow();
  }

  const [header, ...dataRows] = rows;
  return dataRows
    .filter((cells) => cells.some((cell) => cell.trim() !== ""))
    .map((cells) => {
      const record: Record<string, string> = {};
      for (let index = 0; index < header.length; index += 1) {
        record[header[index]] = cells[index] ?? "";
      }
      return record;
    });
}

export function readCsvFile(filePath: string): Record<string, string>[] {
  return parseCsv(readText(filePath));
}

function csvTitleFromSlug(slug: string): string {
  return slug
    .split("-")
    .map((part) => (part ? part[0].toUpperCase() + part.slice(1) : part))
    .join(" ");
}

const COMMISSION_SERVICE_KEYWORDS: Record<string, string[]> = {
  CLIMA: ["climate", "green deal", "emissions", "net zero", "clean growth"],
  CNECT: [
    "digital policy",
    "ai regulation",
    "artificial intelligence",
    "platform regulation",
    "cybersecurity",
    "connectivity",
    "data governance",
  ],
  COMP: ["competition", "antitrust", "state aid", "merger control", "digital competition"],
  DIGIT: ["digital government", "public sector IT", "digital infrastructure"],
  EEAS: ["foreign affairs", "external action", "ukraine", "security policy", "diplomacy"],
  ENEST: ["enlargement", "western balkans", "ukraine", "eastern neighbourhood"],
  ENV: ["environment", "water resilience", "circular economy", "biodiversity"],
  FPI: ["foreign policy instruments", "security policy", "ukraine", "external action"],
  HOME: ["migration", "asylum", "internal security", "borders"],
  JUST: ["justice", "rule of law", "fundamental rights", "consumer rights"],
  MOVE: ["transport", "mobility", "aviation", "rail"],
  NEAR: ["enlargement", "western balkans", "ukraine", "neighbourhood policy"],
  SANTE: ["health", "pharmaceuticals", "medicines", "public health", "HERA", "food safety"],
  TAXUD: ["taxation", "customs", "excise", "green taxation"],
};

function normalizedServiceCode(value: string): string {
  return value.replace(/^DG\s+/i, "").trim().toUpperCase();
}

function expandedCommissionKeywords(services: string): string {
  const keywords = new Set<string>();
  for (const rawCode of services.split(/[;,]/).map((part) => part.trim()).filter(Boolean)) {
    const code = normalizedServiceCode(rawCode);
    for (const keyword of COMMISSION_SERVICE_KEYWORDS[code] ?? []) {
      keywords.add(keyword);
    }
  }
  return [...keywords].join("; ");
}

function loadDatasets(repoRoot: string): DatasetSummary[] {
  const sections = readdirSync(path.join(repoRoot, "data"), {
    withFileTypes: true,
  }).filter((entry: { isDirectory(): boolean }) => entry.isDirectory());

  const output: DatasetSummary[] = [];

  for (const section of sections) {
    const sectionDir = path.join(repoRoot, "data", section.name);
    const csvNames = readdirSync(sectionDir)
      .filter((name: string) => name.endsWith(".csv"))
      .sort();

    for (const csvName of csvNames) {
      const absolutePath = path.join(sectionDir, csvName);
      const rows = readCsvFile(absolutePath);
      const columns = rows[0] ? Object.keys(rows[0]) : [];
      output.push({
        slug: slugFromFilename(csvName),
        title: csvTitleFromSlug(slugFromFilename(csvName)),
        path: absolutePath,
        rows: rows.length,
        columns,
        sample: rows.slice(0, 3),
      });
    }
  }

  return output.sort((a, b) => a.slug.localeCompare(b.slug));
}

function loadIssueRoutes(repoRoot: string): IssueRoute[] {
  const rows = parseCsv(
    readText(path.join(repoRoot, "data", "national-authorities", "issue-router.csv")),
  );
  return rows as IssueRoute[];
}

function loadNationalAuthorities(repoRoot: string): AuthorityRow[] {
  return parseCsv(
    readText(
      path.join(
        repoRoot,
        "data",
        "national-authorities",
        "national-digital-authorities.csv",
      ),
    ),
  );
}

function loadIssueBundles(repoRoot: string): BundleRow[] {
  return parseCsv(
    readText(
      path.join(
        repoRoot,
        "data",
        "community-contacts",
        "issue-specific-contact-bundles.csv",
      ),
    ),
  );
}

function loadContactRows(repoRoot: string): ContactRow[] {
  const contactFiles = [
    path.join(
      repoRoot,
      "data",
      "community-contacts",
      "eu-digital-rights-and-media-contacts.csv",
    ),
    path.join(
      repoRoot,
      "data",
      "community-contacts",
      "national-digital-rights-organisations.csv",
    ),
    path.join(
      repoRoot,
      "data",
      "community-contacts",
      "womens-rights-and-gender-equality-contacts.csv",
    ),
  ];

  const baseRows = contactFiles.flatMap((filePath) =>
    readCsvFile(filePath).map((row) => ({
      ...row,
      __source_path: filePath,
      __contact_index: "general",
    })),
  );

  const ewlPath = path.join(
    repoRoot,
    "data",
    "community-contacts",
    "ewl-member-network.csv",
  );
  const ewlRows = readCsvFile(ewlPath).map((row) => ({
    ...row,
    organization: row.member_name,
    country: row.country_or_label,
    public_contact_type: "contact_page",
    public_contact: row.listed_website,
    public_page: row.listed_website,
    audience: "citizens; civil society; journalists",
    focus: "women's rights; gender equality; EWL member network",
    notes: "Listed on the European Women's Lobby membership directory.",
    __source_path: ewlPath,
    __contact_index: "womens_member_network",
  }));

  const equalityPath = path.join(
    repoRoot,
    "data",
    "national-authorities",
    "national-equality-bodies.csv",
  );
  const equalityRows = readCsvFile(equalityPath).map((row) => ({
    ...row,
    organization: row.body_name,
    country: row.country_name,
    public_contact_type: "contact_page",
    public_contact: row.website_urls,
    public_page: row.website_urls,
    audience: "citizens; civil society",
    focus: ["women's rights", "gender equality", row.body_description]
      .filter(Boolean)
      .join("; "),
    notes: row.notes,
    __source_path: equalityPath,
    __contact_index: "national_equality_body",
  }));

  const bundlesPath = path.join(
    repoRoot,
    "data",
    "community-contacts",
    "issue-specific-contact-bundles.csv",
  );
  const bundleRows = readCsvFile(bundlesPath).map((row) => ({
    ...row,
    organization: row.organization,
    country: row.org_scope,
    public_contact_type: row.contact_scope,
    public_contact: row.public_contact,
    public_page: row.source_url,
    audience: "citizens; journalists; civil society",
    focus: [row.bundle_label, row.bundle_slug, row.why_this_route, row.org_scope]
      .filter(Boolean)
      .join("; "),
    notes: `Bundle: ${row.bundle_label} | Scope: ${row.org_scope} | ${row.why_this_route}`,
    __source_path: bundlesPath,
    __contact_index: "issue_bundle",
  }));

  const institutionalPath = path.join(
    repoRoot,
    "data",
    "institutional-contacts",
    "institutional-contacts.csv",
  );
  const institutionalRows = readCsvFile(institutionalPath).map((row) => ({
    ...row,
    organization: row.unit,
    public_contact_type: row.role,
    public_contact: row.contact_email || row.contact_phone,
    public_phone: row.contact_phone,
    public_page: "",
    audience: "citizens; journalists; civil society",
    focus: [row.scope, row.unit, row.role].filter(Boolean).join("; "),
    notes: [row.institution, row.notes].filter(Boolean).join(" | "),
    __source_path: institutionalPath,
    __contact_index: "institutional_route",
  }));

  const mepPath = path.join(
    repoRoot,
    "data",
    "mep-contacts",
    "complete_mep_database_topics.csv",
  );
  const mepRows = readCsvFile(mepPath).map((row) => ({
    ...row,
    organization: row.mep_name,
    public_contact: row.email,
    public_phone:
      row.staff_contact_phone && row.staff_contact_phone !== "N/A"
        ? row.staff_contact_phone
        : "",
    contact_scope: "political_office",
    audience: "citizens; journalists; civil society",
    focus: [row.policy_briefs, row.topic_tags, row.committee_memberships]
      .filter(Boolean)
      .join("; "),
    notes: [
      row.political_group ? `Political group: ${row.political_group}` : "",
      row.staff_contact_name && row.staff_contact_name !== "N/A"
        ? `Staff contact: ${row.staff_contact_name}`
        : "",
      row.staff_contact_email && row.staff_contact_email !== "N/A"
        ? `Staff email: ${row.staff_contact_email}`
        : "",
      row.role_tags ? `Roles: ${row.role_tags}` : "",
    ]
      .filter(Boolean)
      .join(" | "),
    __source_path: mepPath,
    __contact_index: "mep_political",
  }));

  const collegePath = path.join(
    repoRoot,
    "data",
    "commission-reference",
    "commission-college.csv",
  );
  const collegeRawRows = readCsvFile(collegePath);
  const collegeByMember = new Map(
    collegeRawRows.map((row) => [row.member_name, row] as const),
  );
  const collegeRows = collegeRawRows.map((row) => ({
    ...row,
    organization: row.member_name,
    public_contact_type: "official_portfolio_page",
    public_contact: row.official_college_url,
    public_page: row.official_college_url,
    audience: "citizens; journalists; civil society",
    focus: [
      row.portfolio,
      row.lead_supporting_services,
      expandedCommissionKeywords(row.lead_supporting_services),
    ]
      .filter(Boolean)
      .join("; "),
    notes: [
      row.member_role ? `Role: ${row.member_role}` : "",
      row.portfolio ? `Portfolio: ${row.portfolio}` : "",
      row.lead_supporting_services
        ? `Lead services: ${row.lead_supporting_services}`
        : "",
      row.official_responsibilities_url
        ? `Responsibilities: ${row.official_responsibilities_url}`
        : "",
    ]
      .filter(Boolean)
      .join(" | "),
    __source_path: collegePath,
    __contact_index: "commission_college",
  }));

  const cabinetPath = path.join(
    repoRoot,
    "data",
    "commission-reference",
    "commission-cabinet-contacts.csv",
  );
  const cabinetRows = readCsvFile(cabinetPath).map((row) => {
    const collegeRow = collegeByMember.get(row.member_name);
    const serviceKeywords = expandedCommissionKeywords(
      collegeRow?.lead_supporting_services ?? "",
    );
    return {
      ...row,
      organization: row.member_name,
      public_contact_type: row.office_contact_kind,
      public_contact: row.office_contact,
      public_page:
        row.team_page_url ||
        (row.office_contact.startsWith("http") ? row.office_contact : "") ||
        collegeRow?.official_college_url ||
        "",
      audience: "citizens; journalists; civil society",
      focus: [
        collegeRow?.portfolio,
        collegeRow?.lead_supporting_services,
        serviceKeywords,
        row.member_role,
      ]
        .filter(Boolean)
        .join("; "),
      notes: [
        collegeRow?.portfolio ? `Portfolio: ${collegeRow.portfolio}` : "",
        collegeRow?.lead_supporting_services
          ? `Lead services: ${collegeRow.lead_supporting_services}`
          : "",
        row.head_of_cabinet_name ? `Head of cabinet: ${row.head_of_cabinet_name}` : "",
        row.head_of_cabinet_email
          ? `Head email: ${row.head_of_cabinet_email}`
          : "",
        row.principal_assistant_name
          ? `Assistant: ${row.principal_assistant_name}`
          : "",
        row.notes,
      ]
        .filter(Boolean)
        .join(" | "),
      __source_path: cabinetPath,
      __contact_index: "commission_cabinet",
    };
  });

  const dgPressPath = path.join(
    repoRoot,
    "data",
    "commission-reference",
    "commission-dg-press-surfaces.csv",
  );
  const dgPressRows = readCsvFile(dgPressPath).map((row) => ({
    ...row,
    organization: row.unit_name,
    public_contact_type: row.public_surface_type,
    public_contact:
      row.press_contacts_url ||
      row.public_question_url ||
      row.public_email ||
      row.department_page_url,
    public_page: row.department_page_url,
    audience: "citizens; journalists; civil society",
    focus: [
      row.unit_code,
      row.unit_name,
      expandedCommissionKeywords(row.unit_code),
      row.notes,
    ]
      .filter(Boolean)
      .join("; "),
    notes: [
      row.unit_type ? `Unit type: ${row.unit_type}` : "",
      row.press_contacts_url ? `Press contacts: ${row.press_contacts_url}` : "",
      row.public_question_url ? `Public question route: ${row.public_question_url}` : "",
      row.public_email ? `Public email: ${row.public_email}` : "",
      row.public_phone ? `Public phone: ${row.public_phone}` : "",
      row.notes,
    ]
      .filter(Boolean)
      .join(" | "),
    __source_path: dgPressPath,
    __contact_index: "commission_dg_press",
  }));

  const sppPath = path.join(
    repoRoot,
    "data",
    "commission-reference",
    "commission-spp-contacts.csv",
  );
  const sppRows = readCsvFile(sppPath).map((row) => ({
    ...row,
    organization: row.name,
    public_contact_type: "media_contact",
    public_contact: row.email || row.phone || row.source_url,
    public_page: row.source_url,
    audience: "journalists; citizens; civil society",
    focus: [row.role, row.responsibilities, row.section_name]
      .filter(Boolean)
      .join("; "),
    notes: [
      row.role,
      row.phone ? `Phone: ${row.phone}` : "",
      row.mobile ? `Mobile: ${row.mobile}` : "",
      row.responsibilities ? `Responsibilities: ${row.responsibilities}` : "",
    ]
      .filter(Boolean)
      .join(" | "),
    __source_path: sppPath,
    __contact_index: "commission_spp",
  }));

  return [
    ...baseRows,
    ...ewlRows,
    ...equalityRows,
    ...bundleRows,
    ...institutionalRows,
    ...collegeRows,
    ...cabinetRows,
    ...dgPressRows,
    ...sppRows,
    ...mepRows,
  ];
}

export function buildCatalog(repoRoot: string): Catalog {
  return {
    repoRoot,
    playbooks: loadMarkdownItems(repoRoot, "docs/digital-issues", "playbook", {
      include: (name) => name !== "README.md",
    }),
    templates: [
      ...loadMarkdownItems(repoRoot, "templates/level-0-public-comment", "template", {
        include: (name) => name !== "README.md",
      }),
      ...loadMarkdownItems(repoRoot, "templates/level-1-administrative", "template", {
        include: (name) => name !== "README.md",
      }),
    ].sort((a, b) => a.slug.localeCompare(b.slug)),
    emailTemplates: loadMarkdownItems(
      repoRoot,
      "docs/digital-issues/email-templates",
      "email-template",
      { include: (name) => name !== "README.md" },
    ),
    datasets: loadDatasets(repoRoot),
    issueRoutes: loadIssueRoutes(repoRoot),
    nationalAuthorities: loadNationalAuthorities(repoRoot),
    issueBundles: loadIssueBundles(repoRoot),
    contactRows: loadContactRows(repoRoot),
  };
}

export function getItemBySlug(items: RepoItem[], slug: string): RepoItem | undefined {
  return items.find((item) => item.slug === slug);
}

export function getDatasetBySlug(
  datasets: DatasetSummary[],
  slug: string,
): DatasetSummary | undefined {
  return datasets.find((dataset) => dataset.slug === slug);
}
