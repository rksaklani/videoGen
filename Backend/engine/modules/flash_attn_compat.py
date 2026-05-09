"""
flash_attn is optional. Hunyuan modules call ``flash_attn_varlen_func`` from here so the
API server can start without compiling flash-attn (fallback is slower but correct for inference).
"""
from __future__ import annotations

import torch
import torch.nn.functional as F
from loguru import logger

try:
    from flash_attn.flash_attn_interface import flash_attn_varlen_func as _native_flash_attn_varlen
except ImportError:
    _native_flash_attn_varlen = None

_fallback_logged = False


def _sdpa_varlen_fallback(
    q: torch.Tensor,
    k: torch.Tensor,
    v: torch.Tensor,
    cu_seqlens_q: torch.Tensor,
    cu_seqlens_kv: torch.Tensor,
    max_seqlen_q: int,
    max_seqlen_kv: int,
) -> torch.Tensor:
    cq = cu_seqlens_q.detach().cpu().tolist()
    ck = cu_seqlens_kv.detach().cpu().tolist()
    if len(cq) != len(ck):
        raise RuntimeError(
            f"cu_seqlens_q and cu_seqlens_kv lengths differ ({len(cq)} vs {len(ck)}); "
            "cannot run SDPA fallback."
        )
    out = torch.empty_like(q)
    for i in range(len(cq) - 1):
        sq, eq = cq[i], cq[i + 1]
        sk, ek = ck[i], ck[i + 1]
        qi = q[sq:eq]
        ki = k[sk:ek]
        vi = v[sk:ek]
        a = qi.transpose(0, 1).unsqueeze(0).contiguous()
        b = ki.transpose(0, 1).unsqueeze(0).contiguous()
        c = vi.transpose(0, 1).unsqueeze(0).contiguous()
        oi = F.scaled_dot_product_attention(a, b, c, is_causal=False)
        out[sq:eq] = oi.squeeze(0).transpose(0, 1).to(dtype=out.dtype)
    _ = max_seqlen_q, max_seqlen_kv  # API parity with flash_attn
    return out


def flash_attn_varlen_func(q, k, v, cu_seqlens_q, cu_seqlens_kv, max_seqlen_q, max_seqlen_kv):
    if _native_flash_attn_varlen is not None:
        return _native_flash_attn_varlen(
            q, k, v, cu_seqlens_q, cu_seqlens_kv, max_seqlen_q, max_seqlen_kv
        )
    global _fallback_logged
    if not _fallback_logged:
        logger.warning(
            "flash_attn is not installed — using PyTorch SDPA per packed segment (slower). "
            "For best performance install matching wheels: "
            "https://github.com/Dao-AILab/flash-attention"
        )
        _fallback_logged = True
    return _sdpa_varlen_fallback(
        q, k, v, cu_seqlens_q, cu_seqlens_kv, max_seqlen_q, max_seqlen_kv
    )
