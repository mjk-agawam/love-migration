# Adversary: Salesforce Build Verification System

**Date:** 2026-06-21  
**Status:** Approved design, pending implementation  
**Customer context:** Salesforce demo org customization (Service Pros and future engagements)

---

## 1. Architecture

The adversary system uses a three-layer architecture: a PostToolCall hook, an adversary skill, and orchestrator instructions in CLAUDE.md.

```
Primary builder agent
       |
       | (every SF tool call)
       v
PostToolCall hook          ← harness-enforced, fires mechanically
       |
       | writes .claude/adversary-pending.json
       v
Adversary skill            ← invoked at turn start when marker present
       |
       | PASS / FAIL verdict
       v
Orchestrator (CLAUDE.md)   ← reads verdict, proceeds or retries
```

The hook is the reliability guarantee. It fires on every matching tool call regardless of session length, context size, or Claude's attention. CLAUDE.md instructions are attention-dependent and would be skipped in long sessions. The hook cannot be.

**Domain configuration:** The system defaults to Salesforce mode. The active domain is stored in `.claude/adversary-config.json`. At session start, if no domain is set, it defaults to `salesforce`. To switch domains for a session, tell Claude which domain to use (e.g., "use the general domain for this session") or set it in the config file. Auto-detection also applies: if a tool call involves `.cls`, `.trigger`, `.object`, `.flow`, `sf deploy`, `sf retrieve`, or similar Salesforce artifacts, the Salesforce module activates regardless of the config setting.

---

## 2. Components

### 2a. PostToolCall Hook

**Trigger condition:** Any tool call that matches Salesforce metadata or code patterns:
- `Edit` or `Write` on files with extensions: `.cls`, `.trigger`, `.object`, `.field`, `.flow`, `.layout`, `.permissionset`, `.profile`, `.page`, `.component`
- `Bash` commands containing: `sf deploy`, `sf retrieve`, `sfdx force:source:deploy`, `sfdx force:source:retrieve`, `sfdx force:apex`, `sf apex`
- `Bash` commands accessing Salesforce CLI or org-related paths

**On match:** The hook writes `.claude/adversary-pending.json` with:
```json
{
  "tool": "<tool name>",
  "target": "<file or command>",
  "timestamp": "<ISO timestamp>",
  "step_description": "<brief description of what just happened>",
  "domain": "salesforce",
  "attempt": 1
}
```

**On no match:** The hook does nothing. No file is written. No overhead.

### 2b. Adversary Skill

The adversary is a subagent invoked by the orchestrator whenever `.claude/adversary-pending.json` is present at the start of a turn.

**Inputs:** The pending marker file plus context from the primary agent's last output (files modified, commands run).

**Verification steps the adversary performs:**

1. **Shortcut detection.** Did the primary agent implement the change in a way that produces the right output but bypasses Salesforce best practices? Examples: hardcoding IDs instead of querying, using DML inside loops, skipping governor limit considerations, using deprecated APIs.

2. **Documentation verification.** Fetch the relevant Salesforce documentation for the action taken. Sources in priority order:
   - `developer.salesforce.com` (primary: Apex Developer Guide, Metadata API, Flow Builder, etc.)
   - `help.salesforce.com` (secondary: admin/config guides)
   
   The adversary must cite the specific URL and section it used to verify the implementation. If documentation cannot be found or fetched, this is a hard stop (see Section 4).

3. **Implementation correctness.** Does the code or config match what the documentation says? Flag any deviation.

**Output:** A verdict written to `.claude/adversary-verdict.json`:
```json
{
  "verdict": "PASS" | "FAIL",
  "issues": ["<issue 1>", "<issue 2>"],
  "citations": [
    {
      "url": "https://developer.salesforce.com/...",
      "section": "<section title>",
      "finding": "<what was verified or what failed>"
    }
  ],
  "attempt": 1
}
```

### 2c. Retry Counter and Escalation

The attempt counter lives in `.claude/adversary-pending.json`. On FAIL:
- Increment `attempt`
- Clear the verdict file
- Instruct the primary agent to retry the failed step

Cap: 3 attempts. On the third FAIL, escalate to Mike with a hard stop (see Section 4).

On PASS:
- Delete `.claude/adversary-pending.json` and `.claude/adversary-verdict.json`
- Primary agent proceeds to the next step

---

## 3. Data Flow

**Normal (PASS) path:**

1. Primary agent executes a Salesforce tool call.
2. PostToolCall hook detects the match, writes `adversary-pending.json` with `attempt: 1`.
3. At the start of the next turn, the orchestrator (CLAUDE.md) detects the marker file.
4. Orchestrator invokes the adversary skill.
5. Adversary fetches live Salesforce documentation, verifies the step, writes `adversary-verdict.json` with `verdict: PASS`.
6. Orchestrator reads PASS, deletes both JSON files, proceeds.

