"""
ui/app.py — Personal Omniscience Engine
Streamlit tabanlı chatbot arayüzü.
Çalıştır: streamlit run ui/app.py
"""

import sys
import shutil
import tempfile
import logging
from pathlib import Path

import streamlit as st

# Proje kökünü path'e ekle
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config import (
    DATA_DIR,
    QDRANT_URL,
    OLLAMA_BASE_URL,
    LLM_MODEL,
    EMBED_MODEL,
    COLLECTION_NAME,
    STYLE_ENABLED,
)

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Omniscience",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Main background */
.stApp {
    background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    border-right: 1px solid rgba(100, 200, 255, 0.1);
}

/* Chat messages */
[data-testid="stChatMessage"] {
    border-radius: 12px;
    padding: 4px 0;
}

/* User message */
[data-testid="stChatMessage"][data-testid*="user"] {
    background: rgba(100, 200, 255, 0.05);
}

/* Input area */
.stChatInputContainer {
    border-top: 1px solid rgba(100, 200, 255, 0.15);
    padding-top: 10px;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 500;
    transition: transform 0.2s, box-shadow 0.2s;
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

/* Status badges */
.status-ok {
    display: inline-block;
    background: rgba(0,200,100,0.2);
    color: #00c864;
    border: 1px solid rgba(0,200,100,0.3);
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 0.8em;
}
.status-err {
    display: inline-block;
    background: rgba(255,80,80,0.2);
    color: #ff5050;
    border: 1px solid rgba(255,80,80,0.3);
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 0.8em;
}

/* Metric cards */
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    padding: 12px;
}

/* File uploader */
[data-testid="stFileUploader"] {
    border: 2px dashed rgba(100, 200, 255, 0.2);
    border-radius: 12px;
    padding: 8px;
}
</style>
""", unsafe_allow_html=True)


# ─── Helper Functions ─────────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def _load_index():
    """Qdrant indeksini yükler (Streamlit cache — bir kere çalışır)."""
    try:
        from ingestion.indexer import load_existing_index
        return load_existing_index()
    except Exception as e:
        return None


def _check_qdrant() -> bool:
    try:
        from qdrant_client import QdrantClient
        c = QdrantClient(url=QDRANT_URL, timeout=3)
        c.get_collections()
        return True
    except Exception:
        return False


def _check_ollama() -> bool:
    try:
        import urllib.request
        urllib.request.urlopen(OLLAMA_BASE_URL, timeout=3)
        return True
    except Exception:
        return False


def _get_doc_count() -> int:
    try:
        from qdrant_client import QdrantClient
        c = QdrantClient(url=QDRANT_URL, timeout=3)
        info = c.get_collection(COLLECTION_NAME)
        return info.points_count or 0
    except Exception:
        return 0


def _ingest_file(path: Path):
    """Tek dosyayı yükleyip indeksler (Streamlit upload flow için)."""
    from ingestion.loader import load_single_file
    from ingestion.indexer import build_index
    docs = load_single_file(path)
    if docs:
        build_index(docs)
        _load_index.clear()  # cache'i temizle

def _get_chat_engine(use_style: bool):
    """Chat engine'i oluşturur. Session state'de saklanır."""
    from ingestion.indexer import load_existing_index
    from engine.query import get_chat_engine
    from engine.memory import ChatMemoryBuffer

    # memory session'da yaşıyor
    if "memory" not in st.session_state:
        from engine.memory import create_memory
        st.session_state.memory = create_memory()

    index = _load_index()
    if index is None:
        return None
    return get_chat_engine(index, use_style=use_style, memory=st.session_state.memory)


# ─── Session Initialization ───────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "use_style" not in st.session_state:
    st.session_state.use_style = STYLE_ENABLED


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 16px 0 8px 0;'>
        <span style='font-size: 2.5rem;'>🧠</span>
        <h2 style='margin:0; color: #a0c4ff; font-weight:700;'>Omniscience</h2>
        <p style='margin:0; color:#666; font-size:0.8em;'>Privacy-First AI</p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── Bağlantı Durumu ────────────────────────────────────────────────────────
    st.markdown("**🔌 Bağlantı Durumu**")
    col1, col2 = st.columns(2)
    qdrant_ok = _check_qdrant()
    ollama_ok = _check_ollama()
    with col1:
        badge = '<span class="status-ok">✓ Qdrant</span>' if qdrant_ok else '<span class="status-err">✗ Qdrant</span>'
        st.markdown(badge, unsafe_allow_html=True)
    with col2:
        badge = '<span class="status-ok">✓ Ollama</span>' if ollama_ok else '<span class="status-err">✗ Ollama</span>'
        st.markdown(badge, unsafe_allow_html=True)

    st.divider()

    # ── Metrikler ─────────────────────────────────────────────────────────────
    doc_count = _get_doc_count()
    file_count = len(list(DATA_DIR.rglob("*"))) if DATA_DIR.exists() else 0
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("📄 Vektör", f"{doc_count:,}")
    with col_b:
        st.metric("📁 Dosya", f"{file_count}")

    st.divider()

    # ── Stil Taklidi ──────────────────────────────────────────────────────────
    st.markdown("**🎨 Yazım Stili**")
    st.session_state.use_style = st.toggle(
        "Stilimi taklit et",
        value=st.session_state.use_style,
        help="Aktifken notlarındaki yazım tarzında cevap verir.",
    )

    st.divider()

    # ── Dosya Yükleme ─────────────────────────────────────────────────────────
    st.markdown("**📤 Belge Ekle**")
    uploaded = st.file_uploader(
        "Dosya seç",
        type=["pdf", "md", "txt", "docx"],
        label_visibility="collapsed",
    )
    if uploaded is not None:
        dest = DATA_DIR / uploaded.name
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(uploaded.getbuffer())
        with st.spinner(f"'{uploaded.name}' indeksleniyor…"):
            try:
                _ingest_file(dest)
                st.success(f"✅ '{uploaded.name}' eklendi!")
            except Exception as e:
                st.error(f"❌ Hata: {e}")

    st.divider()

    # ── Eylemler ─────────────────────────────────────────────────────────────
    st.markdown("**⚙️ Eylemler**")
    if st.button("🗑️ Sohbeti Temizle", use_container_width=True):
        st.session_state.messages = []
        if "memory" in st.session_state:
            del st.session_state["memory"]
        st.rerun()

    if st.button("🔄 İndeksi Yenile", use_container_width=True):
        _load_index.clear()
        st.rerun()

    st.divider()
    st.markdown(f"<div style='color:#444;font-size:0.75em;text-align:center;'>Model: {LLM_MODEL}<br>Embed: {EMBED_MODEL}</div>", unsafe_allow_html=True)


# ─── Main Content ─────────────────────────────────────────────────────────────
st.markdown("""
<div style='text-align:center; padding: 24px 0 8px 0;'>
    <h1 style='color: #a0c4ff; font-weight:700; font-size:2rem; margin:0;'>
        🧠 Kişisel Bilgi Asistanın
    </h1>
    <p style='color:#666; margin:4px 0 0 0;'>
        Notlarını, belgelerini ve fikirlerini sana geri anlatan yapay zeka.
    </p>
