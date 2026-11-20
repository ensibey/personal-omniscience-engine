"""
Style drift evaluator for Personal Omniscience Engine.

Quantifies how closely a candidate LLM response matches the user's target StyleProfile
across sentence length, formality, bullet formatting, emoji usage, and language.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from style.analyzer import StyleProfile, analyze_text


@dataclass(frozen=True)
class StyleDriftReport:
    alignment_score: float
    sentence_length_delta: float
    formality_delta: float
    language_match: bool
    warnings: List[str] = field(default_factory=list)


def evaluate_style_drift(candidate_response: str, target_profile: StyleProfile) -> StyleDriftReport:
    """Measure alignment between a generated response and the user's corpus StyleProfile."""
    cand = analyze_text(candidate_response)
    warnings: List[str] = []

    sent_delta = abs(cand.avg_sentence_length - target_profile.avg_sentence_length)
    sent_sim = max(0.0, 1.0 - (sent_delta / 18.0))
    if sent_delta > 8.0:
        warnings.append(
            f"Sentence length drift: candidate={cand.avg_sentence_length:.1f}w vs target={target_profile.avg_sentence_length:.1f}w"
        )

    formality_delta = abs(cand.formality_score - target_profile.formality_score)
    formality_sim = max(0.0, 1.0 - formality_delta)
    if formality_delta > 0.35:
        warnings.append(
            f"Formality drift: candidate={cand.formality_score:.2f} vs target={target_profile.formality_score:.2f}"
        )

    bullet_delta = abs(cand.bullet_ratio - target_profile.bullet_ratio)
    bullet_sim = max(0.0, 1.0 - bullet_delta)

    emoji_penalty = 0.0
    if target_profile.emoji_density < 0.005 and cand.emoji_density > 0.01:
        emoji_penalty = 0.25
        warnings.append("Candidate injected emojis despite emoji-free target profile.")

    lang_match = cand.language_hint == target_profile.language_hint
    if not lang_match:
        warnings.append(
            f"Language mismatch: candidate='{cand.language_hint}' vs target='{target_profile.language_hint}'"
        )

    raw_score = (0.35 * sent_sim + 0.35 * formality_sim + 0.20 * bullet_sim + (0.10 if lang_match else 0.0)) - emoji_penalty
    alignment = round(max(0.0, min(1.0, raw_score)), 4)

    return StyleDriftReport(
        alignment_score=alignment,
        sentence_length_delta=round(sent_delta, 2),
        formality_delta=round(formality_delta, 3),
        language_match=lang_match,
        warnings=warnings,
    )
