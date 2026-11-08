"""
ingestion/loader.py
PDF, Markdown, Word (.docx) ve TXT dosyalarını LlamaIndex Document'larına dönüştürür.
"""

import logging
from pathlib import Path
from typing import List

from llama_index.core import SimpleDirectoryReader
from llama_index.core.schema import Document

from config import DATA_DIR, SUPPORTED_EXTENSIONS

logger = logging.getLogger(__name__)


def load_documents(directory: Path = DATA_DIR) -> List[Document]:
    """
    Verilen dizindeki desteklenen tüm dosyaları yükler.
    Boş dizin ya da desteklenmeyen dosya türlerini sessizce atlar.
    """
    directory = Path(directory)

    if not directory.exists():
        logger.warning(f"Veri klasörü bulunamadı: {directory}. Oluşturuluyor…")
        directory.mkdir(parents=True, exist_ok=True)
        return []

    # Desteklenen uzantılara sahip en az bir dosya var mı?
    found = list(directory.rglob("*"))
    eligible = [f for f in found if f.suffix.lower() in SUPPORTED_EXTENSIONS]

    if not eligible:
        logger.warning(
            f"'{directory}' klasöründe desteklenen dosya yok "
            f"({', '.join(SUPPORTED_EXTENSIONS)})."
        )
        return []

    logger.info(f"{len(eligible)} dosya bulundu, yükleniyor…")

    reader = SimpleDirectoryReader(
        input_dir=str(directory),
        recursive=True,
        required_exts=SUPPORTED_EXTENSIONS,
        # Her Document'a kaynak dosyasının adını metadata olarak ekle
        filename_as_id=True,
    )

    documents = reader.load_data()
    logger.info(f"✅ {len(documents)} döküman yüklendi.")
    return documents


def load_single_file(path: Path) -> List[Document]:
    """
    Tek bir dosyayı yükler. Watchdog tetiklendiğinde kullanılır.
    """
    path = Path(path)
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        logger.warning(f"Desteklenmeyen dosya türü atlandı: {path.name}")
        return []

    reader = SimpleDirectoryReader(input_files=[str(path)], filename_as_id=True)
    docs = reader.load_data()
    logger.info(f"✅ '{path.name}' yüklendi → {len(docs)} döküman parçası.")
    return docs
