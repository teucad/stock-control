# -*- coding: utf-8 -*-
"""Emanet Ver / Emanet Teslim Al sayfaları."""

import tkinter as tk
from tkinter import ttk

import veritabani as db
from arayuz.ortak import (
    Sayfa, tablo_olustur, form_satiri, entry_ayarla, hata, bilgi, turkce_klavye_duzelt,
)
from arayuz.uye import _AramaKarti, UYE_SUTUNLARI
from arayuz.stok import STOK_SUTUNLARI


def _uye_tabloya_doldur(tv, uyeler):
    tv.delete(*tv.get_children())
    for u in uyeler:
        tv.insert("", "end", iid=str(u["uye_no"]), values=(
            u["uye_no"], u["uye_adi"], u["tc"], u["telefon"] or "", u["adres"] or "",
        ))


def _urun_tabloya_doldur(tv, urunler):
    tv.delete(*tv.get_children())
    for u in urunler:
        tv.insert("", "end", iid=str(u["sira_no"]), values=(
            u["sira_no"], u["raf_no"], u["stok_adi"], u["stok_adedi"],
            u["emanette"], u["musait"], db.tarih_goster(u["giris_tarihi"]),
        ))


EMANET_SUTUNLARI = [
    ("emanet_no", "Emanet No", 80),
    ("stok_adi", "Stok Adı", 160),
    ("raf_no", "Raf No", 70),
    ("adet", "Verilen", 70),
    ("iade_adedi", "İade", 60),
    ("kalan", "Kalan", 60),
    ("veris_tarihi", "Veriş Tarihi", 140),
]


def _emanet_tabloya_doldur(tv, kayitlar):
    tv.delete(*tv.get_children())
    for k in kayitlar:
        tv.insert("", "end", iid=str(k["emanet_no"]), values=(
            k["emanet_no"], k["stok_adi"], k["raf_no"], k["adet"],
            k["iade_adedi"], k["kalan"], db.tarih_goster(k["veris_tarihi"]),
        ))


