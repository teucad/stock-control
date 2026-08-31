# -*- coding: utf-8 -*-
"""Stok Takip Sistemi - Uygulama girişi."""

import tkinter as tk
from tkinter import ttk

import veritabani as db
from arayuz.ana_menu import AnaMenu
from arayuz.stok import StokGiris, StokAraDuzelt, StokSil
from arayuz.uye import UyeKayit, UyeAraDuzelt, UyeSil
from arayuz.emanet import EmanetVer, EmanetAl


class Uygulama(tk.Tk):
    def __init__(self):
        super().__init__()
        # Windows'ta konsol kod sayfası (ör. Türkçe 857/1254) Tcl/Tk'nin
        # klavyeden gelen Türkçe karakterleri (ç, ğ, ı, ö, ş, ü) yanlış
        # yorumlamasına yol açabiliyor; iç kodlamayı burada açıkça UTF-8'e
        # sabitliyoruz.
        self.tk.call("encoding", "system", "utf-8")
        self.option_add("*Font", ("Segoe UI", 10))
        self.title("Stok Takip Sistemi")
        self.geometry("950x680")
        self.minsize(800, 600)

        kapsayici = ttk.Frame(self)
        kapsayici.pack(fill="both", expand=True)
        kapsayici.columnconfigure(0, weight=1)
        kapsayici.rowconfigure(0, weight=1)

        self._sayfalar = {}
        sinif_haritasi = {
            "ana_menu": AnaMenu,
            "stok_giris": StokGiris,
            "stok_ara": StokAraDuzelt,
            "stok_sil": StokSil,
            "uye_kayit": UyeKayit,
            "uye_ara": UyeAraDuzelt,
            "uye_sil": UyeSil,
            "emanet_ver": EmanetVer,
            "emanet_al": EmanetAl,
        }
        for ad, Sinif in sinif_haritasi.items():
            sayfa = Sinif(kapsayici, self)
            self._sayfalar[ad] = sayfa
            sayfa.grid(row=0, column=0, sticky="nsew")

        self.sayfa_goster("ana_menu")

    def sayfa_goster(self, ad):
        sayfa = self._sayfalar[ad]
        sayfa.tkraise()
        sayfa.goster()


if __name__ == "__main__":
    db.sema_kur()
    uygulama = Uygulama()
    uygulama.mainloop()
