import type { Catalog, ContactRow, IssueRoute, RepoItem } from "./catalog.js";

const COMMITTEE_CODES = new Set([
  "afet",
  "agri",
  "budi",
  "budg",
  "cont",
  "cult",
  "deve",
  "droi",
  "econ",
  "empl",
  "envi",
  "femm",
  "fisc",
  "imco",
  "inta",
  "itre",
  "juri",
  "libe",
  "pech",
  "peri",
  "peti",
  "regi",
  "sant",
  "sede",
  "tran",
  "afco",
]);

const GENERIC_TOKENS = new Set([
  "policy",
  "policies",
  "european",
  "committee",
  "commissioner",
  "commissioners",
  "affairs",
  "market",
  "internal",
  "research",
  "industry",
  "energy",
  "civil",
  "rights",
  "digital",
  "europe",
]);

const COMMISSION_CONTACT_INDEXES = new Set([
  "commission_cabinet",
  "commission_college",
  "commission_dg_press",
  "commission_spp",
]);

const SUPPORT_ROUTE_PATTERN =
  /\b(support|help|helpline|assistance|safe(?:ty)?|secure tip|security helpline|at risk|in exile|emergency)\b/i;
const JOURNALIST_ROUTE_PATTERN =
  /\b(journalist|journalists|press freedom|press safety|press-freedom|media freedom|newsroom|editorial|secure source)\b/i;
const SURVEILLANCE_ROUTE_PATTERN =
  /\b(surveillance|spyware|pegasus|state power|privacy|data protection|digital security|wiretap|source protection)\b/i;
const FINANCIAL_ADVICE_PATTERN =
  /\b(buy shares|stock advice|stock tips|investment advice|financial advice|should i invest|trading advice|portfolio advice|share dealing)\b/i;
const MEDICAL_REFERRAL_PATTERN =
  /\b(find me a doctor|doctor referral|physician referral|medical referral|find a doctor|need a doctor|hospital referral|clinic referral)\b/i;

type ConfidenceBand = "high" | "medium" | "low" | "out_of_scope";

function inferConfidence(
  normalizedTopic: string,
  matches: Array<{ score: number }>,
): {
  confidenceBand: ConfidenceBand;
  suggestedAction: "use_results" | "refine_query" | "suggest_external_resource" | "out_of_scope";
  confidenceReason: string;
  scopeMessage: string | null;
} {
  if (FINANCIAL_ADVICE_PATTERN.test(normalizedTopic)) {
    return {
      confidenceBand: "out_of_scope",
      suggestedAction: "out_of_scope",
      confidenceReason: "The query asks for personal financial or investment advice, which is outside the toolkit's remit.",
      scopeMessage:
        "This toolkit covers EU citizen-engagement, public-interest contacts, and institutional routing, not stock-picking or personal financial advice.",
    };
  }

  if (MEDICAL_REFERRAL_PATTERN.test(normalizedTopic)) {
    return {
      confidenceBand: "out_of_scope",
      suggestedAction: "suggest_external_resource",
      confidenceReason: "The query asks for a medical referral rather than an EU civic, rights, or policy route.",
      scopeMessage:
        "Try national health-service directories, licensed medical providers, or emergency services instead of the toolkit's civic-contact datasets.",
    };
  }

  if (matches.length === 0) {
    return {
      confidenceBand: "out_of_scope",
      suggestedAction: "refine_query",
      confidenceReason: "No materially relevant routes were found in the indexed toolkit datasets.",
      scopeMessage: "No good match was found in the toolkit for this query.",
    };
  }

  const topScore = matches[0]?.score ?? 0;
  const scoreSpread = topScore - (matches[Math.min(matches.length - 1, 4)]?.score ?? topScore);
  const tightlyClustered = scoreSpread <= 2;

  if (topScore <= 6 && tightlyClustered) {
    return {
      confidenceBand: "out_of_scope",
      suggestedAction: "refine_query",
      confidenceReason: "Only weak, tightly-clustered token matches were found.",
      scopeMessage: "This query does not map cleanly to the toolkit's scope or needs a more specific civic/policy framing.",
    };
  }

  if (topScore <= 10) {
    return {
      confidenceBand: "low",
      suggestedAction: "refine_query",
      confidenceReason: "Matches were found, but relevance is weak or ambiguous.",
      scopeMessage: null,
    };
  }

  if (topScore <= 24) {
    return {
      confidenceBand: "medium",
      suggestedAction: "use_results",
      confidenceReason: "Matches are relevant, but the query may still mix multiple intents.",
      scopeMessage: null,
    };
  }

  return {
    confidenceBand: "high",
    suggestedAction: "use_results",
    confidenceReason: "The top matches have strong relevance and clear separation from weaker rows.",
    scopeMessage: null,
  };
}

