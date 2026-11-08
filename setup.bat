@echo off
setlocal enabledelayedexpansion

echo.
echo  ========================================================
echo   Personal Omniscience Engine — Windows Kurulum Scripti
echo  ========================================================
echo.

:: Python kontrolü
python --version >nul 2>&1
if errorlevel 1 (
    echo [HATA] Python bulunamadi. Lutfen Python 3.11+ kur: https://python.org
    pause
    exit /b 1
)

:: Sanal ortam oluştur
if not exist "venv\" (
    echo [1/4] Sanal Python ortami olusturuluyor...
    python -m venv venv
) else (
    echo [1/4] Sanal ortam mevcut, atlaniyor.
)

:: Aktifleştir
echo [2/4] Sanal ortam aktifleştiriliyor...
call venv\Scripts\activate.bat

:: Bağımlılıkları yükle
echo [3/4] Bagimliliklar yukleniyor (ilk seferde uzun surebilir)...
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

:: .env dosyası yoksa kopyala
if not exist ".env" (
    echo [4/4] .env dosyasi olusturuluyor...
    copy .env.example .env >nul
    echo     ✓   .env olusturuldu. Gerekirse duzenle.
) else (
    echo [4/4] .env dosyasi mevcut, atlaniyor.
)

echo.
echo  ========================================================
echo   Kurulum tamamlandi!
echo  ========================================================
echo.
echo  Sonraki adimlar:
echo.
echo  1. Docker Desktop acik olduğundan emin ol, sonra:
echo     docker-compose up -d
echo.
echo  2. Ollama'yi calistir:
echo     ollama run llama3.2
echo.
echo  3. Dosyalarini data\ klasorune koy, sonra indeksle:
echo     python main.py ingest
echo.
echo  4. Arayuzu baslat:
echo     streamlit run ui\app.py
echo.
echo  VEYA terminal sohbeti:
echo     python main.py chat
echo.
pause
