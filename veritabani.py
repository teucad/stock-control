# -*- coding: utf-8 -*-
"""
Stok Takip Sistemi - Veri Katmanı

Tüm SQLite erişimi ve iş kuralları burada toplanır. Arayüz (arayuz/*.py)
dosyaları doğrudan SQL yazmaz, sadece bu modüldeki fonksiyonları çağırır.

İş kuralı ihlallerinde (silme engeli, adet aşımı, tekrar eden TC vb.)
ValueError fırlatılır; arayüz katmanı bunu yakalayıp kullanıcıya
Türkçe mesaj olarak gösterir.
"""

import sqlite3
import os
import sys
from contextlib import contextmanager
from datetime import datetime

if getattr(sys, "frozen", False):
    # PyInstaller ile paketlenmiş exe: __file__ her çalıştırmada silinen
    # geçici bir _MEIPASS klasörünü gösterir; onun yerine exe'nin kendi
    # bulunduğu klasörü kullanmalıyız ki veritabanı kalıcı olsun.
    _TEMEL_DIZIN = os.path.dirname(os.path.abspath(sys.executable))
else:
    _TEMEL_DIZIN = os.path.dirname(os.path.abspath(__file__))

DB_YOLU = os.path.join(_TEMEL_DIZIN, "stok.db")


