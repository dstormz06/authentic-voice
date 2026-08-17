# Skill Benchmark: authentic-voice

> **Read this first.** This file is a retained v1 artifact and its numbers are not
> trustworthy. The header claimed three runs per configuration, but only `run-1` exists on
> disk for each cell, so the reported spread is across the three *evals*, not across repeats
> of one eval. Time and token figures are all zero because the harness never recorded them,
> and the model fields were never filled in. The pass rates below come from a grader whose
> evidence strings are template constants ("cue found", "none").
>
> For a measurement that can be reproduced, run `tools/av_lint.py` over the stored outputs.
> That comparison, and its limits, are documented in the README under
> "Measured effect on the sample corpus". Kept here for provenance only.

**Model**: not recorded
**Date**: 2026-08-16T10:52:51Z
**Evals**: 1, 2, 3 (1 run recorded per configuration, despite the claim below)

## Summary

| Metric | With Skill | Without Skill | Delta |
|--------|------------|---------------|-------|
| Pass Rate | 100% ± 0% | 75% ± 25% | +0.25 |
| Time | 0.0s ± 0.0s | 0.0s ± 0.0s | +0.0s |
| Tokens | 0 ± 0 | 0 ± 0 | +0 |