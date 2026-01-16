TODO: Consolidate architecture docs and relocate one-off tests

Goal
----
Merge `factory_ui_simulator/ARCHITECTURE_MQTT.md` and `TEMPLATE_DRIVEN_ARCHITECTURE.md` into the canonical `docs/ARCHITECTURE.md`, clean up overlapping content, update references, and move one-off test scripts into `tests/` (or archive them) so documentation is single-source-of-truth and tests are CI-friendly.

High-level steps
----------------
- Create this `TODO.md` as the migration plan (you are reading it).
- Produce a draft merged doc at `docs/ARCHITECTURE_MERGE_DRAFT.md` (staging area).
- Reconcile conflicts and decide canonical module names (recommendation: `shared/template_driven_test_generator.py`).
- Replace `docs/ARCHITECTURE.md` with the cleaned consolidated content.
- Archive originals to `docs/archive/` (keep history).
- Convert one-off test scripts to pytest under `tests/` and add a minimal test runner or CI instructions.
- Triage in-code `# TODO` items: fix trivial ones, create issues for larger work, and list issue IDs here.
- Run tests and smoke checks; document any follow-ups.

Actionable subtasks (ordered)
-----------------------------
1) Draft merge
   - File: `docs/ARCHITECTURE_MERGE_DRAFT.md`
   - Content: combine `docs/ARCHITECTURE.md`, `factory_ui_simulator/ARCHITECTURE_MQTT.md`, and `TEMPLATE_DRIVEN_ARCHITECTURE.md` preserving authoritative examples (MQTT topics, REST endpoints, generator internals).
   - Acceptance: Draft exists and contains merged sections: Overview, Layered Design, MQTT runtime flow, UI Simulator (endpoints + managers), Template-Driven Generator details, Test Case Generation flow.

2) Decide canonical generator and update references
   - Decide module: recommended `shared/template_driven_test_generator.py`.
   - Update all docs to reference the canonical name; leave note where old names are mentioned.
   - Acceptance: mapping recorded in `TODO.md` and draft updated.

3) Finalize and replace
   - Replace `docs/ARCHITECTURE.md` with the cleaned draft.
   - Add a short changelog at top of `docs/ARCHITECTURE.md` linking to archived originals.
   - Acceptance: `docs/ARCHITECTURE.md` contains consolidated content and points to `docs/archive/`.

4) Archive originals
   - Move `factory_ui_simulator/ARCHITECTURE_MQTT.md` and `TEMPLATE_DRIVEN_ARCHITECTURE.md` → `docs/archive/`.
   - Acceptance: archived files present and original locations either removed or contain short redirect notes.

5) Tests
   - Convert `test_template_driven.py`, `test_generalization.py`, and `verify_templates.py` into pytest tests under `tests/` (or move to `docs/archive/` if deprecated).
   - Add `tests/__init__.py` if required.
   - Acceptance: `pytest -q` runs the new tests (they may be smoke tests asserting non-empty outputs).

6) Code TODOs
   - Scan repo for `# TODO` comments; for small fixes apply patch, for larger items open issues and add references in this file.
   - Example: `tools/factory_generator.py` contains `# TODO: Safely evaluate formula` — triage and open issue if not trivial.

7) Update cross-references
   - Update `README.md`, `docs/QUICK_REFERENCE.md`, and other docs to point to the consolidated `docs/ARCHITECTURE.md`.

8) Verification
   - Run smoke tests and basic `docker compose up` steps for a sample generated factory (e.g., `generated-factories/tshirt-factory-001`).
   - Document any failing steps and next actions in `TODO.md`.

Acceptance criteria (summary)
----------------------------
- `docs/ARCHITECTURE.md` is the canonical architecture doc and includes the UI Simulator MQTT/REST details and the Template-Driven generator info.
- Originals archived in `docs/archive/`.
- One-off test scripts converted to `tests/` and runnable with `pytest` (or clearly archived).
- All README and internal doc links updated to the new canonical doc.
- All repo `# TODO` comments are either fixed or have an issue opened and referenced here.

Owner / Next steps
------------------
- Owner: repo maintainer (assign as appropriate).
- Pilot: run the migration for `tshirt-factory-001` first.
- After review, I will proceed to the next task: create `docs/ARCHITECTURE_MERGE_DRAFT.md`.

Notes
-----
- This TODO is intentionally prescriptive to make the migration reviewable in a small PR. If you want me to continue, approve and I will proceed to the next task: create `docs/ARCHITECTURE_MERGE_DRAFT.md`.