**Retry (FAIL, attempts 1-2) path:**

1-4. Same as above.
5. Adversary writes `adversary-verdict.json` with `verdict: FAIL` and lists issues.
6. Orchestrator reads FAIL, increments `attempt` in `adversary-pending.json`, instructs primary agent to fix and retry.
7. Primary agent retries the step. Hook fires again. Loop repeats from step 3.

**Escalation (FAIL, attempt 3) path:**

1-4. Same as above.
5. Adversary writes `adversary-verdict.json` with `verdict: FAIL`.
6. Orchestrator reads FAIL on attempt 3. Hard stop (see Section 4).

---

## 4. Error Handling

All failures result in a visible hard stop in the UI. No log files. No silent fallbacks. No UNVERIFIED verdicts that let work continue.

**Case 1: Adversary can't find documentation**

Display to user:
```
ADVERSARY STOP — Documentation Not Found

The adversary could not locate Salesforce documentation for the step that was just completed.

What was being verified: <step description from adversary-pending.json>
What was searched: developer.salesforce.com, help.salesforce.com
Search query used: <query>

Work has stopped. Options:
1. Provide the documentation URL manually and I will re-run verification.
2. Skip verification for this step (type: skip adversary).
3. End the session and investigate.
```

**Case 2: Adversary skill unavailable or fails to execute**

Display to user:
```
ADVERSARY STOP — Verification Unavailable

The adversary skill could not run. The step that just completed has not been verified.

What was being verified: <step description from adversary-pending.json>
Error: <error message from adversary execution>

Work has stopped. Options:
1. Retry adversary verification (type: retry adversary).
2. Skip verification for this step (type: skip adversary).
3. End the session and investigate.
```

**Case 3: Three failed attempts on a step**

Display to user:
```
ADVERSARY STOP — Step Failed 3 Times

The primary agent attempted this step 3 times and the adversary found issues each time.

Step: <step description>
Issues found on last attempt:
- <issue 1>
- <issue 2>

Documentation consulted:
- <citation URL and section>

Work has stopped. Review the issues above and decide how to proceed.
Options:
1. Provide guidance and I will attempt a different approach (describe it).
2. Skip this step (type: skip step).
3. End the session.
```

**Strict mode toggle:** A flag `adversary_strict: true` in `.claude/adversary-config.json` controls this behavior. When `true` (default), all three cases above are hard stops. When `false`, cases 1 and 2 produce a warning and allow work to continue while logging the unverified step. Case 3 (three failures) always stops regardless of mode. To toggle: update the config file or tell Claude "set adversary to warn mode" / "set adversary to strict mode."

---

## 5. Testing

**Hook detection accuracy**

For each rule in the hook's trigger condition:
- Confirm it fires on a file edit matching each Salesforce extension.
- Confirm it fires on a Bash command matching each SF CLI pattern.
- Confirm it does NOT fire on non-SF tool calls (Python edits, README updates, git commands).

**Adversary verdict quality**

Test with three planted scenarios:
1. A correct Apex class with proper bulkification. Expect PASS with citation.
2. An Apex class with DML inside a loop. Expect FAIL citing "Bulk Apex Triggers" doc.
3. A Flow with a known best-practice violation. Expect FAIL with citation.

**Retry loop mechanics**

Simulate three consecutive FAILs on a single step:
- Confirm `attempt` counter increments correctly in the JSON file.
- Confirm the escalation hard stop fires on attempt 3, not attempt 2 or 4.
- Confirm both JSON files are deleted after a PASS.

**Hard stop display**

Trigger each of the three error cases manually:
- Block network access during adversary doc fetch → Case 1.
- Break the adversary skill invocation → Case 2.
- Inject three consecutive FAIL verdicts → Case 3.
- Confirm each produces the correct UI message with no silent fallback.

---

## 6. Domain Configuration Reference

| Action | How |
|---|---|
| Check current domain | Read `.claude/adversary-config.json` |
| Switch to general domain for session | Tell Claude: "use general domain" |
| Switch back to Salesforce | Tell Claude: "use Salesforce domain" or just start working with SF files |
| Permanently change default | Edit `.claude/adversary-config.json` `"default_domain": "salesforce"` |
| Override auto-detection | Set `"force_domain": "general"` in config |

Auto-detection takes precedence over the config setting when Salesforce file types or CLI commands are detected.

**General domain (future):** When `domain: general` is active, the adversary performs shortcut detection and web documentation verification using general programming and configuration best practices rather than Salesforce-specific sources. The sources, verification criteria, and citations differ; the architecture (hook, marker file, retry loop, hard stops) is identical.
