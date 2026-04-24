# ADR-0007: Citizen-First Cartography Layer

## Status

Accepted

## Context

The repository now has substantial depth:

- playbooks
- templates
- contact datasets
- campaign packs
- MCP selectors and campaign-decision tools

That depth helps power users and AI-assisted workflows, but it does not yet provide a true front door for an ordinary frustrated citizen.

The recurring real-world problem is:

- the user knows something unfair happened
- the user does not know whether the route is platform, controller, regulator, ombudsman, MEP, journalist, or NGO
- the user does not know whether the problem is EU-level, national, or mixed
- the user cannot afford hours of search just to discover who has power

In short: the digital interfaces were imposed, but the cartography was not provided.

## Decision

Add a plain-language `start-here` layer to the repo that starts from lived harm and maps the user into the existing deeper layers.

This layer should:

- begin from user situations rather than institutions
- explain who can move a problem before listing detailed contacts
- distinguish clearly between first contact, escalation, and public-pressure routes
- point users into the existing playbooks, datasets, bundles, and campaign packs

The cartography layer is documentation first. MCP should mirror it later, not replace it.

## Consequences

### Positive

- the repo becomes more usable without MCP
- citizens can orient before they choose tools, templates, or campaigns
- contributors get a clearer model for what “citizen-first” means
- the deeper MCP and campaign layers remain intact but are no longer the only navigable path

### Negative

- this adds another documentation layer to maintain
- oversimplification is a risk if the map stops reflecting the real procedural complexity underneath
- some pages will need frequent link maintenance as datasets and campaign packs expand

## Rejected Alternatives

### Rely on the MCP server as the main front door

Rejected because the repository must still be usable by humans without an MCP client and because plain-language orientation should not require software.

### Keep only deep playbooks and data indexes

Rejected because they presuppose too much institutional understanding from the user.

## Follow-Up

- create `docs/start-here/`
- add pages for orientation, first-step routing, power mapping, and no-reply escalation
- link these pages from the top-level README and docs index
- later decide whether MCP should expose a matching `start_here` tool family
