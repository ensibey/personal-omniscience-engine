"""
style/prompt_builder.py
StyleProfile'a bakarak dinamik LLM sistem prompt'u üretir.
"""

from __future__ import annotations

import logging
from typing import Optional

from style.analyzer import StyleProfile, analyze_style

logger = logging.getLogger(__name__)

_BASE_PROMPT = """Sen, kullanıcının kişisel bilgi tabanına erişebilen bir yapay zeka asistanısın.
Adın 'Omniscience'. Görevin, kullanıcının kendi notlarını, belgelerini ve fikirlerini anlamasına yardımcı olmaktır.

TEMEL KURALLAR:
1. Yalnızca sağlanan bağlamdaki bilgileri kullan. Bilmiyorsan açıkça söyle.
2. Cevaplarını kısa, net ve anında kullanılabilir tut.
3. Türkçe sorulara Türkçe, İngilizce sorulara İngilizce cevap ver.
4. Kaynak göster: hangi belgeden aldığını belirt.
"""

_STYLE_ADDON_TR = """
YAZIM TARZI TALİMATLARI (Kullanıcının notlarından analiz edildi):
{style_bullets}

Bu talimatları uygula — kullanıcı sanki kendi notlarını okuyor gibi hissetmeli.
"""

_STYLE_ADDON_EN = """
STYLE INSTRUCTIONS (Analyzed from the user's own notes):
{style_bullets}

Apply these — the answers should feel like reading their own notes.
"""


def build_system_prompt(
    use_style: bool = True,
    profile: Optional[StyleProfile] = None,
) -> str:
    """
    Sistem prompt'unu oluşturur.

    Args:
        use_style: Yazım tarzı taklidi aktif mi?
        profile: Dışarıdan verilmiş StyleProfile (None → otomatik analiz).

    Returns:
        LLM'e gönderilecek sistem prompt string'i.
    """
    prompt = _BASE_PROMPT

    if not use_style:
        return prompt.strip()

    if profile is None:
        profile = analyze_style()

    bullets = _build_style_bullets(profile)

    if not bullets:
        logger.debug("Stil profili boş; standart prompt kullanılıyor.")
        return prompt.strip()

    addon_template = _STYLE_ADDON_TR if profile.language_hint == "tr" else _STYLE_ADDON_EN
    addon = addon_template.format(style_bullets="\n".join(bullets))
    prompt = prompt + addon

    logger.info(f"🎨 Stil direktifleri eklendi: {len(bullets)} madde.")
    return prompt.strip()


def _build_style_bullets(profile: StyleProfile) -> list[str]:
    """StyleProfile'dan insan-okunabilir direktifler listesi üretir."""
    bullets = []

    # ── Cümle uzunluğu ─────────────────────────────────────────────────────────
    avg = profile.avg_sentence_length
    if avg < 8:
        bullets.append("- Çok kısa ve öz cümleler kur; tek fikirde kal.")
    elif avg < 14:
        bullets.append("- Orta uzunlukta cümleler kullan; sade ve anlaşılır ol.")
    else:
        bullets.append("- Daha geniş açıklamalar yapabilirsin; ayrıntı vermekten çekinme.")

    # ── Emoji ──────────────────────────────────────────────────────────────────
    if profile.emoji_density > 0.01:
        bullets.append("- Uygun yerlerde emoji kullan 🎯 — ama abartma.")
    else:
        bullets.append("- Emoji kullanma; sade ve metin odaklı kal.")

    # ── Madde listesi ──────────────────────────────────────────────────────────
    if profile.bullet_ratio > 0.15:
        bullets.append("- Bilgileri madde listesi (- veya 1. 2. 3.) olarak sun.")
    else:
        bullets.append("- Paragraf biçiminde yaz; listeleri yalnızca şart olduğunda kullan.")

    # ── Başlık kullanımı ───────────────────────────────────────────────────────
    if profile.heading_ratio > 0.03:
        bullets.append("- Uzun cevaplarda Markdown başlıkları (## Başlık) kullan.")

    # ── Bold ───────────────────────────────────────────────────────────────────
    if profile.uses_bold:
        bullets.append("- **Anahtar terimleri** veya önemli kavramları kalın yap.")

    # ── Kod bloğu ─────────────────────────────────────────────────────────────
    if profile.uses_code_blocks:
        bullets.append("- Kod veya teknik içerik varsa ```kod bloğu``` kullan.")

    # ── Örnek cümlelerden ton tespiti ─────────────────────────────────────────
    if profile.sample_sentences:
        excerpts = " | ".join(profile.sample_sentences[:3])
        bullets.append(
            f"- Kullanıcının yazım tonuna örnekler: {excerpts[:300]}"
        )

    return bullets
