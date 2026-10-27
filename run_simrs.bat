@echo off
title SIMRS - Sistem Informasi Rumah Sakit Terintegrasi
echo ============================================================
echo   MENJALANKAN SISTEM INFORMASI RUMAH SAKIT (SIMRS)
echo ============================================================
echo.
echo Pastikan Laragon dan MySQL sudah berjalan (Start All pada Laragon).
echo.
echo Menjalankan server aplikasi web Flask...
echo Buka peramban di: http://127.0.0.1:5000
echo Login Admin: username=admin ^| password=admin123
echo.
python app.py
pause