function audienceValues(value: string): string[] {
  return value
    .split(/[;,]/)
    .map((part) => normalizeText(part))
    .filter(Boolean);
}

function audienceExactMatch(rowAudience: string, requestedAudience: string[]): boolean {
  if (requestedAudience.length === 0) {
    return true;
  }
  const available = new Set(audienceValues(rowAudience));
  return requestedAudience.some((needle) => available.has(needle));
}

function hasScopedCommitteeRole(
  roleText: string,
  committeeCodes: string[],
  role: "chair" | "vice chair" | "rapporteur" | "coordinator",
): boolean {
  return committeeCodes.some((code) => roleText.includes(`${code} ${role}`));
}

function hasAnyScopedCommitteeRole(roleText: string, committeeCodes: string[]): boolean {
  return committeeCodes.some((code) =>
    ["chair", "vice chair", "rapporteur", "coordinator"].some((role) =>
      roleText.includes(`${code} ${role}`),
    ),
  );
}

function committeeSecretariatMatch(row: ContactRow, committeeCodes: string[]): boolean {
  if (row.__contact_index !== "institutional_route") {
    return false;
  }
  const roleText = normalizeText(row.role ?? "");
  if (!roleText.includes("committee secretariat")) {
    return false;
  }
  const searchable = normalizeText(
    [row.organization, row.unit, row.scope, row.focus, row.contact_email].filter(Boolean).join(" "),
  );
  return committeeCodes.some((code) => new RegExp(`(^|\\s)${code}(\\s|$)`, "i").test(searchable));
}

function tokenize(value: string): string[] {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter((token) => token.length > 1);
}

