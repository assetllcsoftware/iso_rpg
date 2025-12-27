# Tech Debt Tracker

When you're unsure about something, don't block. Document it here and keep moving.

---

## Format

```markdown
### [Short Title]
- **Date:** YYYY-MM-DD
- **File(s):** path/to/file.py
- **Issue:** What's the uncertainty?
- **Current Solution:** What did we do for now?
- **Revisit When:** When should we come back to this?
- **Priority:** Low / Medium / High
```

---

## Open Items

### Spell Cooldowns: Per-Entity or Per-Spell?
- **Date:** 2024-12-25
- **File(s):** Not yet implemented
- **Issue:** Should cooldowns be tracked per-entity (each character has own cooldowns) or globally per-spell (casting fireball puts it on CD for everyone)?
- **Current Solution:** Assuming per-entity (like original game)
- **Revisit When:** Implementing MagicProcessor
- **Priority:** Medium

### Save/Load with ECS
- **Date:** 2024-12-25
- **File(s):** Not yet implemented
- **Issue:** How to serialize Esper world? Walk all entities and components? Snapshot?
- **Current Solution:** TBD
- **Revisit When:** Implementing save system
- **Priority:** Low (can play without saves during dev)

---

## Resolved Items

(Move items here when resolved)

<!-- 
### Example Resolved Item
- **Date:** 2024-12-25
- **Resolution:** We decided to do X because Y
- **Resolved By:** [commit hash or description]
-->

