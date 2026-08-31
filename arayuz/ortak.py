# -*- coding: utf-8 -*-
"""Sayfa taban sınıfı ve tüm arayuz modüllerinin paylaştığı yardımcılar."""

import tkinter as tk
from tkinter import ttk, messagebox

import veritabani as db


def hata(mesaj):
    messagebox.showerror("Hata", mesaj)


def bilgi(mesaj):
    messagebox.showinfo("Bilgi", mesaj)


def onay(mesaj):
    return messagebox.askyesno("Onay", mesaj)


class Sayfa(ttk.Frame):
    """Tüm alt sayfaların taban sınıfı.

    Üstte başlık + "Ana Menü" butonu bulunur. Alt sınıflar içerik
    alanına (self.icerik) widget'larını ekler. Sayfa her açıldığında
    goster() çağrılır; alt sınıflar burada listelerini tazeleyebilir.
    """

    def __init__(self, parent, controller, baslik):
        super().__init__(parent)
        self.controller = controller

        ust_cubuk = ttk.Frame(self, padding=(10, 10, 10, 0))
        ust_cubuk.pack(fill="x")

        ttk.Button(
            ust_cubuk, text="◀ Ana Menü",
            command=lambda: controller.sayfa_goster("ana_menu"),
        ).pack(side="left")

        ttk.Label(ust_cubuk, text=baslik, font=("Segoe UI", 14, "bold")).pack(
            side="left", padx=20
        )

        ttk.Separator(self).pack(fill="x", pady=(8, 0))

        self.icerik = ttk.Frame(self, padding=10)
        self.icerik.pack(fill="both", expand=True)

    def goster(self):
        """Sayfa ekrana getirildiğinde çağrılır. Alt sınıf isterse override eder."""
        pass


def tablo_olustur(parent, sutunlar, yukseklik=10):
    """sutunlar: [(id, baslik, genislik), ...] biçiminde liste.
    (Treeview, çerçeve) döndürür; çerçeveyi grid/pack ile yerleştir."""
    cerceve = ttk.Frame(parent)
    kimlikler = [s[0] for s in sutunlar]
    tv = ttk.Treeview(cerceve, columns=kimlikler, show="headings", height=yukseklik)
    for kimlik, baslik, genislik in sutunlar:
        tv.heading(kimlik, text=baslik)
        tv.column(kimlik, width=genislik, anchor="center")
    dikey = ttk.Scrollbar(cerceve, orient="vertical", command=tv.yview)
    tv.configure(yscrollcommand=dikey.set)
    tv.grid(row=0, column=0, sticky="nsew")
    dikey.grid(row=0, column=1, sticky="ns")
    cerceve.columnconfigure(0, weight=1)
    cerceve.rowconfigure(0, weight=1)
    return tv, cerceve


def form_satiri(parent, satir, etiket, salt_okunur=False, genislik=30):
    """Hizalı Label + Entry çifti oluşturur ve Entry'yi döndürür."""
    ttk.Label(parent, text=etiket).grid(row=satir, column=0, sticky="e", padx=(0, 8), pady=4)
    girdi = ttk.Entry(parent, width=genislik)
    if salt_okunur:
        girdi.configure(state="readonly")
    girdi.grid(row=satir, column=1, sticky="w", pady=4)
    return girdi


def entry_ayarla(entry, deger):
    """readonly olsa bile Entry içeriğini günceller."""
    onceki_durum = entry.cget("state")
    entry.configure(state="normal")
    entry.delete(0, tk.END)
    entry.insert(0, "" if deger is None else str(deger))
    entry.configure(state=onceki_durum)


def sayi_dogrula(metin, alan_adi):
    """Metni pozitif tam sayıya çevirir; geçersizse ValueError fırlatır."""
    deger = db.pozitif_sayi(metin)
    if deger is None:
        raise ValueError(f"{alan_adi} geçerli bir sayı olmalı.")
    return deger
