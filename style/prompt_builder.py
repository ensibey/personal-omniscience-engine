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

    avg = profile.avg_sentence_length
    if avg < 8:
        bullets.append("- Kısa ve öz cümleler kur; tek fikirde kal.")
    elif avg < 14:
        bullets.append("- Orta uzunlukta cümleler kullan; sade ve anlaşılır ol.")
    else:
        bullets.append("- Daha geniş açıklamalar yapabilirsin; ayrıntı vermekten çekinme.")

    if profile.emoji_density > 0.01:
        bullets.append("- Uygun yerlerde ölçülü emoji kullan.")
    else:
        bullets.append("- Emoji kullanma; sade ve metin odaklı kal.")

    if profile.bullet_ratio > 0.15:
        bullets.append("- Bilgileri madde listesi (- veya 1. 2. 3.) olarak sun.")
    else:
        bullets.append("- Paragraf biçiminde yaz; listeleri yalnızca gerektiğinde kullan.")

    if profile.heading_ratio > 0.03:
        bullets.append("- Uzun cevaplarda Markdown başlıkları (## Başlık) kullan.")

    if profile.uses_bold:
        bullets.append("- **Anahtar terimleri** veya önemli kavramları kalın yap.")

    if profile.uses_code_blocks:
        bullets.append("- Kod veya teknik içerik varsa ```kod bloğu``` kullan.")

    if profile.sample_sentences:
        excerpts = " | ".join(profile.sample_sentences[:3])
        bullets.append(f"- Kullanıcının yazım tonuna örnekler: {excerpts[:300]}")

    return bullets
