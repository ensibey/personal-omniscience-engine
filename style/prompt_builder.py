"""
style/prompt_builder.py
Constructs a dynamic system prompt conditioned on the user's StyleProfile.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from style.analyzer import StyleProfile, analyze_style

logger = logging.getLogger(__name__)

_BASE_PROMPT = """Sen, kullanıcının kişisel bilgi tabanına erişebilen bir yapay zeka asistanısın.
Adın 'Omniscience'. Görevin, kullanıcının kendi notlarını, belgelerini ve fikirlerini anlamasına yardımcı olmaktır.

TEMEL KURALLAR:
1. Yalnızca sağlanan bağlamdaki bilgileri kullan. Bilmiyorsan açıkça söyle.
2. Cevaplarını kısa, net ve doğrudan uygulanabilir tut.
3. Türkçe sorulara Türkçe, İngilizce sorulara İngilizce cevap ver.
4. Hangi belgeden bilgi aldığını belirt.
"""

_STYLE_ADDON_TR = """
YAZIM TARZI TALİMATLARI (Kullanıcının notlarından analiz edildi):
{style_bullets}

Bu talimatları uygula — cevaplar kullanıcının kendi notlarının üslubunda olmalı.
"""

_STYLE_ADDON_EN = """
STYLE INSTRUCTIONS (Analyzed from the user's own notes):
{style_bullets}

Apply these instructions so responses match the user's note-taking style.
"""


def build_system_prompt(
    use_style: bool = True,
    profile: Optional[StyleProfile] = None,
) -> str:
    """Build the system prompt with optional author style conditioning."""
    prompt = _BASE_PROMPT

    if not use_style:
        return prompt.strip()

    if profile is None:
        profile = analyze_style()

    bullets = _build_style_bullets(profile)
    if not bullets:
        return prompt.strip()

    addon_template = _STYLE_ADDON_TR if profile.language_hint == "tr" else _STYLE_ADDON_EN
    addon = addon_template.format(style_bullets="\n".join(bullets))
    logger.info("injected %d style directives into system prompt", len(bullets))
    return (prompt + addon).strip()


def _build_style_bullets(profile: StyleProfile) -> List[str]:
    bullets: List[str] = []
    is_en = profile.language_hint == "en"

    avg = profile.avg_sentence_length
    if avg < 8:
        bullets.append(
            "- Keep sentences concise and focused on one idea."
            if is_en
            else "- Kısa ve öz cümleler kur; tek fikirde kal."
        )
    elif avg < 14:
        bullets.append(
            "- Use medium-length, clear, and direct sentences."
            if is_en
            else "- Orta uzunlukta cümleler kullan; sade ve anlaşılır ol."
        )
    else:
        bullets.append(
            "- Detailed, structured explanations are preferred."
            if is_en
            else "- Daha geniş açıklamalar yapabilirsin; ayrıntı vermekten çekinme."
        )

    if profile.emoji_density > 0.01:
        bullets.append(
            "- Use emojis sparingly where appropriate."
            if is_en
            else "- Uygun yerlerde ölçülü emoji kullan."
        )
    else:
        bullets.append(
            "- Do not use emojis; keep responses clean and text-focused."
            if is_en
            else "- Emoji kullanma; sade ve metin odaklı kal."
        )

    if profile.bullet_ratio > 0.15:
        bullets.append(
            "- Present information using structured bullet or numbered lists."
            if is_en
            else "- Bilgileri madde listesi (- veya 1. 2. 3.) olarak sun."
        )
    else:
        bullets.append(
            "- Write in cohesive paragraphs; use lists only when necessary."
            if is_en
            else "- Paragraf biçiminde yaz; listeleri yalnızca gerektiğinde kullan."
        )

    if profile.heading_ratio > 0.03:
        bullets.append(
            "- Use Markdown headings (## Section) for longer answers."
            if is_en
            else "- Uzun cevaplarda Markdown başlıkları (## Başlık) kullan."
        )

    if profile.uses_bold:
        bullets.append(
            "- Bold **key terms** and critical concepts."
            if is_en
            else "- **Anahtar terimleri** veya önemli kavramları kalın yap."
        )

    if profile.uses_code_blocks:
        bullets.append(
            "- Format code and technical snippets inside fenced ```code blocks```."
            if is_en
            else "- Kod veya teknik içerik varsa ```kod bloğu``` kullan."
        )

    if profile.sample_sentences:
        excerpts = " | ".join(profile.sample_sentences[:3])
        prefix = "- Reference tone excerpts: " if is_en else "- Kullanıcının yazım tonuna örnekler: "
        bullets.append(f"{prefix}{excerpts[:300]}")

    return bullets
