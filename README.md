<div align="center">

# 🧠 Personal Omniscience Engine

### *Senin verin, senin dilin.*
**İnternet gerektirmeyen, kişiselleştirilmiş bilgi asistanı.**

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)](https://python.org)
[![LlamaIndex](https://img.shields.io/badge/LlamaIndex-0.10+-purple?logo=data:image/svg+xml;base64,)](https://llamaindex.ai)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-red)](https://qdrant.tech)
[![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-black)](https://ollama.ai)
[![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B?logo=streamlit)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## ✨ Ne Yapar?

**Personal Omniscience Engine**, kendi notlarını, PDF'lerini ve dökümanlarını kullanarak sana cevap veren **tamamen yerel** bir yapay zeka asistanıdır.

- 🔒 **Privacy-First**: Verilerin internet'e çıkmaz. Her şey kendi bilgisayarında çalışır.
- 🎨 **Style Mimicry**: Kendi notlarındaki yazım tarzını öğrenir; çıktıları da senin gibi yazar.
- 📁 **Multi-Source**: PDF, Markdown, Word, TXT — tek merkezde birleşir.
- 👁️ **Auto-Index**: Klasörü izler, yeni dosya gelince otomatik vektörleştirir.
- 💬 **Memory**: Konuşma geçmişini hatırlar.

---

## 🏗️ Mimari

```
┌─────────────────────────────────────────────────────────┐
│  KULLANICI (UI / CLI)                                   │
│  ┌─────────────┐   ┌──────────────────────────────┐    │
│  │Streamlit UI │   │  python main.py chat          │    │
│  └──────┬──────┘   └──────────────┬───────────────┘    │
└─────────┼────────────────────────┼───────────────────  │
          │  SORU                  │  SORU               │
          ▼                        ▼                      │
┌─────────────────────────────────────────────────────┐   │
│  ENGINE (LlamaIndex)                                │   │
│   ┌──────────────┐    ┌──────────────────────────┐  │   │
│   │ query.py     │    │ memory.py                │  │   │
│   │ ChatEngine   │◄───│ ChatMemoryBuffer          │  │   │
│   └──────┬───────┘    └──────────────────────────┘  │   │
└──────────┼──────────────────────────────────────────┘   │
           │  retrieve                                     │
           ▼                                               │
┌─────────────────────────────────────────────────────┐   │
│  QDRANT (Vector DB)  ←── ingestion/indexer.py       │   │
│   nomic-embed-text embeddings, cosine similarity    │   │
└─────────────────────────────────────────────────────┘   │
           │  generate                                     │
           ▼                                               │
┌─────────────────────────────────────────────────────┐   │
│  OLLAMA (Local LLM)  llama3.2 / mistral             │   │
└─────────────────────────────────────────────────────┘   │
```

---

## 🚀 Hızlı Başlangıç

### 1. Ön Koşullar

| Araç | Kurulum |
|---|---|
| Python 3.11+ | [python.org](https://python.org) |
| Docker Desktop | [docker.com](https://docker.com/products/docker-desktop) |
| Ollama | [ollama.ai](https://ollama.ai) |

### 2. Modelleri İndir

```bash
# Metin üretimi için
ollama pull llama3.2

# Embedding için
ollama pull nomic-embed-text
```

### 3. Projeyi Kur (Windows)

```bash
git clone https://github.com/ensibey/personal-omniscience-engine.git
cd personal-omniscience-engine

# Tek tıkla kurulum:
setup.bat
```

Manuel kurulum:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

### 4. Qdrant'ı Başlat

```bash
docker-compose up -d
```

### 5. Dosyalarını Ekle

```
data/
├── notlarim.md
├── kitap_ozeti.pdf
├── fikirler.txt
└── proje_dokumanı.docx
```

### 6. İndeksle

```bash
python main.py ingest
```

### 7. Kullan!

**Streamlit UI (önerilen):**
```bash
streamlit run ui/app.py
```

**Terminal sohbeti:**
```bash
python main.py chat
```

---

## 🛠️ CLI Komutları

```bash
python main.py ingest          # Dosyaları vektörleştirir
python main.py chat            # Terminal sohbet
python main.py watch           # Klasörü izler (auto-index)
python main.py clear           # Sohbet geçmişini siler
python main.py analyze-style   # Yazım stili profilini gösterir
```

---

## ⚙️ Konfigürasyon

`.env` dosyasını düzenle:

```env
DATA_DIR=data
LLM_MODEL=llama3.2          # veya mistral, phi3, vb.
EMBED_MODEL=nomic-embed-text
QDRANT_URL=http://localhost:6333
CHUNK_SIZE=512
CHUNK_OVERLAP=64
TOP_K=5
STYLE_ENABLED=true
```

---

## 📁 Proje Yapısı

```
personal-omniscience-engine/
├── config.py                # Merkezi konfigürasyon
├── main.py                  # CLI entrypoint
├── docker-compose.yml       # Qdrant servisi
├── requirements.txt
├── setup.bat                # Windows kurulum
│
├── ingestion/
│   ├── loader.py            # Dosya okuyucu
│   ├── indexer.py           # Qdrant vektörleme
│   └── watcher.py           # Otomatik izleme
│
├── engine/
│   ├── query.py             # RAG sorgu motoru
│   └── memory.py            # Konuşma hafızası
│
├── style/
│   ├── analyzer.py          # Yazım tarzı analizi
│   └── prompt_builder.py    # Dinamik sistem prompt
│
├── ui/
│   └── app.py               # Streamlit arayüzü
│
└── data/                    # ← Kendi dosyalarını buraya koy
```

---

## 🔮 Yol Haritası

- [x] PDF, MD, TXT, DOCX desteği
- [x] Qdrant vektör veritabanı entegrasyonu
- [x] Ollama yerel LLM entegrasyonu
- [x] Konuşma hafızası
- [x] Yazım tarzı analizi & taklidi
- [x] Watchdog otomatik indeksleme
- [x] Streamlit UI
- [ ] Obsidian vault entegrasyonu
- [ ] Grafik tabanlı bilgi haritası (Graph RAG)
- [ ] Ses ile soru sorma

---

## 📄 Lisans

MIT © 2025