function normalizeText(value: string): string {
  return value
    .toLowerCase()
    .replace(/[_/;:,()-]+/g, " ")
    .replace(/[^a-z0-9\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function normalizeCountry(value: string): string {
  const normalized = value
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();

  const aliases: Record<string, string> = {
    "czech republic": "czechia",
    "republic of north macedonia": "north macedonia",
    "fyrom": "north macedonia",
    "united kingdom": "uk",
    "great britain": "uk",
  };

  return aliases[normalized] ?? normalized;
}

function scoreText(haystack: string, needles: string[]): number {
  const lower = normalizeText(haystack);
  let score = 0;

  for (const needle of needles) {
    const normalizedNeedle = normalizeText(needle);
    if (!normalizedNeedle) {
      continue;
    }
    if (new RegExp(`(^|\\s)${normalizedNeedle}(\\s|$)`, "i").test(lower)) {
      if (COMMITTEE_CODES.has(normalizedNeedle)) {
        score += 6;
      } else if (GENERIC_TOKENS.has(normalizedNeedle)) {
        score += 1;
      } else if (normalizedNeedle.length >= 8) {
        score += 3;
      } else if (normalizedNeedle.length >= 5) {
        score += 2;
      } else {
        score += 1;
      }
    }
  }

  return score;
}

function uniquePhrases(tokens: string[]): string[] {
  const phrases = new Set<string>();
  for (let size = 2; size <= Math.min(3, tokens.length); size += 1) {
    for (let index = 0; index <= tokens.length - size; index += 1) {
      phrases.add(tokens.slice(index, index + size).join(" "));
    }
  }
  return [...phrases];
}

function rolePriorityBoost(roleText: string): number {
  let boost = 0;
  if (/\bchair\b/.test(roleText)) {
    boost += 4;
  }
  if (/\bcoordinator\b/.test(roleText)) {
    boost += 3;
  }
  if (/\brapporteur\b/.test(roleText)) {
    boost += 3;
  }
  if (/\bvice chair\b/.test(roleText)) {
    boost += 2;
  }
  return boost;
}

function queryWantsRole(normalizedTopic: string, role: "rapporteur" | "coordinator" | "chair" | "vice_chair"): boolean {
  switch (role) {
    case "rapporteur":
      return /\brapporteurs?\b/.test(normalizedTopic);
    case "coordinator":
      return /\bcoordinators?\b/.test(normalizedTopic);
    case "chair":
      return /\bchairs?\b/.test(normalizedTopic);
    case "vice_chair":
      return /\bvice chairs?\b/.test(normalizedTopic) || /\bvice chair\b/.test(normalizedTopic);
  }
}

function queryWantsCommissionPortfolio(normalizedTopic: string): boolean {
  return (
    /\bcommissioners?\b/.test(normalizedTopic) ||
    /\bexecutive vice president\b/.test(normalizedTopic) ||
    /\bexecutive vice presidents\b/.test(normalizedTopic) ||
    /\bhigh representative\b/.test(normalizedTopic)
  );
}

function routeKeywords(route: IssueRoute): string[] {
  return tokenize(
    [
      route.issue_key,
      route.issue_name,
      route.first_route_type,
      route.possible_eu_layer,
      route.possible_national_layer,
      route.evidence_priority,
      route.notes,
    ].join(" "),
  );
}

function playbookKeywords(playbook: RepoItem): string[] {
  return tokenize(`${playbook.slug} ${playbook.title} ${playbook.summary}`);
}

export function rankIssueMatches(catalog: Catalog, problemDescription: string) {
  const needles = tokenize(problemDescription);
  const routeMatches = catalog.issueRoutes
    .map((route) => ({
      route,
      score: scoreText(routeKeywords(route).join(" "), needles),
    }))
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 3);

  const playbookMatches = catalog.playbooks
    .map((playbook) => ({
      playbook,
      score: scoreText(playbookKeywords(playbook).join(" "), needles),
    }))
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 3);

  return { routeMatches, playbookMatches };
}

export function filterAuthorities(
  catalog: Catalog,
  country: string,
  issueType?: string,
): ContactRow[] {
  const normalizedCountry = normalizeCountry(country);
  const issueLower = issueType?.toLowerCase() ?? "";

  return catalog.nationalAuthorities
    .filter((row) =>
      [row.country, row.member_state, row.country_name, row.country_code]
        .filter(Boolean)
        .some((value) => normalizeCountry(value) === normalizedCountry),
    )
    .map((row) => ({
      ...row,
      __match_reason: issueLower
        ? `Matched country ${country} with issue context ${issueType}`
        : `Matched country ${country}`,
    }));
}

export function findRelevantContacts(
  catalog: Catalog,
  topic: string,
  audience?: string,
  country?: string,
) {
  const normalizedTopic = normalizeText(topic);
  const topicNeedles = tokenize(topic);
  const topicPhrases = uniquePhrases(topicNeedles);
  const audienceNeedles = tokenize(audience ?? "");
  const requestedAudience = audienceValues(audience ?? "");
  const normalizedCountry = country ? normalizeCountry(country) : undefined;
  const queryCommitteeCodes = topicNeedles.filter((token) => COMMITTEE_CODES.has(token));
  const queryMentionsRole =
    queryWantsRole(normalizedTopic, "rapporteur") ||
    queryWantsRole(normalizedTopic, "coordinator") ||
    queryWantsRole(normalizedTopic, "chair") ||
    queryWantsRole(normalizedTopic, "vice_chair");
  const queryWantsCommission = queryWantsCommissionPortfolio(normalizedTopic);
  const bareCommitteeCodeQuery =
    queryCommitteeCodes.length === 1 && topicNeedles.length === 1;
  const wantsJournalists =
    requestedAudience.includes("journalists") ||
    /\bjournalis|press|media|newsroom|source\b/.test(normalizedTopic);
  const wantsSupport = /\bhelp|support|assistance|helpline|emergency|safe(?:ty)?|secure\b/.test(
    normalizedTopic,
  );
  const wantsSurveillance = /\bsurveillance|spyware|pegasus|monitoring|wiretap|state power\b/.test(
    normalizedTopic,
  );
  const mixedOperationalQuery = wantsJournalists && (wantsSupport || wantsSurveillance);
  const queryTargetsPoliticalOffice =
    /\bmep|meps|committee|parliament|rapporteur|coordinator|chair|vice chair|commissioner\b/.test(
      normalizedTopic,
    );
  const countryFields = [
    "country",
    "country_name",
    "country_or_label",
    "jurisdiction",
  ];

  const ranked = catalog.contactRows
    .map((row) => {
      const searchable = normalizeText(Object.values(row).join(" "));
      const roleText = normalizeText(row.role_tags ?? row.notes ?? "");
      const committeeText = normalizeText(row.committee_memberships ?? "");
      const countryValues = countryFields
        .map((field) => row[field] ?? "")
        .filter(Boolean);
      const exactCountryMatch = normalizedCountry
        ? countryValues.some((value) => normalizeCountry(value) === normalizedCountry)
        : false;
      const exactAudienceMatch = audienceExactMatch(row.audience ?? "", requestedAudience);
      const topicScore = scoreText(searchable, topicNeedles);
      const phraseScore = topicPhrases.reduce((sum, phrase) => {
        if (!phrase) {
          return sum;
        }
        return sum + (searchable.includes(phrase) ? 6 : 0);
      }, normalizedTopic && searchable.includes(normalizedTopic) ? 10 : 0);
      const audienceScore = audienceNeedles.length > 0 ? scoreText(searchable, audienceNeedles) : 0;
      const roleBoost = rolePriorityBoost(roleText);
      const routeText = normalizeText(
        [
          row.audience,
          row.focus,
          row.notes,
          row.public_contact_type,
          row.contact_scope,
          row.bundle_slug,
          row.bundle_label,
        ]
          .filter(Boolean)
          .join(" "),
      );
      const journalistRouteMatch = JOURNALIST_ROUTE_PATTERN.test(routeText);
      const supportRouteMatch = SUPPORT_ROUTE_PATTERN.test(routeText);
      const surveillanceRouteMatch = SURVEILLANCE_ROUTE_PATTERN.test(routeText);
      const digitalSecurityHelplineMatch = /\bdigital security helpline\b/.test(routeText);
      const scopedCommitteeRoleMatch = hasAnyScopedCommitteeRole(
        roleText,
        queryCommitteeCodes,
      );
      let score =
        topicScore +
        phraseScore +
        (exactAudienceMatch ? 3 : audienceScore > 0 ? 1 : 0);

      if (row.__contact_index === "issue_bundle" && topicScore > 0) {
        score += 8;
        if ((row.org_scope || "").toLowerCase() === "eu_level") {
          score += 1;
        }
      }

      if (wantsJournalists) {
        if (exactAudienceMatch) {
          score += 3;
        }
        if (journalistRouteMatch) {
          score += 8;
        }
      }

      if (wantsSupport && supportRouteMatch) {
        score += 7;
      }

      if (wantsSurveillance && surveillanceRouteMatch) {
        score += 6;
      }

      if (
        wantsJournalists &&
        wantsSurveillance &&
        (row.__contact_index === "general" || row.__contact_index === "issue_bundle")
      ) {
        if (journalistRouteMatch || supportRouteMatch || surveillanceRouteMatch) {
          score += 5;
        }
      }

      if (
        wantsJournalists &&
        wantsSupport &&
        (row.__contact_index === "general" || row.__contact_index === "issue_bundle")
      ) {
        if (journalistRouteMatch && supportRouteMatch) {
          score += 10;
        } else if (journalistRouteMatch || supportRouteMatch) {
          score += 6;
        }
      }

      if (
        wantsJournalists &&
        wantsSupport &&
        wantsSurveillance &&
        (row.__contact_index === "general" || row.__contact_index === "issue_bundle")
      ) {
        if (journalistRouteMatch || supportRouteMatch || surveillanceRouteMatch) {
          score += 8;
        }
      }

      if (
        wantsJournalists &&
        wantsSupport &&
        wantsSurveillance &&
        digitalSecurityHelplineMatch
      ) {
        score += 14;
      }

      if (
        wantsJournalists &&
        (wantsSupport || wantsSurveillance) &&
        row.__contact_index === "mep_political" &&
        !queryTargetsPoliticalOffice
      ) {
        score -= 18;
        if (surveillanceRouteMatch) {
          score += 8;
        }
        if (journalistRouteMatch || supportRouteMatch) {
          score += 4;
        }
      }

      if (queryCommitteeCodes.length > 0) {
        const committeeMatch = queryCommitteeCodes.some((code) => committeeText.includes(code));
        const secretariatMatch = committeeSecretariatMatch(row, queryCommitteeCodes);
        if (row.__contact_index === "mep_political" && committeeMatch) {
          score += bareCommitteeCodeQuery ? 10 : 12;
          if (scopedCommitteeRoleMatch) {
            score += 4;
          }
          if (!queryMentionsRole) {
            score += roleBoost;
          }
          if (queryCommitteeCodes.length > 1 && queryCommitteeCodes.every((code) => committeeText.includes(code))) {
            score += 4;
          }
        } else if (secretariatMatch) {
          score += bareCommitteeCodeQuery ? 24 : 12;
        } else if (row.__contact_index !== "mep_political") {
          score -= 6;
        }
      }

      if (queryMentionsRole && roleText) {
        if (normalizedTopic && roleText.includes(normalizedTopic)) {
          score += 12;
        } else {
          for (const phrase of topicPhrases) {
            if (roleText.includes(phrase)) {
              score += 8;
            }
          }
        }

        const scopedCommitteeRoleQuery = queryCommitteeCodes.length > 0;
        if (
          queryWantsRole(normalizedTopic, "rapporteur") &&
          /\brapporteur\b/.test(roleText) &&
          (!scopedCommitteeRoleQuery ||
            hasScopedCommitteeRole(roleText, queryCommitteeCodes, "rapporteur"))
        ) {
          score += roleText.trim() === "rapporteur" ? 2 : 5;
        }
        if (
          queryWantsRole(normalizedTopic, "coordinator") &&
          /\bcoordinator\b/.test(roleText) &&
          (!scopedCommitteeRoleQuery ||
            hasScopedCommitteeRole(roleText, queryCommitteeCodes, "coordinator"))
        ) {
          score += 5;
        }
        if (
          queryWantsRole(normalizedTopic, "chair") &&
          /\bchair\b/.test(roleText) &&
          (!scopedCommitteeRoleQuery ||
            hasScopedCommitteeRole(roleText, queryCommitteeCodes, "chair"))
        ) {
          score += 5;
        }
        if (
          queryWantsRole(normalizedTopic, "vice_chair") &&
          /\bvice chair\b/.test(roleText) &&
          (!scopedCommitteeRoleQuery ||
            hasScopedCommitteeRole(roleText, queryCommitteeCodes, "vice chair"))
        ) {
          score += 4;
        }
      }

      if (queryWantsCommission) {
        if (COMMISSION_CONTACT_INDEXES.has(row.__contact_index)) {
          if (row.__contact_index === "commission_college") {
            score += 12;
          } else if (row.__contact_index === "commission_cabinet") {
            score += 10;
          } else if (row.__contact_index === "commission_dg_press") {
            score += 6;
          } else {
            score += 5;
          }
        } else if (row.__contact_index === "mep_political") {
          score -= 8;
          if (searchable.includes("former commissioner")) {
            score -= 4;
          }
        }
      }

      if (exactCountryMatch) {
        score += 5;
      } else if (normalizedCountry && searchable.includes(normalizedCountry)) {
        score += 2;
      }

      const rankedRow: ContactRow = {
        ...row,
        __audience_match: exactAudienceMatch ? "exact" : "none",
        __country_match: exactCountryMatch ? "exact" : "none",
        __country_values: countryValues.join(" | "),
      };

      return {
        row: rankedRow,
        score,
        topicScore,
        phraseScore,
        roleBoost,
        journalistRouteMatch,
        supportRouteMatch,
        surveillanceRouteMatch,
        digitalSecurityHelplineMatch,
        scopedCommitteeRoleMatch,
        exactCountryMatch,
        exactAudienceMatch,
      };
    })
    .filter(
      (item) =>
        item.topicScore > 0 ||
        item.exactCountryMatch ||
        (mixedOperationalQuery &&
          item.exactAudienceMatch &&
          (item.journalistRouteMatch || item.supportRouteMatch || item.surveillanceRouteMatch)),
    )
    .sort((a, b) => {
      if (queryWantsCommission) {
        const aCommission = COMMISSION_CONTACT_INDEXES.has(a.row.__contact_index);
        const bCommission = COMMISSION_CONTACT_INDEXES.has(b.row.__contact_index);
        if (aCommission !== bCommission) {
          return aCommission ? -1 : 1;
        }
        if (a.score !== b.score) {
          return b.score - a.score;
        }
      }

      const aCountryAndTopic = a.exactCountryMatch && a.topicScore > 0;
      const bCountryAndTopic = b.exactCountryMatch && b.topicScore > 0;
      if (aCountryAndTopic !== bCountryAndTopic) {
        return aCountryAndTopic ? -1 : 1;
      }
      if (a.phraseScore !== b.phraseScore) {
        return b.phraseScore - a.phraseScore;
      }
      if (a.topicScore !== b.topicScore) {
        return b.topicScore - a.topicScore;
      }
      if (a.score !== b.score) {
        return b.score - a.score;
      }
      if (!queryMentionsRole && a.roleBoost !== b.roleBoost) {
        return b.roleBoost - a.roleBoost;
      }
      if (a.exactCountryMatch !== b.exactCountryMatch) {
        return a.exactCountryMatch ? -1 : 1;
      }
      return 0;
    });

  const filteredRanked = ranked;
  const audienceExactMatchesTotal = filteredRanked.filter((item) => item.exactAudienceMatch).length;
  const audienceFilteredRanked =
    requestedAudience.length > 0 && audienceExactMatchesTotal > 0
      ? filteredRanked.filter((item) => item.exactAudienceMatch)
      : filteredRanked;
  const bestPhraseScore = ranked[0]?.phraseScore ?? 0;
  const phraseFilteredRanked =
    bestPhraseScore > 0
      ? audienceFilteredRanked.filter(
          (item) =>
            item.phraseScore > 0 ||
            item.topicScore >= 3 ||
            (mixedOperationalQuery &&
              item.exactAudienceMatch &&
              (item.journalistRouteMatch || item.supportRouteMatch || item.surveillanceRouteMatch)),
        )
      : audienceFilteredRanked;

  const operationalPriorityRows = mixedOperationalQuery
    ? phraseFilteredRanked.filter(
        (item) =>
          item.row.__contact_index !== "mep_political" &&
          (item.journalistRouteMatch || item.supportRouteMatch || item.surveillanceRouteMatch),
      )
        .sort((a, b) => {
          const aOperationalScore =
            (a.exactCountryMatch ? 6 : 0) +
            (a.digitalSecurityHelplineMatch ? 6 : 0) +
            (a.journalistRouteMatch ? 5 : 0) +
            (a.supportRouteMatch ? 5 : 0) +
            (a.surveillanceRouteMatch ? 4 : 0);
          const bOperationalScore =
            (b.exactCountryMatch ? 6 : 0) +
            (b.digitalSecurityHelplineMatch ? 6 : 0) +
            (b.journalistRouteMatch ? 5 : 0) +
            (b.supportRouteMatch ? 5 : 0) +
            (b.surveillanceRouteMatch ? 4 : 0);
          if (aOperationalScore !== bOperationalScore) {
            return bOperationalScore - aOperationalScore;
          }
          return b.score - a.score;
        })
    : [];
  const operationalSeed = operationalPriorityRows.slice(0, 6);
  const seededMatches = [
    ...operationalSeed,
    ...phraseFilteredRanked.filter((item) => !operationalSeed.includes(item)),
  ];
  const seenMatchKeys = new Set<string>();
  const matches = seededMatches
    .filter((item) => {
      const key = normalizeText(
        [item.row.organization, item.row.public_contact]
          .filter(Boolean)
          .join(" | "),
      );
      if (seenMatchKeys.has(key)) {
        return false;
      }
      seenMatchKeys.add(key);
      return true;
    })
    .slice(0, 10);
  const countryMatchesFound = matches.filter((item) => item.exactCountryMatch).length;
  const countryMatchesTotal = phraseFilteredRanked.filter((item) => item.exactCountryMatch).length;
  const scopedCommitteeRoleMatchesTotal = phraseFilteredRanked.filter(
    (item) => item.scopedCommitteeRoleMatch,
  ).length;
  const audienceMatchesFound = matches.filter((item) => item.exactAudienceMatch).length;
  const audienceMatchesTotal = phraseFilteredRanked.filter((item) => item.exactAudienceMatch).length;
  const indexSet = new Set(matches.map((item) => item.row.__contact_index));
  const dominantIndexShare =
    matches.length > 0
      ? Math.max(
          ...[...indexSet].map(
            (index) => matches.filter((item) => item.row.__contact_index === index).length,
          ),
        ) / matches.length
      : 0;
  const tiedTopScores =
    matches.length > 1 &&
    matches.every((item) => item.score === matches[0]?.score);
  const rankingWarning =
    tiedTopScores || indexSet.size === 1 || dominantIndexShare >= 0.8
      ? "Results are clustered into a narrow score band or one contact type. Treat them as candidate routes, not a definitive ranking, and prefer bundle or support-route entries when the query mixes multiple intents."
      : null;
  const confidence = inferConfidence(normalizedTopic, matches);
  const safeMatches = confidence.confidenceBand === "out_of_scope" ? [] : matches;

  return {
    matches: safeMatches,
    suppressedMatches: confidence.confidenceBand === "out_of_scope" ? matches.length : 0,
    countryMatchesFound,
    countryMatchesTotal,
    audienceMatchesFound,
    audienceMatchesTotal,
    scopedCommitteeRoleMatchesTotal,
    resultIndexDiversity: indexSet.size,
    fallbackStrategy:
      country && countryMatchesFound === 0
        ? "No country-specific matches were indexed for this query; broader EU-level or cross-border results were returned."
        : null,
    audienceFallbackStrategy:
      audience && audienceMatchesFound === 0
        ? "No exact audience-matched contacts were indexed for this query; broader cross-audience routes were returned."
        : null,
    confidenceBand: confidence.confidenceBand,
    suggestedAction: confidence.suggestedAction,
    confidenceReason: confidence.confidenceReason,
    scopeMessage: confidence.scopeMessage,
    searchWarning:
      queryMentionsRole &&
      queryCommitteeCodes.length > 0 &&
      scopedCommitteeRoleMatchesTotal === 0
        ? "No committee-scoped leadership tags were indexed for this committee query, so results show committee members but cannot reliably identify the chair or vice-chairs."
        : null,
    rankingWarning,
  };
}