</div>
""", unsafe_allow_html=True)

# ── Durum Uyarıları ────────────────────────────────────────────────────────────
if not qdrant_ok:
    st.warning(
        "⚠️ **Qdrant bağlantısı kurulamadı.**  \n"
        "Terminalde şunu çalıştır: `docker-compose up -d`",
        icon="🐋",
    )
if not ollama_ok:
    st.warning(
        "⚠️ **Ollama çalışmıyor.**  \n"
        f"Terminalde şunu çalıştır: `ollama run {LLM_MODEL}`",
        icon="🦙",
    )

index = _load_index()
if index is None and qdrant_ok:
    st.info(
        "💡 Henüz indeks yok. Sol panelden belge yükle veya `python main.py ingest` komutunu çalıştır.",
        icon="📥",
    )

# ── Sohbet Geçmişi ────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧠" if msg["role"] == "assistant" else "👤"):
        st.markdown(msg["content"])

# ── Input ─────────────────────────────────────────────────────────────────────
if prompt := st.chat_input(
    "Notlarından bir şey sor…",
    disabled=(index is None or not qdrant_ok or not ollama_ok),
):
    # Kullanıcı mesajını kaydet
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Cevap üret
    with st.chat_message("assistant", avatar="🧠"):
        placeholder = st.empty()
        placeholder.markdown("_Düşünüyor_ ⏳")

        try:
            engine = _get_chat_engine(st.session_state.use_style)
            if engine is None:
                response_text = "❌ İndeks yüklenemedi. Lütfen `python main.py ingest` komutunu çalıştır."
            else:
                response = engine.chat(prompt)
                response_text = str(response)
        except Exception as e:
            response_text = f"❌ Hata oluştu: {e}"

        placeholder.markdown(response_text)
        st.session_state.messages.append({"role": "assistant", "content": response_text})
