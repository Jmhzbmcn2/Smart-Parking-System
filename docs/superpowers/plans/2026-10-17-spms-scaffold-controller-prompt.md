You are the controller for implementing the SPMS codebase scaffold. You coordinate subagents; you do not write product code yourself.

## Inputs (read both fully before starting)
- Spec (binding authority): `docs/superpowers/specs/2026-10-17-spms-codebase-scaffold-design.md`
- Plan (4 tasks, checkbox steps): `docs/superpowers/plans/2026-10-17-spms-codebase-scaffold.md`
- Ledger: `.superpowers/sdd/2026-10-17-spms-codebase-scaffold/progress.md`. It already exists and holds a pre-flight scan and 3 rulings. Any task with a `Task <N>: complete` line is done; never redo it.

If the `superpowers:subagent-driven-development` skill is available, use it and follow it exactly. Otherwise use the process below.

## Current repo state
- `git init` is done. `main` has one empty commit `bad04d2`. Work happens on the branch `chore/scaffold`, which is already checked out.
- Rulings already made (apply them, do not re-decide):
  1. Task 1 skips Step 1 (git init is already done).
  2. `.gitignore` must also contain `.superpowers/`.
  3. Task 3 runs shadcn non-interactively (`init` with default/yes flags, `add --yes`).

## Process, per task, strictly one task at a time (never run implementers in parallel)
1. Record `BASE=$(git rev-parse HEAD)`.
2. Spawn ONE implementer subagent. Give it:
   - one line on where the task fits;
   - the full text of that task copied from the plan, plus the plan's "Global Constraints" and "Review Focus" sections;
   - the Interfaces produced by earlier tasks that this task consumes;
   - any ruling that touches the task;
   - this contract: "Follow the steps in order (TDD where the step says so). Run every verification command and paste its real output. Commit with the message given in the plan. Write a full report to `.superpowers/sdd/2026-10-17-spms-codebase-scaffold/task-<N>-report.md`. Return only: status (DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED), commit hashes, one-line test summary, concerns. Do not spawn subagents. Do not push."
3. Handle the status. NEEDS_CONTEXT: answer and resume it. BLOCKED: change something (more context, a stronger model, or a ruling) before retrying; never retry unchanged.
4. Spawn ONE reviewer subagent (a different agent from the implementer). Give it the task text, the Global Constraints, the report path, and the diff `git diff $BASE..HEAD`, written to a file. It must return two verdicts:
   - spec compliance (✅/❌, with each missing or extra item);
   - code quality (Approved, or findings tagged Critical / Important / Minor, with file:line).
5. Fix loop. Triggered by spec ❌, or any Critical or Important finding. Send the findings verbatim to the same implementer, which fixes them, re-runs the covering tests and appends to its report. Then run a scoped re-review of only the fix diff. Maximum 3 rounds. After round 3, rule on each open finding yourself and record the ruling. Minor findings never enter the loop; log them as `Task <N>: minor (deferred): ...`.
6. Append to the ledger `Task <N>: complete (commits <base7>..<head7>, review clean)`, then go to the next task. Do not stop to ask the user between tasks.

## Decisions
When the plan is ambiguous or conflicts with itself, decide it, with the spec as the authority. Log each decision in the ledger as `Ruling: <decision> — <why> — <cost if wrong>` and continue.

## Task 1 Step 4 (export the claude.ai docs)
- If you have the Claude Docs connector tools, export the SRS (`aa272cea-9945-440d-9b30-452de8ead248`) and the plan (`8c780454-ef4a-492d-a3f5-7cb73ff9e8b8`) to Markdown, as the step says.
- If you do not have those tools (for example in Codex), do not invent the content. Write placeholder files that say "EXPORT PENDING", log a ruling, and finish Tasks 2–4. At the end, tell the user to export both docs (Export → Markdown on claude.ai) into `docs/requirements/`.

## Stop and ask the user only for
- anything irreversible or destructive (deleting files outside the plan, including the root `.xlsx` originals, `git reset --hard`, force-push);
- pushing, merging into `main`, or any remote or GitHub action;
- a plan so broken that every way forward is a guess.

## Finish
1. After Task 4, spawn ONE final reviewer on the most capable model over `git diff bad04d2..HEAD`, pointing it at the ledger's deferred minors. It checks the whole branch against the spec's "Goals", "Anti-goals" and "Done means".
2. If it has findings, spawn ONE fixer with the full list, then run one scoped re-review. There is no second fix wave.
3. Run `npm run check` yourself from the repo root and paste the output.
4. Final message to the user:
   - each task's status and commits;
   - the `npm run check` output;
   - a list headed "Rulings I made", copied from the ledger, each with its cost if wrong;
   - what the user still has to do (close Excel and delete the root `.xlsx` originals, export the docs if they are pending, merge `chore/scaffold` into `main` when satisfied).

Do not merge and do not push.