@contextmanager
def baglanti():
    """Tek bir bağlantı açar, foreign key desteğini etkinleştirir,
    işlem başarılıysa commit, hata olursa rollback yapar."""
    con = sqlite3.connect(DB_YOLU)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def sema_kur():
    """Veritabanı dosyasını ve tabloları (yoksa) oluşturur."""
    with baglanti() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS urun (
                sira_no      INTEGER PRIMARY KEY AUTOINCREMENT,
                raf_no       TEXT    NOT NULL,
                stok_adi     TEXT    NOT NULL,
                stok_adedi   INTEGER NOT NULL CHECK (stok_adedi >= 0),
                pert_adedi   INTEGER NOT NULL DEFAULT 0 CHECK (pert_adedi >= 0),
                giris_tarihi TEXT    NOT NULL
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS uye (
                uye_no   INTEGER PRIMARY KEY AUTOINCREMENT,
                uye_adi  TEXT NOT NULL,
                tc       TEXT NOT NULL UNIQUE,
                telefon  TEXT,
                adres    TEXT
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS emanet (
                emanet_no     INTEGER PRIMARY KEY AUTOINCREMENT,
                uye_no        INTEGER NOT NULL REFERENCES uye(uye_no),
                sira_no       INTEGER NOT NULL REFERENCES urun(sira_no),
                adet          INTEGER NOT NULL CHECK (adet > 0),
                iade_adedi    INTEGER NOT NULL DEFAULT 0 CHECK (iade_adedi >= 0),
                veris_tarihi  TEXT    NOT NULL,
                teslim_tarihi TEXT
            )
        """)
        # Daha önce oluşturulmuş veritabanlarında CREATE TABLE IF NOT EXISTS
        # yeni sütunu eklemez; sonradan gelen sütunlar burada tamamlanır.
        _sutun_ekle_yoksa(con, "urun", "pert_adedi",
                          "INTEGER NOT NULL DEFAULT 0 CHECK (pert_adedi >= 0)")


def _sutun_ekle_yoksa(con, tablo, sutun, tanim):
    """Var olan veritabanlarına sonradan eklenen sütunları tamamlar."""
    mevcut = [s["name"] for s in con.execute(f"PRAGMA table_info({tablo})")]
    if sutun not in mevcut:
        con.execute(f"ALTER TABLE {tablo} ADD COLUMN {sutun} {tanim}")


# --------------------------------------------------------------------------
# Doğrulama / biçimlendirme yardımcıları
# --------------------------------------------------------------------------

def tc_gecerli(tc):
    tc = (tc or "").strip()
    return tc.isdigit() and len(tc) == 11


def telefon_gecerli(telefon):
    telefon = (telefon or "").strip().replace(" ", "")
    return telefon.isdigit() and len(telefon) == 10


def pozitif_sayi(metin):
    """Metni pozitif tam sayıya çevirir; geçersizse None döner."""
    try:
        deger = int(str(metin).strip())
    except (TypeError, ValueError):
        return None
    return deger if deger >= 0 else None


def bugun():
    """Şu anki tarih ve saati 'YYYY-AA-GG SS:DD:ss' biçiminde döner."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def tarih_goster(iso_deger):
    """'YYYY-AA-GG SS:DD:ss' -> 'GG.AA.YYYY SS:DD'. Geçersizse olduğu gibi döner."""
    if not iso_deger:
        return ""
    parcalar = iso_deger.split(" ")
    tarih_kismi = parcalar[0]
    saat_kismi = parcalar[1][:5] if len(parcalar) > 1 else ""
    gun_ay_yil = tarih_kismi.split("-")
    if len(gun_ay_yil) == 3:
        yil, ay, gun = gun_ay_yil
        tarih_metni = f"{gun}.{ay}.{yil}"
    else:
        tarih_metni = tarih_kismi
    return f"{tarih_metni} {saat_kismi}" if saat_kismi else tarih_metni


def _tr_kucult(metin):
    """Python'un varsayılan .lower() metodu Türkçe İ/I harflerini doğru
    çevirmez (İ -> iki karakter, I -> 'i'). Arama/karşılaştırmalarda bu
    yüzden önce Türkçe'ye özgü eşleme uygulanır."""
    return (metin or "").replace("İ", "i").replace("I", "ı").lower()


def _icerir(buyuk_metin, arama_metni):
    """Türkçe karakterlere duyarlı, büyük/küçük harf gözetmeyen 'içerir mi'."""
    return _tr_kucult(arama_metni) in _tr_kucult(buyuk_metin)


# --------------------------------------------------------------------------
# ÜRÜN (STOK)
# --------------------------------------------------------------------------

_URUN_SECIM_SQL = """
    SELECT u.sira_no, u.raf_no, u.stok_adi, u.stok_adedi, u.pert_adedi,
           u.giris_tarihi,
           COALESCE(SUM(CASE WHEN e.adet > e.iade_adedi
                              THEN e.adet - e.iade_adedi ELSE 0 END), 0) AS emanette
    FROM urun u
    LEFT JOIN emanet e ON e.sira_no = u.sira_no
    {kosul}
    GROUP BY u.sira_no
    ORDER BY u.sira_no
"""


def _urun_satiri_isle(satir):
    d = dict(satir)
    # Pert (bozuk/arızalı) adetler stok adedinin içinde sayılır ama
    # emanet verilemez; bu yüzden müsait adetten düşülür.
    d["musait"] = d["stok_adedi"] - d["emanette"] - d["pert_adedi"]
    return d


def urun_ekle(raf_no, stok_adi, stok_adedi, giris_tarihi, pert_adedi=0):
    raf_no = (raf_no or "").strip()
    stok_adi = (stok_adi or "").strip()
    if not raf_no:
        raise ValueError("Raf no boş olamaz.")
    if not stok_adi:
        raise ValueError("Stok adı boş olamaz.")
    adet = pozitif_sayi(stok_adedi)
    if adet is None:
        raise ValueError("Stok adedi geçerli bir sayı olmalı.")
    pert = pozitif_sayi(pert_adedi)
    if pert is None:
        raise ValueError("Pert adedi geçerli bir sayı olmalı.")
    if pert > adet:
        raise ValueError("Pert adedi stok adedinden fazla olamaz.")
    if not giris_tarihi:
        raise ValueError("Stok giriş tarihi boş olamaz.")
    with baglanti() as con:
        if _stok_adi_cakisiyor(con, stok_adi):
            raise ValueError("Bu isimde bir stok zaten kayıtlı.")
        cur = con.execute(
            "INSERT INTO urun (raf_no, stok_adi, stok_adedi, pert_adedi, giris_tarihi) "
            "VALUES (?, ?, ?, ?, ?)",
            (raf_no, stok_adi, adet, pert, giris_tarihi),
        )
        return cur.lastrowid


def _stok_adi_cakisiyor(con, stok_adi, haric_sira_no=None):
    """Verilen isimde (Türkçe'ye duyarlı, büyük/küçük harf gözetmeksizin)
    başka bir stok kaydı olup olmadığını kontrol eder."""
    hedef = _tr_kucult(stok_adi)
    satirlar = con.execute("SELECT sira_no, stok_adi FROM urun").fetchall()
    for s in satirlar:
        if haric_sira_no is not None and s["sira_no"] == haric_sira_no:
            continue
        if _tr_kucult(s["stok_adi"]) == hedef:
            return True
    return False


def urun_ara(stok_adi=""):
    stok_adi = (stok_adi or "").strip()
    with baglanti() as con:
        sql = _URUN_SECIM_SQL.format(kosul="")
        satirlar = con.execute(sql).fetchall()
    urunler = [_urun_satiri_isle(s) for s in satirlar]
    if stok_adi:
        urunler = [u for u in urunler if _icerir(u["stok_adi"], stok_adi)]
    return urunler


def urun_getir(sira_no):
    with baglanti() as con:
        sql = _URUN_SECIM_SQL.format(kosul="WHERE u.sira_no = ?")
        satir = con.execute(sql, (sira_no,)).fetchone()
        return _urun_satiri_isle(satir) if satir else None


def urun_emanette_adedi(sira_no, con=None):
    sql = (
        "SELECT COALESCE(SUM(adet - iade_adedi), 0) AS toplam FROM emanet "
        "WHERE sira_no = ? AND adet > iade_adedi"
    )
    if con is not None:
        return con.execute(sql, (sira_no,)).fetchone()["toplam"]
    with baglanti() as c:
        return c.execute(sql, (sira_no,)).fetchone()["toplam"]


def urun_guncelle(sira_no, raf_no, stok_adi, stok_adedi, pert_adedi=0):
    raf_no = (raf_no or "").strip()
    stok_adi = (stok_adi or "").strip()
    if not raf_no:
        raise ValueError("Raf no boş olamaz.")
    if not stok_adi:
        raise ValueError("Stok adı boş olamaz.")
    adet = pozitif_sayi(stok_adedi)
    if adet is None:
        raise ValueError("Stok adedi geçerli bir sayı olmalı.")
    pert = pozitif_sayi(pert_adedi)
    if pert is None:
        raise ValueError("Pert adedi geçerli bir sayı olmalı.")
    if pert > adet:
        raise ValueError("Pert adedi stok adedinden fazla olamaz.")
    with baglanti() as con:
        var_mi = con.execute("SELECT 1 FROM urun WHERE sira_no = ?", (sira_no,)).fetchone()
        if not var_mi:
            raise ValueError("Stok kaydı bulunamadı.")
        if _stok_adi_cakisiyor(con, stok_adi, haric_sira_no=sira_no):
            raise ValueError("Bu isimde başka bir stok zaten kayıtlı.")
        emanette = urun_emanette_adedi(sira_no, con)
        # Emanetteki ve pert adetler stok adedinin içinde olmak zorunda.
        if adet < emanette + pert:
            if pert:
                raise ValueError(
                    f"Bu üründen {emanette} adet emanette, {pert} adet pert; "
                    f"stok adedi {emanette + pert} adedin altına indirilemez."
                )
            raise ValueError(
                f"Bu üründen {emanette} adet emanette, stok adedi "
                f"{emanette} adedin altına indirilemez."
            )
        con.execute(
            "UPDATE urun SET raf_no = ?, stok_adi = ?, stok_adedi = ?, pert_adedi = ? "
            "WHERE sira_no = ?",
            (raf_no, stok_adi, adet, pert, sira_no),
        )


def urun_sil(sira_no):
    with baglanti() as con:
        var_mi = con.execute("SELECT 1 FROM urun WHERE sira_no = ?", (sira_no,)).fetchone()
        if not var_mi:
            raise ValueError("Stok kaydı bulunamadı.")
        emanette = urun_emanette_adedi(sira_no, con)
        if emanette > 0:
            raise ValueError(
                f"Bu stok üzerinde {emanette} adet emanet bulunuyor, silinemez."
            )
        # Açık emanet yok; bu ürüne ait kapanmış (tamamen iade edilmiş)
        # emanet geçmişi varsa, dış anahtar kısıtı silmeyi engellemesin diye
        # önce onu temizliyoruz.
        con.execute("DELETE FROM emanet WHERE sira_no = ?", (sira_no,))
        con.execute("DELETE FROM urun WHERE sira_no = ?", (sira_no,))


# --------------------------------------------------------------------------
# ÜYE
# --------------------------------------------------------------------------

def uye_ekle(uye_adi, tc, telefon, adres):
    uye_adi = (uye_adi or "").strip()
    tc = (tc or "").strip()
    telefon = (telefon or "").strip()
    adres = (adres or "").strip()
    if not uye_adi:
        raise ValueError("Üye adı boş olamaz.")
    if not tc_gecerli(tc):
        raise ValueError("Üye TC 11 haneli ve sadece rakamlardan oluşmalı.")
    if not telefon_gecerli(telefon):
        raise ValueError("Telefon no 10 haneli ve sadece rakamlardan oluşmalı.")
    with baglanti() as con:
        var_mi = con.execute("SELECT 1 FROM uye WHERE tc = ?", (tc,)).fetchone()
        if var_mi:
            raise ValueError("Bu TC numarasına sahip bir üye zaten kayıtlı.")
        cur = con.execute(
            "INSERT INTO uye (uye_adi, tc, telefon, adres) VALUES (?, ?, ?, ?)",
            (uye_adi, tc, telefon, adres),
        )
        return cur.lastrowid


def uye_ara(kriter, deger):
    """kriter: 'tc' | 'telefon' | 'ad'"""
    deger = (deger or "").strip()
    with baglanti() as con:
        satirlar = con.execute("SELECT * FROM uye ORDER BY uye_no").fetchall()
    uyeler = [dict(s) for s in satirlar]
    if not deger:
        return uyeler
    if kriter == "tc":
        return [u for u in uyeler if deger in (u["tc"] or "")]
    if kriter == "telefon":
        return [u for u in uyeler if deger in (u["telefon"] or "")]
    return [u for u in uyeler if _icerir(u["uye_adi"], deger)]  # ad


def uye_getir(uye_no):
    with baglanti() as con:
        satir = con.execute("SELECT * FROM uye WHERE uye_no = ?", (uye_no,)).fetchone()
        return dict(satir) if satir else None


def uye_guncelle(uye_no, uye_adi, tc, telefon, adres):
    uye_adi = (uye_adi or "").strip()
    tc = (tc or "").strip()
    telefon = (telefon or "").strip()
    adres = (adres or "").strip()
    if not uye_adi:
        raise ValueError("Üye adı boş olamaz.")
    if not tc_gecerli(tc):
        raise ValueError("Üye TC 11 haneli ve sadece rakamlardan oluşmalı.")
    if not telefon_gecerli(telefon):
        raise ValueError("Telefon no 10 haneli ve sadece rakamlardan oluşmalı.")
    with baglanti() as con:
        var_mi = con.execute("SELECT 1 FROM uye WHERE uye_no = ?", (uye_no,)).fetchone()
        if not var_mi:
            raise ValueError("Üye kaydı bulunamadı.")
        cakisan = con.execute(
            "SELECT 1 FROM uye WHERE tc = ? AND uye_no != ?", (tc, uye_no)
        ).fetchone()
        if cakisan:
            raise ValueError("Bu TC numarasına sahip başka bir üye zaten kayıtlı.")
        con.execute(
            "UPDATE uye SET uye_adi = ?, tc = ?, telefon = ?, adres = ? WHERE uye_no = ?",
            (uye_adi, tc, telefon, adres, uye_no),
        )


def uye_acik_emanet_adedi(uye_no, con=None):
    sql = (
        "SELECT COALESCE(SUM(adet - iade_adedi), 0) AS toplam FROM emanet "
        "WHERE uye_no = ? AND adet > iade_adedi"
    )
    if con is not None:
        return con.execute(sql, (uye_no,)).fetchone()["toplam"]
    with baglanti() as c:
        return c.execute(sql, (uye_no,)).fetchone()["toplam"]


def uye_sil(uye_no):
    with baglanti() as con:
        var_mi = con.execute("SELECT 1 FROM uye WHERE uye_no = ?", (uye_no,)).fetchone()
        if not var_mi:
            raise ValueError("Üye kaydı bulunamadı.")
        emanette = uye_acik_emanet_adedi(uye_no, con)
        if emanette > 0:
            raise ValueError(
                f"Bu üyenin {emanette} adet açık emaneti var, silinemez."
            )
        # Açık emaneti yok; bu üyeye ait kapanmış (tamamen iade edilmiş)
        # emanet geçmişi varsa, dış anahtar kısıtı silmeyi engellemesin diye
        # önce onu temizliyoruz.
        con.execute("DELETE FROM emanet WHERE uye_no = ?", (uye_no,))
        con.execute("DELETE FROM uye WHERE uye_no = ?", (uye_no,))


# --------------------------------------------------------------------------
# EMANET
# --------------------------------------------------------------------------

def emanet_ver(uye_no, sira_no, adet):
    adet = pozitif_sayi(adet)
    if not adet or adet <= 0:
        raise ValueError("Verilecek adet geçerli bir pozitif sayı olmalı.")
    with baglanti() as con:
        urun = con.execute("SELECT * FROM urun WHERE sira_no = ?", (sira_no,)).fetchone()
        if not urun:
            raise ValueError("Stok kaydı bulunamadı.")
        uye = con.execute("SELECT * FROM uye WHERE uye_no = ?", (uye_no,)).fetchone()
        if not uye:
            raise ValueError("Üye kaydı bulunamadı.")
        emanette = urun_emanette_adedi(sira_no, con)
        pert = urun["pert_adedi"]
        # Pert (bozuk/arızalı) adetler emanet verilemez, müsaitten düşülür.
        musait = urun["stok_adedi"] - emanette - pert
        if musait <= 0 and pert > 0:
            raise ValueError(
                f"Bu üründen müsait adet yok ({pert} adet pert, "
                f"{emanette} adet emanette)."
            )
        if adet > musait:
            raise ValueError(
                f"Müsait adetten fazla verilemez. Müsait: {musait}, istenen: {adet}."
            )
        con.execute(
            "INSERT INTO emanet (uye_no, sira_no, adet, iade_adedi, veris_tarihi) "
            "VALUES (?, ?, ?, 0, ?)",
            (uye_no, sira_no, adet, bugun()),
        )


def acik_emanetler(uye_no):
    """Üyenin açık (tamamen teslim alınmamış) emanet kayıtlarını döner."""
    with baglanti() as con:
        satirlar = con.execute(
            """
            SELECT e.emanet_no, e.uye_no, e.sira_no, e.adet, e.iade_adedi,
                   e.veris_tarihi, e.teslim_tarihi,
                   u.stok_adi, u.raf_no,
                   (e.adet - e.iade_adedi) AS kalan
            FROM emanet e
            JOIN urun u ON u.sira_no = e.sira_no
            WHERE e.uye_no = ? AND e.adet > e.iade_adedi
            ORDER BY e.emanet_no
            """,
            (uye_no,),
        ).fetchall()
        return [dict(s) for s in satirlar]


def emanet_teslim_al(emanet_no, adet):
    adet = pozitif_sayi(adet)
    if not adet or adet <= 0:
        raise ValueError("Teslim alınacak adet geçerli bir pozitif sayı olmalı.")
    with baglanti() as con:
        kayit = con.execute(
            "SELECT * FROM emanet WHERE emanet_no = ?", (emanet_no,)
        ).fetchone()
        if not kayit:
            raise ValueError("Emanet kaydı bulunamadı.")
        kalan = kayit["adet"] - kayit["iade_adedi"]
        if adet > kalan:
            raise ValueError(
                f"Teslim alınacak adet kalan miktardan fazla olamaz. Kalan: {kalan}."
            )
        yeni_iade = kayit["iade_adedi"] + adet
        teslim_tarihi = bugun() if yeni_iade >= kayit["adet"] else None
        con.execute(
            "UPDATE emanet SET iade_adedi = ?, teslim_tarihi = ? WHERE emanet_no = ?",
            (yeni_iade, teslim_tarihi, emanet_no),
        )
