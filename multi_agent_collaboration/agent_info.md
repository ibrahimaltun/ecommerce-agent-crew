# Module Details

## Agent Details

1. Developer Agent (Geliştirici):

- Kullanıcı isterine göre kodu yazar veya Reviewer'dan gelen eleştiriler doğrultusunda
kodu günceller (Code Refactoring / Bug Fixing).

2. Code Reviewer Agent (Kod İnceleyici):

- Yazılan kodu güvenlik, performans, okunabilirlik ve işlevsellik açısından denetler.
Kod kusursuzsa onay verir (Approval), eksik varsa somut geri bildirimler (Feedback)
sunarak kodu Developer'a geri gönderir.

---

Çoklu Agent Mimarisinin Temel Terimleri:

- Peer Review Pattern (Akran Denetimi Mimarisi): Çıktının son kullanıcıya sunulmadan
önce başka bir uzman agent tarafından denetlenip onaylanması süreci.

- Structured Output (Yapısallaştırılmış Çıktı): Reviewer'ın kararlarını (Onay Durumu
ve Eleştiriler) Pydantic şeması kullanarak garanti altına alınmış JSON formatında
döndürmesi.

- Max Iterations / Recursion Limit (Maksimum Döngü Sınırı): Local modellerin sonsuz
bir tartışma döngüsüne (Infinite Debate Loop) girmesini engelleyen güvenlik barajı.

## Module Architecture

[Developer Node] ──> [Tester Node (Subprocess / PyTest)]
                           │
             ┌─────────────┴─────────────┐
        (Test Başarısız)            (Test Başarılı)
             │                           │
             ▼                           ▼
     [Developer'a Dön]           [Reviewer Node]
                                         │
                           ┌─────────────┴─────────────┐
                      (Revizyon)                     (Onay)
                           │                           │
                           ▼                           ▼
                   [Developer'a Dön]                 [END]

# Detail Concepts

1. Dynamic Code Execution (Dinamik Kod Çalıştırma): Developer'ın ürettiği kodun sanal ortamda geçici bir
dosyaya (.py) yazılması ve local terminal üzerinden subprocess ile tetiklenmesi.

2. Traceback Capture (Hata Dökümü Yakalama): Testlerin kalması veya kodun SyntaxError / RuntimeError
vermesi durumunda oluşan terminal çıktısının (stdout/stderr) okunup Developer'a hata geri bildirimi
olarak beslenmesi.

3. Execution Sandbox (Çalıştırma Kum Havuzu): Test dosyasının izole bir dizinde oluşturulup işlem bitince
temizlenmesi.

# New Libs

- pytest
- rich

---
