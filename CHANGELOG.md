# История изменений

## 0.1.0 CPU — 2026-09-19

- Добавлена отдельная полная CPU-сборка без комплекта CUDA/cuBLAS/cuDNN.
- Все модели Whisper, включая `large-v3`, доступны для ручного выбора на CPU.
- Добавлен отдельный Inno Setup installer и CPU release build-script.
- Фоновые workers удерживаются до завершения длительных операций.

## 0.1.0 — 2026-09-18

- Первый Windows-релиз: CPU/CUDA transcription, SRT editing, ASS и burn-in MP4.
- Автоматические профили NVENC/QSV/AMF/libx264 и аппаратные fallback.
- First-run диагностика, локальный model manager, прогресс, отмена и rotating log.
- PyInstaller distribution, Inno Setup installer и GitHub Actions.
