# KAN-32 — WebSocket Echo Spike

- Django Channels + Daphne ile yerel WebSocket echo çalıştırıldı.
- Test sayfası: http://localhost:8000/chat-test/
- Gönderilen metin in-memory channel layer üzerinden geri dönüyor.
- In-memory katman yalnızca tek süreçte çalışır; Sprint 2’de Redis ile değiştirilecek.
- Kalıcı mesaj geçmişi PostgreSQL’de tutulacak.
- Proje JWT kullanıyor; WebSocket için ayrıca token doğrulaması eklenecek.
- Bu deneme anonimdir ve müşteri verilerine erişmez.

Test: `python -m pytest chat/tests.py -q`