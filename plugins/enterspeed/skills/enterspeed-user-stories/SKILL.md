---
name: enterspeed-user-stories
version: 1.0.0
description: Generate well-structured user stories for Enterspeed using the standard team template. Use when someone describes a feature, capability, or user role + goal and needs a formatted user story. Works from rough ideas or specific role+goal inputs.
---

# Enterspeed User Story Generator

Generates user stories in the Enterspeed standard format from a rough feature description or a specific user role + goal.

## Input

The user will provide one of:
- A **rough idea or feature description** (e.g. "we need a way to filter food items by allergens")
- A **specific user role + goal** (e.g. "As a developer, I want to query products by SKU")

Both are valid starting points. Work with whatever is given.

## Your Job

1. **Generate a complete user story draft immediately** — do not ask questions first.
2. **List your assumptions** clearly at the end, so the user knows what you inferred and can correct you.
3. Use the Enterspeed template below exactly — preserve all emoji headers, formatting, and checkboxes.

## The Template

```
### 🎯 User Story
**As a** [user role],
**I want** [capability],
**so that** [benefit].

---

### ✅ Acceptance Criteria
- [ ] [Testable outcome 1]
- [ ] [Testable outcome 2]
- [ ] [Edge case / error behavior]

---

### 🔒 Security
> Security considered — assessed as **low risk**. No auth, input validation, or data exposure concerns identified for this story.

---

### 🔧 Tech Notes (optional)
- [API endpoint, filters, or component reuse — leave blank if unknown]

---

### 📊 Success Criteria
- [What metric or behavior defines "done"?]

---

### 🎨 Design (if applicable)
- [Figma link / mockup reference — leave blank if not applicable]
```

## Section Rules

- **🎯 User Story** — Always included. If only a rough idea is given, infer a sensible user role.
- **✅ Acceptance Criteria** — Always included. Write at least 3 criteria: a happy path, an edge case, and an error/failure scenario.
- **🔒 Security** — Always included. For most stories, keep it simple: state that security was considered and assessed as low risk. Only escalate to a brief description of the specific risk if the feature involves authentication, mutations, sensitive data, or access control.
- **🔧 Tech Notes** — Optional. Include if the input mentions technical details (endpoints, components, filters). Otherwise leave the section with a placeholder.
- **📊 Success Criteria** — Always included. Write a concrete, measurable definition of done — not vague language like "works correctly".
- **🎨 Design** — Optional. Include only if the feature clearly involves UI. Otherwise omit entirely.

## Assumptions Block

After the story, add a section like this:

---

### 💭 Assumptions Made
- [Assumption 1 — what you inferred and why]
- [Assumption 2]
- ...

*If any of these are wrong, let me know and I'll revise the story.*

## Enterspeed Context

Enterspeed is a headless CMS and data ingestion platform. Common user roles include:
- **Engineer** — integrating APIs, building schemas, writing ingest code
- **Content editor** — managing and publishing content
- **DevOps engineer** — managing environments, API keys, access
- **Data engineer** — setting up data pipelines and transformations

Keep acceptance criteria and tech notes consistent with this product domain when making inferences.

## Tone & Style

- Be specific and testable — avoid vague criteria like "it should work" or "it should be fast"
- Use present tense in acceptance criteria: "The system returns..." not "The system will return..."
- Keep language concise and professional
