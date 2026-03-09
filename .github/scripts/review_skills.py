import os
import time
import requests
import anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def call_claude(prompt, retries=3, delay=10):
    for attempt in range(retries):
        try:
            return client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
        except anthropic.APIStatusError as e:
            if e.status_code == 529 and attempt < retries - 1:
                print(f"API overloaded, retrying in {delay}s... (attempt {attempt + 1}/{retries})")
                time.sleep(delay)
            else:
                raise

changed_skills = [s for s in os.environ.get("CHANGED_SKILLS", "").strip().split("\n") if s]
version_bumped = os.environ.get("VERSION_BUMPED", "false") == "true"

reviews = []

for skill_path in changed_skills:
    if not os.path.exists(skill_path):
        continue

    with open(skill_path) as f:
        content = f.read()

    skill_name = skill_path.split("/")[-2]
    skill_dir = os.path.dirname(skill_path)

    # Include any companion scripts from the scripts/ subdirectory
    scripts_dir = os.path.join(skill_dir, "scripts")
    scripts_content = ""
    if os.path.isdir(scripts_dir):
        for script_file in sorted(os.listdir(scripts_dir)):
            script_path = os.path.join(scripts_dir, script_file)
            if os.path.isfile(script_path):
                with open(script_path) as f:
                    scripts_content += f"\n\n### scripts/{script_file}\n```\n{f.read()}\n```"

    prompt = (
        f"Review this Claude Code skill file and give concise, actionable feedback.\n\n"
        f"Skill: {skill_name}\n"
        f"File: {skill_path}\n\n"
        f"Content:\n{content}\n"
        + (f"\nCompanion scripts (in the skill's scripts/ subdirectory):{scripts_content}\n" if scripts_content else "")
        + f"\nConventions used in this plugin:\n"
        f"- Skills are versioned via git — there is no `version` field in frontmatter. Do not flag its absence.\n"
        f"- Skills may reference companion scripts via `<skill-path>/scripts/<file>`. `<skill-path>` is the directory containing the SKILL.md file. This is the established pattern — do not flag it as unclear.\n"
        f"- Skills reference sibling skills by name (e.g. **gitflow-prerequisites**). This is valid inter-skill referencing — do not flag it as missing a call mechanism.\n\n"
        f"Check for:\n"
        f"1. Frontmatter — are `name` and `description` present?\n"
        f"2. Description quality — is it specific enough for Claude to know exactly when to trigger this skill? Does it include concrete trigger phrases or examples?\n"
        f"3. Skill body — is the instruction clear, focused, and actionable? Does it give Claude enough context to do its job?\n"
        f"4. Scope — is this skill focused on one thing, or trying to do too much?\n\n"
        f"Format your response as:\n"
        f"- A brief summary (1-2 sentences)\n"
        f"- Bullet points for any issues found (be specific)\n"
        f"- A clear LGTM or NEEDS WORK verdict at the end\n\n"
        f"Be constructive and concise. If the skill is good, say so briefly."
    )

    response = call_claude(prompt)

    reviews.append(f"### `{skill_name}`\n\n{response.content[0].text}")

body = "## 🤖 Skill Review\n\n"

if not version_bumped:
    body += "> ⚠️ **Version not bumped** — remember to increment the version in `.claude-plugin/marketplace.json`\n\n"

if reviews:
    body += "\n\n---\n\n".join(reviews)
else:
    body += "_No skill files changed._"

headers = {
    "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
    "Accept": "application/vnd.github+json"
}
url = f"https://api.github.com/repos/{os.environ['REPO']}/issues/{os.environ['PR_NUMBER']}/comments"
requests.post(url, headers=headers, json={"body": body})

print("Review posted.")
