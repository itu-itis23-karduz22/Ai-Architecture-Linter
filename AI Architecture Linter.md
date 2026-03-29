# PROJECT CHARTER

**Proje Adı:** Yapay Zeka Destekli Mimari Kod Analiz ve Denetim Aracı (AI Architecture Linter)
**Hedef Kitle / Ekip:** SKY Remote
**Tarih:** 24 Mart 2026
**Versiyon:** 1.0
**Sınıflandırma: TASNİF DIŞI**

---

## 1. Projenin Amacı ve Gerekçesi (Executive Summary)
Yazılım geliştirme süreçlerinde (SDLC) Kod İnceleme (Code Review) adımlarını otomatize eden ve zenginleştiren yapay zeka destekli bir araç geliştirmektir. 

Mevcut araçlar sözdizimsel hatalara (syntax errors) odaklanırken, bu projenin amacı sistemin yapısal bütünlüğüne, mimari prensiplere (SOLID, Clean Architecture) uyumluluğuna ve teknik borç (technical debt) oluşumuna proaktif olarak müdahale etmektir. Pull Request (PR) aşamasında mimari sapmaları (architectural drift) tespit ederek kalite güvence süreçlerine yeni bir katman eklenecektir.

## 2. Proje Kapsamı (Project Scope)

**Kapsam İçi (In-Scope):**
* Versiyon kontrol sistemlerinde (GitHub/GitLab) açılan Pull Request'lerin dinlenmesi.
* PR içerisindeki kod değişikliklerinin (diff), değişen dosya yollarının ve yeni `import/using` bağımlılıklarının tespit edilmesi.
* Elde edilen verilerin, Büyük Dil Modelleri (LLM) kullanılarak mimari kurallar çerçevesinde analiz edilmesi.
* İlgili PR üzerine otomatik bot yorumu (comment/annotation) ile geri bildirim bırakılması.

**Kapsam Dışı (Out-of-Scope):**
* Birim test (unit test) veya entegrasyon testlerinin yazılması.
* Performans, sızma (pentest) veya genel güvenlik açığı (vulnerability) taramaları.
* CI/CD süreçlerini durduran (hard-blocker) zorunlu kural setlerinin uygulanması (araç sadece tavsiye ve uyarı niteliğinde çalışacaktır).

## 3. Pazar ve Rekabet Konumlandırması

| Çözüm Kategorisi | Sektördeki Temsilciler | Projenin Farkı ve Odak Noktası |
| :--- | :--- | :--- |
| **Geleneksel Statik Analiz** | SonarQube, ArchUnit | Katı kurallara dayanır. AI aracımız ise esnek bağlam analizi yapar ve kurulum eforunu düşürür. |
| **Genel AI Asistanları** | Copilot, CodeRabbit | Genel hata bulur. AI aracımız ise projeye özgü "mimari tasarım kararlarına" odaklanır. |

## 4. Teslimatlar ve Proje Kilometre Taşları (Milestones)

**Faz 1: Minimum Çalışan Ürün (MVP) - [Tahmini Deadline: 30 Nisan 2026]**
* **Aşama 1.1:** Versiyon kontrol sistemi (VCS) API entegrasyonu ve Webhook/CI tetikleyicilerinin ayarlanması.
* **Aşama 1.2:** Değişiklik setinin (diff) ayrıştırılarak anlamlı verilere dönüştürülmesi.
* **Aşama 1.3:** Kapalı Ağda çalışan LLM (LLaMa3 vb.) prompt mühendisliği ve API bağlantısının kurulması.
* **Aşama 1.4:** İlk başarılı otomatik PR yorumunun CI/CD akışında sergilenmesi (Proof of Concept).

**Faz 2: İleri Seviye Özellikler - [Tahmini Deadline: MVP Sonrası 11 Mayıs 2026]**
* **Aşama 2.1:** Depo içindeki `architecture.md` dosyasını okuyarak dinamik kural motoru (RAG yaklaşımı) oluşturulması.
* **Aşama 2.2:** Abstract Syntax Tree (AST) tabanlı bağımlılık grafiği çıkarımı ile yapay zeka halüsinasyonlarının en aza indirilmesi.

## 5. Gelişim Hedefleri (Expected Learnings)
1. **Üretken Yapay Zeka (GenAI) Mühendisliği:** LLM API yönetimi, Persona/Prompt tasarımı, maliyet/token optimizasyonu ve yapılandırılmış veri (JSON) işleme.
2. **DevOps ve Otomasyon:** Git API'leri, Webhook yönetimi ve CI/CD pipeline yapılandırması.
3. **Yazılım Mimarisi Hakimiyeti:** Clean Architecture, Design Patterns ve SOLID prensiplerinin pratiğe dökülmesi.

## 6. Proje Kaynakları ve Teknoloji Yığını (Tech Stack)
*(Not: Bu alan proje başlangıcında ekip kararlarına bırakılmıştır.)*
* **Versiyon Kontrol ve CI/CD:** [Örn: GitHub Actions / GitLab CI]
* **Geliştirme Dili:** [Örn: Python / Node.js / Go]
* **LLM Sağlayıcı:** [Örn: Groq API (LLaMa3)]

## 7. Riskler ve Azaltma Stratejileri (Risks & Mitigations)
* **Risk:** LLM'in yanlış veya alakasız mimari uyarılarda bulunması (Halüsinasyon).
  * *Çözüm:* Prompt'a projenin bağımlılık ağacının verilmesi ve çıktının sadece belirli bir JSON formatında (Structured Output) istenmesi.
* **Risk:** Token maliyetlerinin veya API limitlerinin aşılması.
  * *Çözüm:* Tüm dosyayı değil, sadece değişen (diff) satırları ve `import` bloklarını LLM'e göndererek bağlam penceresini (context window) daraltmak.

---
**NOT:** Bu doküman TASNİF DIŞI olarak sınıflandırılmıştır.