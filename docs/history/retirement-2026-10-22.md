# 2026-10-22 case retirement

The ended application cases and experiments have been removed from the current tree. Complete archives belong to private source history; this public snapshot includes neither those objects nor their recovery commands. Historical v0.4.0 carried only a curated Swift sample, not the complete archives.

## Research record

- `projects/ablation`: the earlier ten-check mechanism comparison scored the
  baseline and simplified candidate 100/100. It selected removal of a duplicate
  `begin` count check because later verification and resume transitions enforced
  the limit. These checks do not estimate model or product quality.
- `projects/business-ablation`: four single-run arms each passed 12 public cases
  and two confirmed holdouts; one planned holdout remained unavailable. It found
  no pass-rate gain, with N=1 per arm.
- `projects/exploration-ablation`: 02/03 did not yield a comparable strategy
  result, 04 added zero semantic atoms in both arms, and 05/06 recorded real
  strategy changes and actions without a matched control. This does not establish
  exploration efficiency or reconstruction-quality gains.
- `projects/frontend-quality-ablation`: both arms passed 40/40 checks, while the
  feedback arm had larger image differences. The initial metric was saturated;
  N=1 does not show that frontend feedback is generally ineffective.
- `projects/model-pipeline`: run01 failed at a Stop-deduplication defect; run02
  completed 11 attempts across two sessions with 12/12 reference and candidate
  cases. This is host-pipeline feasibility evidence, not novel discovery or a
  business improvement estimate.
- `projects/rebuild-mechanisms`: fixed checks scored 36/36 for full, 35/36 without
  behavior progress, 33/36 without Stop feedback, and 35/36 without supplemental
  discovery. The later ordered replay matched these results. This shows which
  checks depended on those mechanisms, not their independent effect on products.

The synthetic `projects/dream-rsi-check` remains a framework fixture and is not
part of this retirement. Core `capabilities/`, `runtime/`, and `workflows/` remain
framework-owned. No experiment result above certifies a product as complete or
authorizes restarting a finished case.
