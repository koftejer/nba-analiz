# NBA Maç Analiz Programı

Bu program, NBA maçları için gelişmiş istatistiksel analizler sunan ve maç önü raporları hazırlayan bir araçtır.

## Özellikler
- **Son 10 Maç Analizi**: Takımların son performanslarını, ilk yarı (İY) ve maç sonu (MS) detaylarıyla inceleyin.
- **H2H (Aralarındaki Maçlar)**: İki takımın bu sezonki karşılaşmalarını analiz edin.
- **Detaylı İstatistikler**: Çeyrek skorları ve takım liderleri.
- **Sakatlık Raporu**: CBS Sports üzerinden anlık sakatlık durumlarını takip edin.
- **Türkçe Rapor Çıktısı**: Bahis analizleri için hazır metin formatı.

## Kurulum
1. Gerekli kütüphaneleri yükleyin:
   ```bash
   pip install -r requirements.txt
   ```
2. Uygulamayı çalıştırın:
   ```bash
   streamlit run app.py
   ```

## Kullanım
- Sol menüden takımları ve maç tarihini seçin.
- "Analizi Oluştur" butonuna tıklayın.
- Oluşturulan raporu kopyalayıp kullanabilirsiniz.
