"""
main.py — Personal Omniscience Engine CLI
Kullanım:
    python main.py ingest          # data/ klasörünü vektörleştirir
    python main.py chat            # Terminal sohbet döngüsü
    python main.py watch           # Klasör izlemeyi başlatır
    python main.py clear           # Sohbet geçmişini siler
    python main.py analyze-style   # Stil profilini gösterir
"""

import logging
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

# ── Loglama ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True, show_path=False)],
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

console = Console()

BANNER = """
[bold cyan]
  ___                   _                   
 / _ \\ _ __ ___  _ __ (_)___  ___(_) ___ _ __   ___ ___ 
| | | | '_ ` _ \\| '_ \\| / __|/ __| |/ _ \\ '_ \\ / __/ _ \\
| |_| | | | | | | | | | \\__ \\ (__| |  __/ | | | (_|  __/
 \\___/|_| |_| |_|_| |_|_|___/\\___|_|\\___|_| |_|\\___\\___|

[/bold cyan][dim]Personal Omniscience Engine — Privacy-First AI[/dim]
"""


@click.group()
@click.version_option("1.0.0", prog_name="omniscience")
def cli():
    """🧠 Personal Omniscience Engine — kişisel bilgi asistanın."""
    pass


# ── ingest ─────────────────────────────────────────────────────────────────────

@cli.command()
@click.option(
    "--data-dir",
    default=None,
    type=click.Path(),
    help="Vektörleştirilecek klasör (varsayılan: config'deki DATA_DIR).",
)
def ingest(data_dir: str):
    """📥 Dosyaları okuyup Qdrant'a indeksler."""
    console.print(BANNER)

    from config import DATA_DIR
    from ingestion.loader import load_documents
    from ingestion.indexer import build_index

    directory = Path(data_dir) if data_dir else DATA_DIR

    with console.status(f"[bold green]Dosyalar yükleniyor: {directory}…"):
        docs = load_documents(directory)

    if not docs:
        console.print(
            Panel(
                f"[yellow]'{directory}' içinde desteklenen dosya bulunamadı.\n"
                "PDF, Markdown, TXT veya DOCX dosyaları ekle ve tekrar dene.[/yellow]",
                title="⚠️  Boş klasör",
            )
        )
        sys.exit(0)

    console.print(f"\n[bold]📄 {len(docs)} döküman yüklendi.[/bold]")

    with console.status("[bold green]Vektörleştiriliyor ve Qdrant'a yazılıyor…"):
        index = build_index(docs)

    if index:
        console.print(Panel("[bold green]✅ İndeksleme tamamlandı![/bold green]", title="Başarılı"))
    else:
        console.print(Panel("[red]❌ İndeksleme başarısız.[/red]", title="Hata"))


# ── chat ───────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--no-style", is_flag=True, default=False, help="Yazım tarzı taklidini devre dışı bırak.")
@click.option("--no-memory", is_flag=True, default=False, help="Sohbet geçmişini kullanma.")
def chat(no_style: bool, no_memory: bool):
    """💬 Terminal tabanlı sohbet döngüsü."""
    console.print(BANNER)

    from ingestion.indexer import load_existing_index
    from engine.query import get_chat_engine
    from engine.memory import load_history, save_history, create_memory

    with console.status("[bold green]İndeks yükleniyor…"):
        index = load_existing_index()

    if index is None:
        console.print(
            Panel(
                "[yellow]Önce [bold]python main.py ingest[/bold] komutunu çalıştır.[/yellow]",
                title="⚠️  İndeks bulunamadı",
            )
        )
        sys.exit(1)

    memory = create_memory() if no_memory else load_history()
    use_style = not no_style

    chat_engine = get_chat_engine(index, use_style=use_style, memory=memory)

    style_status = "[green]Açık[/green]" if use_style else "[yellow]Kapalı[/yellow]"
    console.print(
        Panel(
            f"[bold]Yazım tarzı taklidi:[/bold] {style_status}\n"
            "[dim]Çıkmak için 'çık', ':q' veya Ctrl+C[/dim]",
            title="🧠 Omniscience Hazır",
        )
    )

    while True:
        try:
            question = console.input("\n[bold cyan]Sen:[/bold cyan] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Görüşürüz![/dim]")
            break

        if not question:
            continue
        if question.lower() in {"çık", "q", ":q", "exit", "quit", "bye"}:
            break

        with console.status("[bold green]Düşünüyor…"):
            try:
                response = chat_engine.chat(question)
            except Exception as e:
                console.print(f"[red]❌ Hata: {e}[/red]")
                continue

        console.print(f"\n[bold magenta]Omniscience:[/bold magenta] {response}\n")
        console.rule(style="dim")

    if not no_memory:
        save_history(memory)
        console.print("[dim]💾 Sohbet geçmişi kaydedildi.[/dim]")


