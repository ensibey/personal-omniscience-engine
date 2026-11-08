"""
ingestion/watcher.py
Watchdog tabanlı klasör izleyici.
data/ klasörüne eklenen yeni dosyaları otomatik olarak indeksler.
"""

import logging
import time
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from config import DATA_DIR, SUPPORTED_EXTENSIONS
from ingestion.loader import load_single_file

logger = logging.getLogger(__name__)


class NewFileHandler(FileSystemEventHandler):
    """Yeni dosya oluşturulduğunda tetiklenir."""

    def __init__(self):
        # Import burada yapılır — döngüsel import'tan kaçınmak için
        from ingestion.indexer import build_index
        self._build_index = build_index

    def on_created(self, event: FileSystemEvent):
        if event.is_directory:
            return

        path = Path(event.src_path)

        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return

        logger.info(f"📂 Yeni dosya algılandı: {path.name}")

        # Dosyanın tamamen yazılmasını bekle
        time.sleep(0.5)

        docs = load_single_file(path)
        if docs:
            self._build_index(docs)
            logger.info(f"✅ '{path.name}' otomatik olarak indekslendi.")

    def on_modified(self, event: FileSystemEvent):
        # Değiştirilen dosyaları da yeniden indeksle
        self.on_created(event)


def start_watcher(directory: Path = DATA_DIR) -> None:
    """
    Klasörü izlemeye başlar. Ctrl+C ile durdurulur.
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)

    handler = NewFileHandler()
    observer = Observer()
    observer.schedule(handler, str(directory), recursive=True)
    observer.start()

    logger.info(f"👁️  Klasör izleniyor: {directory.resolve()}")
    logger.info("Durdurmak için Ctrl+C…")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logger.info("İzleyici durduruldu.")

    observer.join()
