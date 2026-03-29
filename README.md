# Ai-Architecture-Linter

**Yapay Zeka Destekli Mimari Kod Analiz ve Denetim Aracı**
*AI-Powered Architecture Code Analysis and Audit Tool*

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Genel Bakış / Overview

AI Architecture Linter, yazılım geliştirme süreçlerinde (SDLC) **Kod İnceleme (Code Review)** adımlarını otomatize eden ve zenginleştiren yapay zeka destekli bir araçtır.

Mevcut sözdizimsel analiz araçlarının ötesine geçerek şu konulara odaklanır:

| Kategori | Ne Kontrol Eder |
|----------|-----------------|
| **SOLID Prensipleri** | SRP, OCP, LSP, ISP, DIP ihlalleri |
| **Clean Architecture** | Katmanlar arası bağımlılık ihlalleri (Entities → Use Cases → Interfaces → Infrastructure) |
| **Teknik Borç (Technical Debt)** | TODO/FIXME yorumları, uzun fonksiyonlar, büyük sınıflar, sihirli sayılar, uzun parametre listeleri, derin iç içe geçme |
| **Yapay Zeka İncelemesi** | OpenAI destekli mimari analiz ve öneri |

---

## Kurulum / Installation

```bash
pip install -e .
```

### Gereksinimler / Requirements

- Python 3.9+
- `click`, `openai`, `python-dotenv`

---

## Kullanım / Usage

### Temel Kullanım / Basic Usage

```bash
# Tek dosya analizi
ai-linter src/domain/user.py

# Dizin taraması (recursive)
ai-linter src/ --recursive

# Metin formatında çıktı (varsayılan)
ai-linter src/ --recursive --format text

# Markdown raporu (PR yorumu için idealdir)
ai-linter src/ --recursive --format markdown --output report.md

# JSON raporu
ai-linter src/ --recursive --format json --output report.json
```

### Yapay Zeka İncelemesini Devre Dışı Bırakma / Disable AI Review

```bash
ai-linter src/ --no-ai
```

### OpenAI API Anahtarı / OpenAI API Key

```bash
export OPENAI_API_KEY="sk-..."
ai-linter src/ --model gpt-4o
```

veya `.env` dosyası oluşturun:

```
OPENAI_API_KEY=sk-...
```

---

## Kural Referansı / Rule Reference

### SOLID Prensipleri

| Kural | Prensip | Açıklama |
|-------|---------|----------|
| `SRP001` | Single Responsibility | Sınıf çok fazla public metoda sahip (> 10) |
| `OCP001` | Open/Closed | Fonksiyon çok fazla `isinstance`/`type` kontrolü içeriyor (≥ 3) |
| `LSP001` | Liskov Substitution | ABC olmaksızın `NotImplementedError` fırlatılıyor |
| `ISP001` | Interface Segregation | Soyut sınıf çok fazla soyut metoda sahip (> 7) |
| `DIP001` | Dependency Inversion | Somut sınıf fonksiyon içinde doğrudan örnekleniyor |

### Clean Architecture

| Kural | Açıklama |
|-------|----------|
| `CA001` | İç katman dış katmandan import ediyor (Entities/UseCases → Interfaces/Infrastructure) |

### Teknik Borç

| Kural | Açıklama |
|-------|----------|
| `TD001` | TODO / FIXME / HACK / XXX yorumu |
| `TD002` | Uzun fonksiyon (> 50 satır) |
| `TD003` | Büyük sınıf (> 300 satır) |
| `TD004` | Sihirli sayı (adlandırılmamış sayısal literal) |
| `TD005` | Uzun parametre listesi (> 5 parametre) |
| `TD006` | Derin iç içe geçme (> 4 seviye) |

---

## GitHub Actions Entegrasyonu / GitHub Actions Integration

`.github/workflows/pr_review.yml` dosyası otomatik olarak:

1. Her Pull Request'te değişen Python dosyalarını analiz eder
2. Sonuçları PR yorumu olarak ekler (mevcut yorum güncellenir)
3. JSON raporunu artifact olarak kaydeder

### Kurulum / Setup

Repository secrets'a `OPENAI_API_KEY` ekleyin (opsiyonel – AI incelemesi için).

---

## Geliştirme / Development

```bash
# Bağımlılıkları kur
pip install -e .
pip install pytest pytest-cov

# Testleri çalıştır
python -m pytest tests/ -v

# Kapsam raporu
python -m pytest tests/ --cov=ai_linter --cov-report=term-missing
```

### Proje Yapısı / Project Structure

```
ai_linter/
├── analyzer/
│   ├── base.py              # Temel sınıflar ve veri modelleri
│   ├── solid_checker.py     # SOLID prensip kontrolleri (SRP/OCP/LSP/ISP/DIP)
│   ├── clean_arch_checker.py# Clean Architecture katman ihlal tespiti
│   └── tech_debt_checker.py # Teknik borç tespiti
├── ai/
│   └── review_engine.py     # OpenAI destekli inceleme motoru
├── report/
│   └── reporter.py          # JSON ve Markdown rapor üreteci
└── cli.py                   # Click tabanlı komut satırı arayüzü

tests/
├── fixtures/                # Test için örnek Python dosyaları
├── test_solid_checker.py
├── test_clean_arch_checker.py
├── test_tech_debt_checker.py
└── test_reporter.py
```

---

## Mimari / Architecture

Bu araç kendisi de Clean Architecture prensiplerine uygun tasarlanmıştır:

```
Domain (analyzer/base.py)
    ↑
Use Cases (analyzer/*_checker.py, ai/review_engine.py)
    ↑
Interface (cli.py, report/reporter.py)
```

Bağımlılıklar yalnızca içe (inward) doğru akar.

