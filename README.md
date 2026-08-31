# Stok Takip Sistemi

Küçük ölçekli bir depo/atölye için geliştirilmiş, masaüstünde çalışan stok ve emanet takip uygulaması. Python'un standart kütüphanesiyle (Tkinter + SQLite) yazılmıştır, harici bir paket kurulumu gerektirmez.

## Özellikler

- **Stok yönetimi:** Ürün girişi, isimle arama/düzeltme, silme (üzerinde açık emanet varsa silme engellenir).
- **Üye yönetimi:** Üye kaydı, ad/TC/telefon ile arama-düzeltme, silme (açık emaneti varsa silme engellenir).
- **Emanet takibi:** Bir üyeye malzeme emanet verme ve (kısmi veya tam) teslim alma. Emanet verilen adet, stok adedinden düşülmez; ekranda `Toplam / Emanette / Müsait` olarak ayrı gösterilir.
- **Canlı arama:** Tüm arama kutuları yazarken listeyi anında günceller.
- **Türkçe karakter desteği:** Bazı Windows/Tcl-Tk kurulumlarında görülen ş/ı/ğ klavye giriş sorununa karşı otomatik düzeltme içerir.
- Tüm veriler yerelde, çalışma klasöründeki `stok.db` adlı SQLite dosyasında saklanır.

## Gereksinimler

- Windows üzerinde **Python 3.10+** (Tkinter, Python'un standart kurulumuyla birlikte gelir; ayrıca kurulum gerekmez).
- Ek bir pip paketi gerekmez.

Python kurulu olup olmadığını kontrol etmek için:

```powershell
python --version
```

Python kurulu değilse [python.org](https://www.python.org/downloads/) adresinden indirip kurulum sırasında **"Add python.exe to PATH"** seçeneğini işaretleyin.

## Kurulum

Ek bir kurulum adımı yoktur; proje klasörünü edinmek yeterlidir.

```powershell
git clone <depo-adresi>
cd stock-status
```

(Depoyu zaten klonladıysanız veya dosyaları elle kopyaladıysanız bu adımı atlayabilirsiniz.)

## Çalıştırma

Proje klasöründeyken:

```powershell
python main.py
```

İlk çalıştırmada aynı klasörde `stok.db` adlı boş bir veritabanı dosyası otomatik olarak oluşturulur. Uygulamayı her kapatıp açtığınızda veriler bu dosyada saklı kalmaya devam eder.

> `stok.db` dosyasını silmek tüm stok, üye ve emanet kayıtlarını kalıcı olarak siler — yedeksiz silmeyin.

## Kullanım

Uygulama açıldığında üç bölmeli bir ana menü karşılar: sol üstte **Stok**, sağ üstte **Üye**, altta **Emanet**.

### Stok

| Ekran | Ne yapar |
|---|---|
| **Stok Giriş** | Raf No, Stok Adı ve Stok Adedi girilerek yeni bir stok kaydı açılır. Sıra No otomatik verilir, giriş tarihi (saatiyle birlikte) otomatik kaydedilir. Aynı isimde stok zaten varsa (büyük/küçük harf ve Türkçe karakter farkı gözetilmeden) kayıt reddedilir. |
| **Stok Ara / Düzelt** | Stok adına göre arama yapılır (yazarken liste anında güncellenir). Listeden bir satır seçilince Raf No, Stok Adı ve Stok Adedi düzenlenebilir. Emanette olan adedin altına düşürülemez. |
| **Stok Sil** | Arama ile bulunan bir stok seçilip silinir. Üzerinde açık (teslim alınmamış) emanet varsa silme işlemi engellenir. |

Arama sonuç tablosunda her ürün için `Toplam`, `Emanette` ve `Müsait` adetler ayrı sütunlarda gösterilir.

### Üye

| Ekran | Ne yapar |
|---|---|
| **Üye Kayıt** | Üye Adı, Üye TC (11 haneli), Telefon No (10 haneli, zorunlu) ve Adres girilerek yeni üye kaydı açılır. Üye No otomatik verilir. Aynı TC ile ikinci kayıt yapılamaz. |
| **Üye Ara / Düzelt** | Ad, TC veya Telefon kriteriyle arama yapılır (yazarken liste anında güncellenir). Seçilen üyenin tüm bilgileri düzenlenebilir. |
| **Üye Sil** | Arama ile bulunan bir üye seçilip silinir. Üyenin açık (teslim edilmemiş) emaneti varsa silme işlemi engellenir. |

### Emanet

| Ekran | Ne yapar |
|---|---|
| **Emanet Ver** | Önce bir üye, ardından bir malzeme seçilir; seçilen malzemenin adı ve müsait adedi ekranda görünür. Verilecek adet girilip onaylanır. Müsait adetten fazlası verilemez. Üyenin mevcut açık emanetleri ekranın altında listelenir. |
| **Emanet Teslim Al** | Önce bir üye seçilir; üyenin açık emanetleri listelenir. Bir kayıt seçilince teslim alınacak adet, kalan miktarla otomatik doldurulur — kısmen veya tamamen teslim alınabilir. Üyenin teslim alınacak emaneti yoksa bilgilendirme mesajı gösterilir. |

## Proje Yapısı

```
stock-status/
├── main.py              # Uygulama girişi: ana pencere + sayfa yönlendirici
├── veritabani.py         # SQLite şeması, veri erişimi ve iş kuralları
├── arayuz/
│   ├── ortak.py           # Ortak sayfa/tablo/form yardımcıları
│   ├── ana_menu.py        # Üç bölmeli ana menü
│   ├── stok.py             # Stok giriş / ara-düzelt / sil sayfaları
│   ├── uye.py               # Üye kayıt / ara-düzelt / sil sayfaları
│   └── emanet.py           # Emanet ver / teslim al sayfaları
└── stok.db                  # Uygulama verisi (ilk çalıştırmada otomatik oluşur)
```

## Sık Karşılaşılan Sorunlar

- **Uygulama açılmıyor / `ModuleNotFoundError: tkinter`:** Python kurulumunuz Tkinter olmadan yapılmış olabilir (bazı Linux dağıtımlarında ayrı paket olarak gelir). Windows'ta standart Python kurulumunda bu sorun görülmez.
- **Türkçe karakterler (ş, ı, ğ) yazarken bozuk çıkıyor:** Uygulama bu duruma karşı otomatik düzeltme içerir. Sorun devam ederse Python'u güncel bir sürüme yükseltmeyi deneyin.
- **Veriler kayboldu:** `stok.db` dosyasının proje klasöründe olduğundan ve yanlışlıkla silinmediğinden emin olun.