# ── watch ──────────────────────────────────────────────────────────────────────

@cli.command()
@click.option(
    "--data-dir",
    default=None,
    type=click.Path(),
    help="İzlenecek klasör (varsayılan: config'deki DATA_DIR).",
)
def watch(data_dir: str):
    """👁️  Klasörü izler; yeni dosya gelince otomatik indeksler."""
    console.print(BANNER)

    from config import DATA_DIR
    from ingestion.watcher import start_watcher

    directory = Path(data_dir) if data_dir else DATA_DIR
    console.print(
        Panel(
            f"[bold]İzlenen klasör:[/bold] {directory.resolve()}\n"
            "[dim]Durdurmak için Ctrl+C[/dim]",
            title="👁️  Watchdog Başlatılıyor",
        )
    )
    start_watcher(directory)


# ── clear ──────────────────────────────────────────────────────────────────────

@cli.command()
@click.confirmation_option(prompt="Sohbet geçmişini silmek istediğinden emin misin?")
def clear():
    """🗑️  Sohbet geçmişini temizler."""
    from engine.memory import clear_history
    clear_history()
    console.print("[bold green]✅ Sohbet geçmişi temizlendi.[/bold green]")


# ── analyze-style ──────────────────────────────────────────────────────────────

@cli.command("analyze-style")
@click.option(
    "--data-dir",
    default=None,
    type=click.Path(),
    help="Analiz edilecek klasör.",
)
def analyze_style_cmd(data_dir: str):
    """🎨 Yazım stili profilini gösterir."""
    from config import DATA_DIR
    from style.analyzer import analyze_style

    directory = Path(data_dir) if data_dir else DATA_DIR

    with console.status("[bold green]Stil analiz ediliyor…"):
        profile = analyze_style(directory)

    table = Table(title="🎨 Yazım Stili Profili", show_header=True, header_style="bold magenta")
    table.add_column("Özellik", style="cyan", no_wrap=True)
    table.add_column("Değer", style="white")

    table.add_row("Ortalama cümle uzunluğu", f"{profile.avg_sentence_length:.1f} kelime")
    table.add_row("Emoji yoğunluğu", f"{profile.emoji_density:.4f}")
    table.add_row("Madde listesi oranı", f"{profile.bullet_ratio:.2%}")
    table.add_row("Başlık oranı", f"{profile.heading_ratio:.2%}")
    table.add_row("Bold kullanımı", "✅" if profile.uses_bold else "❌")
    table.add_row("Kod bloğu kullanımı", "✅" if profile.uses_code_blocks else "❌")
    table.add_row("Toplam kelime", str(profile.total_words))
    table.add_row("Dil tahmini", profile.language_hint)
    table.add_row("Sık kelimeler", ", ".join(profile.top_words[:10]))

    console.print(table)

    if profile.sample_sentences:
        console.print("\n[bold]📝 Örnek cümleler:[/bold]")
        for i, s in enumerate(profile.sample_sentences, 1):
            console.print(f"  [dim]{i}.[/dim] {s}")


# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cli()
