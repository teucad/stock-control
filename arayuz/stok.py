# -*- coding: utf-8 -*-
"""Stok Giriş / Stok Ara-Düzelt / Stok Sil sayfaları."""

import tkinter as tk
from tkinter import ttk

import veritabani as db
from arayuz.ortak import (
    Sayfa, tablo_olustur, form_satiri, hata, bilgi, onay, turkce_klavye_duzelt,
)


STOK_SUTUNLARI = [
    ("sira_no", "Sıra No", 70),
    ("raf_no", "Raf No", 80),
    ("stok_adi", "Stok Adı", 200),
    ("toplam", "Toplam", 70),
    ("emanette", "Emanette", 80),
    ("pert_adedi", "Pert", 60),
    ("musait", "Müsait", 70),
    ("giris_tarihi", "Giriş Tarihi", 140),
]


def urun_tabloya_doldur(tv, urunler):
    """STOK_SUTUNLARI ile kurulmuş bir tabloyu ürün listesiyle doldurur."""
    tv.delete(*tv.get_children())
    for u in urunler:
        tv.insert("", "end", iid=str(u["sira_no"]), values=(
            u["sira_no"], u["raf_no"], u["stok_adi"], u["stok_adedi"],
            u["emanette"], u["pert_adedi"], u["musait"],
            db.tarih_goster(u["giris_tarihi"]),
        ))


class StokGiris(Sayfa):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Stok Giriş")

        form = ttk.Frame(self.icerik)
        form.pack(anchor="w", pady=10)

        self.e_raf_no = form_satiri(form, 0, "Raf No:")
        self.e_stok_adi = form_satiri(form, 1, "Stok Adı:")
        self.e_stok_adedi = form_satiri(form, 2, "Stok Adedi:")
        self.e_pert_adedi = form_satiri(form, 3, "Pert Adedi:")

        ttk.Button(self.icerik, text="Kaydet", command=self._kaydet).pack(
            anchor="w", pady=10
        )

        self._formu_sifirla()

    def goster(self):
        self._formu_sifirla()

    def _formu_sifirla(self):
        self.e_raf_no.delete(0, tk.END)
        self.e_stok_adi.delete(0, tk.END)
        self.e_stok_adedi.delete(0, tk.END)
        self.e_pert_adedi.delete(0, tk.END)
        self.e_pert_adedi.insert(0, "0")
        self.e_raf_no.focus_set()

    def _kaydet(self):
        try:
            sira_no = db.urun_ekle(
                self.e_raf_no.get(),
                self.e_stok_adi.get(),
                self.e_stok_adedi.get(),
                db.bugun(),
                self.e_pert_adedi.get(),
            )
        except ValueError as e:
            hata(str(e))
            return
        bilgi(f"Stok kaydedildi. Sıra No: {sira_no}")
        self._formu_sifirla()


class StokAraDuzelt(Sayfa):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Stok Ara / Düzelt")

        arama = ttk.Frame(self.icerik)
        arama.pack(fill="x", pady=(0, 10))
        ttk.Label(arama, text="Stok Adı:").pack(side="left")
        self.e_arama = ttk.Entry(arama, width=30)
        turkce_klavye_duzelt(self.e_arama)
        self.e_arama.pack(side="left", padx=8)
        self.e_arama.bind("<Return>", lambda ev: self._ara())
        self.e_arama.bind("<KeyRelease>", lambda ev: self._ara(), add="+")

        self.tv, tv_cerceve = tablo_olustur(self.icerik, STOK_SUTUNLARI, yukseklik=10)
        tv_cerceve.pack(fill="both", expand=True, pady=(0, 10))
        self.tv.bind("<<TreeviewSelect>>", self._secildi)

        duzelt = ttk.LabelFrame(self.icerik, text="Seçili Stoku Düzelt", padding=10)
        duzelt.pack(fill="x")

        self.e_raf_no = form_satiri(duzelt, 0, "Raf No:")
        self.e_stok_adi = form_satiri(duzelt, 1, "Stok Adı:")
        self.e_stok_adedi = form_satiri(duzelt, 2, "Stok Adedi:")
        self.e_pert_adedi = form_satiri(duzelt, 3, "Pert Adedi:")

        ttk.Button(duzelt, text="Güncelle", command=self._guncelle).grid(
            row=4, column=1, sticky="w", pady=8
        )

        self._secili_sira_no = None

    def goster(self):
        self._ara()

    def _ara(self):
        urunler = db.urun_ara(self.e_arama.get())
        urun_tabloya_doldur(self.tv, urunler)
        self._formu_temizle()

    def _secildi(self, event):
        secim = self.tv.selection()
        if not secim:
            return
        sira_no = int(secim[0])
        urun = db.urun_getir(sira_no)
        if not urun:
            return
        self._secili_sira_no = sira_no
        self.e_raf_no.delete(0, tk.END)
        self.e_raf_no.insert(0, urun["raf_no"])
        self.e_stok_adi.delete(0, tk.END)
        self.e_stok_adi.insert(0, urun["stok_adi"])
        self.e_stok_adedi.delete(0, tk.END)
        self.e_stok_adedi.insert(0, str(urun["stok_adedi"]))
        self.e_pert_adedi.delete(0, tk.END)
        self.e_pert_adedi.insert(0, str(urun["pert_adedi"]))

    def _formu_temizle(self):
        self._secili_sira_no = None
        self.e_raf_no.delete(0, tk.END)
        self.e_stok_adi.delete(0, tk.END)
        self.e_stok_adedi.delete(0, tk.END)
        self.e_pert_adedi.delete(0, tk.END)

    def _guncelle(self):
        if self._secili_sira_no is None:
            hata("Önce tablodan bir stok seçin.")
            return
        try:
            db.urun_guncelle(
                self._secili_sira_no,
                self.e_raf_no.get(),
                self.e_stok_adi.get(),
                self.e_stok_adedi.get(),
                self.e_pert_adedi.get(),
            )
        except ValueError as e:
            hata(str(e))
            return
        bilgi("Stok güncellendi.")
        self._ara()


class StokSil(Sayfa):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Stok Sil")

        arama = ttk.Frame(self.icerik)
        arama.pack(fill="x", pady=(0, 10))
        ttk.Label(arama, text="Stok Adı:").pack(side="left")
        self.e_arama = ttk.Entry(arama, width=30)
        turkce_klavye_duzelt(self.e_arama)
        self.e_arama.pack(side="left", padx=8)
        self.e_arama.bind("<Return>", lambda ev: self._ara())
        self.e_arama.bind("<KeyRelease>", lambda ev: self._ara(), add="+")

        self.tv, tv_cerceve = tablo_olustur(self.icerik, STOK_SUTUNLARI, yukseklik=14)
        tv_cerceve.pack(fill="both", expand=True, pady=(0, 10))

        ttk.Button(self.icerik, text="Seçili Stoku Sil", command=self._sil).pack(anchor="w")

    def goster(self):
        self._ara()

    def _ara(self):
        urunler = db.urun_ara(self.e_arama.get())
        urun_tabloya_doldur(self.tv, urunler)

    def _sil(self):
        secim = self.tv.selection()
        if not secim:
            hata("Önce tablodan bir stok seçin.")
            return
        sira_no = int(secim[0])
        urun = db.urun_getir(sira_no)
        if not urun:
            return
        if not onay(f"'{urun['stok_adi']}' adlı stok silinsin mi?"):
            return
        try:
            db.urun_sil(sira_no)
        except ValueError as e:
            hata(str(e))
            return
        bilgi("Stok silindi.")
        self._ara()
