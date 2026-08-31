# -*- coding: utf-8 -*-
"""Üye Kayıt / Üye Ara-Düzelt / Üye Sil sayfaları."""

import tkinter as tk
from tkinter import ttk

import veritabani as db
from arayuz.ortak import (
    Sayfa, tablo_olustur, form_satiri, entry_ayarla, hata, bilgi, onay, turkce_klavye_duzelt,
)


UYE_SUTUNLARI = [
    ("uye_no", "Üye No", 60),
    ("uye_adi", "Üye Adı", 150),
    ("tc", "TC", 100),
    ("telefon", "Telefon", 110),
    ("adres", "Adres", 220),
]


def _tabloya_doldur(tv, uyeler):
    tv.delete(*tv.get_children())
    for u in uyeler:
        tv.insert("", "end", iid=str(u["uye_no"]), values=(
            u["uye_no"], u["uye_adi"], u["tc"], u["telefon"] or "", u["adres"] or "",
        ))


class UyeKayit(Sayfa):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Üye Kayıt")

        form = ttk.Frame(self.icerik)
        form.pack(anchor="w", pady=10)

        self.e_uye_adi = form_satiri(form, 0, "Üye Adı:")
        self.e_tc = form_satiri(form, 1, "Üye TC:")
        self.e_telefon = form_satiri(form, 2, "Telefon No:")

        ttk.Label(form, text="Adres:").grid(row=3, column=0, sticky="ne", padx=(0, 8), pady=4)
        self.t_adres = tk.Text(form, width=30, height=4)
        self.t_adres.grid(row=3, column=1, sticky="w", pady=4)
        turkce_klavye_duzelt(self.t_adres)

        ttk.Button(self.icerik, text="Kaydet", command=self._kaydet).pack(
            anchor="w", pady=10
        )

        self._formu_sifirla()

    def goster(self):
        self._formu_sifirla()

    def _formu_sifirla(self):
        self.e_uye_adi.delete(0, tk.END)
        self.e_tc.delete(0, tk.END)
        self.e_telefon.delete(0, tk.END)
        self.t_adres.delete("1.0", tk.END)
        self.e_uye_adi.focus_set()

    def _kaydet(self):
        try:
            uye_no = db.uye_ekle(
                self.e_uye_adi.get(),
                self.e_tc.get(),
                self.e_telefon.get(),
                self.t_adres.get("1.0", tk.END).strip(),
            )
        except ValueError as e:
            hata(str(e))
            return
        bilgi(f"Üye kaydedildi. Üye No: {uye_no}")
        self._formu_sifirla()


class _AramaKarti(ttk.Frame):
    """Üye Ara-Düzelt ve Üye Sil'in paylaştığı arama bloğu (TC/Telefon/Ad)."""

    def __init__(self, parent, ara_callback):
        super().__init__(parent)
        self.kriter = tk.StringVar(value="ad")

        ttk.Radiobutton(
            self, text="Ad", variable=self.kriter, value="ad", command=ara_callback
        ).pack(side="left")
        ttk.Radiobutton(
            self, text="TC", variable=self.kriter, value="tc", command=ara_callback
        ).pack(side="left")
        ttk.Radiobutton(
            self, text="Telefon", variable=self.kriter, value="telefon", command=ara_callback
        ).pack(side="left")

        self.e_arama = ttk.Entry(self, width=25)
        self.e_arama.pack(side="left", padx=8)
        turkce_klavye_duzelt(self.e_arama)
        self.e_arama.bind("<Return>", lambda ev: ara_callback())
        self.e_arama.bind("<KeyRelease>", lambda ev: ara_callback(), add="+")

    def deger(self):
        return self.kriter.get(), self.e_arama.get()