class EmanetVer(Sayfa):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Emanet Ver")

        self._secili_uye = None
        self._secili_urun = None

        # --- Üye seçimi ---
        uye_blok = ttk.LabelFrame(self.icerik, text="1) Üye Seç", padding=8)
        uye_blok.pack(fill="both", expand=True)

        self.uye_arama = _AramaKarti(uye_blok, self._uye_ara)
        self.uye_arama.pack(fill="x", pady=(0, 6))

        self.uye_tv, uye_tv_cerceve = tablo_olustur(uye_blok, UYE_SUTUNLARI, yukseklik=5)
        uye_tv_cerceve.pack(fill="both", expand=True)
        self.uye_tv.bind("<<TreeviewSelect>>", self._uye_secildi)

        self.l_secili_uye = ttk.Label(self.icerik, text="Seçilen üye: —", font=("Segoe UI", 10, "bold"))
        self.l_secili_uye.pack(anchor="w", pady=(6, 10))

        # --- Malzeme seçimi ---
        urun_blok = ttk.LabelFrame(self.icerik, text="2) Malzeme Seç", padding=8)
        urun_blok.pack(fill="both", expand=True)

        arama = ttk.Frame(urun_blok)
        arama.pack(fill="x", pady=(0, 6))
        ttk.Label(arama, text="Stok Adı:").pack(side="left")
        self.e_urun_arama = ttk.Entry(arama, width=25)
        turkce_klavye_duzelt(self.e_urun_arama)
        self.e_urun_arama.pack(side="left", padx=8)
        self.e_urun_arama.bind("<Return>", lambda ev: self._urun_ara())
        self.e_urun_arama.bind("<KeyRelease>", lambda ev: self._urun_ara(), add="+")

        self.urun_tv, urun_tv_cerceve = tablo_olustur(urun_blok, STOK_SUTUNLARI, yukseklik=5)
        urun_tv_cerceve.pack(fill="both", expand=True)
        self.urun_tv.bind("<<TreeviewSelect>>", self._urun_secildi)

        self.l_secili_urun = ttk.Label(self.icerik, text="Seçilen malzeme: —", font=("Segoe UI", 10, "bold"))
        self.l_secili_urun.pack(anchor="w", pady=(6, 6))

        # --- Adet + ver ---
        alt = ttk.Frame(self.icerik)
        alt.pack(fill="x", pady=(0, 6))
        ttk.Label(alt, text="Verilecek Adet:").pack(side="left")
        self.e_adet = ttk.Entry(alt, width=10)
        self.e_adet.pack(side="left", padx=8)
        ttk.Button(alt, text="Emanet Ver", command=self._emanet_ver).pack(side="left")

        # --- Üyenin mevcut açık emanetleri ---
        mevcut_blok = ttk.LabelFrame(self.icerik, text="Üyenin Mevcut Açık Emanetleri", padding=8)
        mevcut_blok.pack(fill="both", expand=True, pady=(6, 0))
        self.mevcut_tv, mevcut_cerceve = tablo_olustur(mevcut_blok, EMANET_SUTUNLARI, yukseklik=4)
        mevcut_cerceve.pack(fill="both", expand=True)

    def goster(self):
        self._secili_uye = None
        self._secili_urun = None
        self.l_secili_uye.config(text="Seçilen üye: —")
        self.l_secili_urun.config(text="Seçilen malzeme: —")
        self.e_adet.delete(0, tk.END)
        self._uye_ara()
        self._urun_ara()
        self.mevcut_tv.delete(*self.mevcut_tv.get_children())

    def _uye_ara(self):
        kriter, deger = self.uye_arama.deger()
        _uye_tabloya_doldur(self.uye_tv, db.uye_ara(kriter, deger))

    def _urun_ara(self):
        _urun_tabloya_doldur(self.urun_tv, db.urun_ara(self.e_urun_arama.get()))

    def _uye_secildi(self, event):
        secim = self.uye_tv.selection()
        if not secim:
            return
        uye_no = int(secim[0])
        uye = db.uye_getir(uye_no)
        if not uye:
            return
        self._secili_uye = uye
        self.l_secili_uye.config(text=f"Seçilen üye: {uye['uye_adi']}  (TC: {uye['tc']})")
        _emanet_tabloya_doldur(self.mevcut_tv, db.acik_emanetler(uye_no))

    def _urun_secildi(self, event):
        secim = self.urun_tv.selection()
        if not secim:
            return
        sira_no = int(secim[0])
        urun = db.urun_getir(sira_no)
        if not urun:
            return
        self._secili_urun = urun
        self.l_secili_urun.config(
            text=f"Seçilen malzeme: {urun['stok_adi']}  (Müsait: {urun['musait']})"
        )

    def _emanet_ver(self):
        if self._secili_uye is None:
            hata("Önce bir üye seçin.")
            return
        if self._secili_urun is None:
            hata("Önce bir malzeme seçin.")
            return
        try:
            db.emanet_ver(self._secili_uye["uye_no"], self._secili_urun["sira_no"], self.e_adet.get())
        except ValueError as e:
            hata(str(e))
            return
        bilgi("Emanet verildi.")
        self.e_adet.delete(0, tk.END)
        self._urun_ara()
        _emanet_tabloya_doldur(self.mevcut_tv, db.acik_emanetler(self._secili_uye["uye_no"]))
        # Malzemenin güncel müsait adedini yeniden getir
        urun = db.urun_getir(self._secili_urun["sira_no"])
        if urun:
            self._secili_urun = urun
            self.l_secili_urun.config(
                text=f"Seçilen malzeme: {urun['stok_adi']}  (Müsait: {urun['musait']})"
            )


