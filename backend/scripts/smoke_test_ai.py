"""End-to-end smoke test for the provider-agnostic AI layer.

Exercises each task path (parsing, inference, extraction, rerank) plus
embeddings, against whatever providers are configured in .env.
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
import traceback


async def test_routes() -> None:
    from app.ai.providers import ai_manager

    print("─── Configured routes ─" + "─" * 40)
    print(json.dumps(ai_manager.describe_routes(), indent=2))
    print("\n─── Provider health ─" + "─" * 40)
    health = await ai_manager.health()
    print(json.dumps(health, indent=2))


async def test_parse_query() -> None:
    print("\n─── task=parsing ──────────────────────────────")
    from app.ai.pipelines.search import _parse_query

    t = time.perf_counter()
    parsed = await _parse_query(
        "Find a senior React engineer in Bangalore with at least 3 years of WebSocket experience"
    )
    elapsed = int((time.perf_counter() - t) * 1000)
    print(f"  ok in {elapsed}ms")
    print("  parsed:", json.dumps(parsed, indent=2))


async def test_inference() -> None:
    print("\n─── task=inference ────────────────────────────")
    from app.ai.pipelines.inference import run_inference
    from app.schemas.extraction import ExtractedSkill

    skills = [
        ExtractedSkill(name="Next.js", proficiency="expert", years=4.0, confidence=0.95),
        ExtractedSkill(name="TypeScript", proficiency="expert", years=4.0, confidence=0.95),
        ExtractedSkill(name="Socket.IO", proficiency="intermediate", years=2.0, confidence=0.85),
    ]
    t = time.perf_counter()
    inferred = await run_inference(skills)
    elapsed = int((time.perf_counter() - t) * 1000)
    print(f"  ok in {elapsed}ms — {len(inferred)} inferred skills")
    for i in inferred[:6]:
        print(f"    • {i['name']:<24} conf={i['confidence']}  ({i.get('reasoning', '')[:60]})")


async def test_extraction() -> None:
    print("\n─── task=extraction ───────────────────────────")
    from app.ai.pipelines.extraction import _call_extraction

    sample_resume = """\
Jane Doe — Senior Frontend Engineer
Location: Bangalore, India
Email: jane.doe@example.com

EXPERIENCE
2020–2024  Acme Corp  —  Senior React Engineer
- Led a team of 4 building a live trading dashboard with React + WebSocket feeds
- 5+ years of TypeScript across multiple production apps; 6 years of React total
- Owned Next.js migration of the marketing site (3 years on Next.js)

PROJECTS
- RealTrade dashboard (React, WebSocket, TypeScript, Redux) — 50K DAU
"""
    t = time.perf_counter()
    profile = await _call_extraction(sample_resume, canonical_skills=[])
    elapsed = int((time.perf_counter() - t) * 1000)
    print(f"  ok in {elapsed}ms")
    print(f"    name={profile.name!r}  location={profile.location!r}")
    print(f"    {len(profile.skills)} skills, {len(profile.projects)} projects")
    for s in profile.skills[:6]:
        print(f"      • {s.name:<14}  {s.proficiency:<12} {s.years or '?'} yrs")


async def test_embedding() -> None:
    print("\n─── embedding (Voyage) ────────────────────────")
    from app.ai.providers import ai_manager

    t = time.perf_counter()
    vec = await ai_manager.embed_single("senior React engineer with WebSocket experience")
    elapsed = int((time.perf_counter() - t) * 1000)
    print(f"  ok in {elapsed}ms  dim={len(vec)}  first5={[round(x, 4) for x in vec[:5]]}")


async def main() -> int:
    failures = 0
    for label, fn in [
        ("routes/health", test_routes),
        ("parse_query", test_parse_query),
        ("inference", test_inference),
        ("extraction", test_extraction),
        ("embedding", test_embedding),
    ]:
        try:
            await fn()
        except Exception:
            failures += 1
            print(f"\n!!! {label} FAILED")
            traceback.print_exc()
    print("\n" + "═" * 60)
    if failures:
        print(f"{failures} test(s) failed")
        return 1
    print("all smoke tests passed ✓")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
