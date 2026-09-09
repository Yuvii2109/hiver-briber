"""Build sentence embeddings ONCE, commit them, so graders never need torch.

torch + sentence-transformers is a ~2GB install and several minutes of model
download. That cannot sit on the critical path of a 15-minute reproduction. So
this module is developer-only: it writes float16 vectors to artifacts/, which are
committed and loaded by numpy alone at eval time.
"""
from __future__ import annotations
import numpy as np

MODEL = "sentence-transformers/all-MiniLM-L6-v2"   # 384-dim, pinned


def encode(texts: list[str], model_name: str = MODEL, batch_size: int = 256) -> np.ndarray:
    from sentence_transformers import SentenceTransformer
    import torch
    torch.manual_seed(0)
    m = SentenceTransformer(model_name, device="cpu")
    v = m.encode(list(texts), batch_size=batch_size, convert_to_numpy=True,
                 normalize_embeddings=True, show_progress_bar=True)
    return v.astype(np.float16)          # 30k x 384 fp16 = 23MB, git-friendly