class EmanetAl(Sayfa):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Emanet Teslim Al")

        self._secili_uye = None
        self._secili_emanet = None

        uye_blok = ttk.LabelFrame(self.icerik, text="1) Üye Seç", padding=8)
        uye_blok.pack(fill="both", expand=True)

        self.uye_arama = _AramaKarti(uye_blok, self._uye_ara)
        self.uye_arama.pack(fill="x", pady=(0, 6))

        self.uye_tv, uye_tv_cerceve = tablo_olustur(uye_blok, UYE_SUTUNLARI, yukseklik=5)
        uye_tv_cerceve.pack(fill="both", expand=True)
        self.uye_tv.bind("<<TreeviewSelect>>", self._uye_secildi)

        self.l_secili_uye = ttk.Label(self.icerik, text="Seçilen üye: —", font=("Segoe UI", 10, "bold"))
        self.l_secili_uye.pack(anchor="w", pady=(6, 10))

        emanet_blok = ttk.LabelFrame(self.icerik, text="2) Teslim Alınacak Malzemeler", padding=8)
        emanet_blok.pack(fill="both", expand=True)

        self.emanet_tv, emanet_cerceve = tablo_olustur(emanet_blok, EMANET_SUTUNLARI, yukseklik=8)
        emanet_cerceve.pack(fill="both", expand=True)
        self.emanet_tv.bind("<<TreeviewSelect>>", self._emanet_secildi)

        alt = ttk.Frame(self.icerik)
        alt.pack(fill="x", pady=(10, 0))
        ttk.Label(alt, text="Teslim Alınacak Adet:").pack(side="left")
        self.e_adet = ttk.Entry(alt, width=10)
        self.e_adet.pack(side="left", padx=8)
        ttk.Button(alt, text="Teslim Al", command=self._teslim_al).pack(side="left")

    def goster(self):
        self._secili_uye = None
        self._secili_emanet = None
        self.l_secili_uye.config(text="Seçilen üye: —")
        self.e_adet.delete(0, tk.END)
        self.emanet_tv.delete(*self.emanet_tv.get_children())
        self._uye_ara()

    def _uye_ara(self):
        kriter, deger = self.uye_arama.deger()
        _uye_tabloya_doldur(self.uye_tv, db.uye_ara(kriter, deger))

    def _uye_secildi(self, event):
        secim = self.uye_tv.selection()
        if not secim:
            return
        uye_no = int(secim[0])
        uye = db.uye_getir(uye_no)
        if not uye:
            return
        self._secili_uye = uye
        self.l_secili_uye.config(text=f"Seçilen üye: {uye['uye_adi']}  (TC: {uye['tc']})")
        kayitlar = self._emanetleri_yenile()
        if not kayitlar:
            bilgi("Bu üyenin teslim alınacak emaneti bulunmuyor.")

    def _emanetleri_yenile(self):
        if self._secili_uye is None:
            return []
        kayitlar = db.acik_emanetler(self._secili_uye["uye_no"])
        _emanet_tabloya_doldur(self.emanet_tv, kayitlar)
        self.e_adet.delete(0, tk.END)
        self._secili_emanet = None
        return kayitlar

    def _emanet_secildi(self, event):
        secim = self.emanet_tv.selection()
        if not secim:
            return
        emanet_no = int(secim[0])
        for k in db.acik_emanetler(self._secili_uye["uye_no"]):
            if k["emanet_no"] == emanet_no:
                self._secili_emanet = k
                self.e_adet.delete(0, tk.END)
                self.e_adet.insert(0, str(k["kalan"]))
                break

    def _teslim_al(self):
        if self._secili_uye is None:
            hata("Önce bir üye seçin.")
            return
        if self._secili_emanet is None:
            hata("Önce teslim alınacak bir emanet kaydı seçin.")
            return
        try:
            db.emanet_teslim_al(self._secili_emanet["emanet_no"], self.e_adet.get())
        except ValueError as e:
            hata(str(e))
            return
        bilgi("Emanet teslim alındı.")
        self._emanetleri_yenile()
