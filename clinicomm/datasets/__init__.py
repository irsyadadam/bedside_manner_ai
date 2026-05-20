"""External-dataset adapters for Phase 13 evaluation.

Each adapter produces ExternalTranscript records from a public source:
  - primock57   : 57 mock primary-care consultations (Babylon)
  - mts_dialog  : 1,700 short clinical conversations with section-labeled
                  reference summaries (MEDIQA-Chat 2023)
  - aci_bench   : 207 doctor-patient encounters paired with SOAP notes

The adapters are lazy — `download()` is called on first use, files
land under the path configured in pipeline.yaml (`datasets.cache_dir`)
or `./db/external/<dataset>/` by default.
"""
from __future__ import annotations

from clinicomm.datasets.base import ExternalTranscript, Turn

__all__ = ["ExternalTranscript", "Turn"]