class UyeAraDuzelt(Sayfa):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Üye Ara / Düzelt")

        self.arama = _AramaKarti(self.icerik, self._ara)
        self.arama.pack(fill="x", pady=(0, 10))

        self.tv, tv_cerceve = tablo_olustur(self.icerik, UYE_SUTUNLARI, yukseklik=9)
        tv_cerceve.pack(fill="both", expand=True, pady=(0, 10))
        self.tv.bind("<<TreeviewSelect>>", self._secildi)

        duzelt = ttk.LabelFrame(self.icerik, text="Seçili Üyeyi Düzelt", padding=10)
        duzelt.pack(fill="x")

        self.e_uye_no = form_satiri(duzelt, 0, "Üye No:", salt_okunur=True)
        self.e_uye_adi = form_satiri(duzelt, 1, "Üye Adı:")
        self.e_tc = form_satiri(duzelt, 2, "Üye TC:")
        self.e_telefon = form_satiri(duzelt, 3, "Telefon No:")

        ttk.Label(duzelt, text="Adres:").grid(row=4, column=0, sticky="ne", padx=(0, 8), pady=4)
        self.t_adres = tk.Text(duzelt, width=30, height=3)
        self.t_adres.grid(row=4, column=1, sticky="w", pady=4)
        turkce_klavye_duzelt(self.t_adres)

        ttk.Button(duzelt, text="Güncelle", command=self._guncelle).grid(
            row=5, column=1, sticky="w", pady=8
        )

        self._secili_uye_no = None

    def goster(self):
        self._ara()

    def _ara(self):
        kriter, deger = self.arama.deger()
        uyeler = db.uye_ara(kriter, deger)
        _tabloya_doldur(self.tv, uyeler)
        self._formu_temizle()

    def _secildi(self, event):
        secim = self.tv.selection()
        if not secim:
            return
        uye_no = int(secim[0])
        uye = db.uye_getir(uye_no)
        if not uye:
            return
        self._secili_uye_no = uye_no
        entry_ayarla(self.e_uye_no, uye["uye_no"])
        self.e_uye_adi.delete(0, tk.END)
        self.e_uye_adi.insert(0, uye["uye_adi"])
        self.e_tc.delete(0, tk.END)
        self.e_tc.insert(0, uye["tc"])
        self.e_telefon.delete(0, tk.END)
        self.e_telefon.insert(0, uye["telefon"] or "")
        self.t_adres.delete("1.0", tk.END)
        self.t_adres.insert("1.0", uye["adres"] or "")

    def _formu_temizle(self):
        self._secili_uye_no = None
        entry_ayarla(self.e_uye_no, "")
        self.e_uye_adi.delete(0, tk.END)
        self.e_tc.delete(0, tk.END)
        self.e_telefon.delete(0, tk.END)
        self.t_adres.delete("1.0", tk.END)

    def _guncelle(self):
        if self._secili_uye_no is None:
            hata("Önce tablodan bir üye seçin.")
            return
        try:
            db.uye_guncelle(
                self._secili_uye_no,
                self.e_uye_adi.get(),
                self.e_tc.get(),
                self.e_telefon.get(),
                self.t_adres.get("1.0", tk.END).strip(),
            )
        except ValueError as e:
            hata(str(e))
            return
        bilgi("Üye güncellendi.")
        self._ara()


class UyeSil(Sayfa):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Üye Sil")

        self.arama = _AramaKarti(self.icerik, self._ara)
        self.arama.pack(fill="x", pady=(0, 10))

        self.tv, tv_cerceve = tablo_olustur(self.icerik, UYE_SUTUNLARI, yukseklik=14)
        tv_cerceve.pack(fill="both", expand=True, pady=(0, 10))

        ttk.Button(self.icerik, text="Seçili Üyeyi Sil", command=self._sil).pack(anchor="w")

    def goster(self):
        self._ara()

    def _ara(self):
        kriter, deger = self.arama.deger()
        uyeler = db.uye_ara(kriter, deger)
        _tabloya_doldur(self.tv, uyeler)

    def _sil(self):
        secim = self.tv.selection()
        if not secim:
            hata("Önce tablodan bir üye seçin.")
            return
        uye_no = int(secim[0])
        uye = db.uye_getir(uye_no)
        if not uye:
            return
        if not onay(f"'{uye['uye_adi']}' adlı üye silinsin mi?"):
            return
        try:
            db.uye_sil(uye_no)
        except ValueError as e:
            hata(str(e))
            return
        bilgi("Üye silindi.")
        self._ara()
