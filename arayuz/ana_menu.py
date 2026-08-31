# -*- coding: utf-8 -*-
"""Ana menü: sol üst STOK, sağ üst ÜYE, alt EMANET bölmeleri."""

from tkinter import ttk

from arayuz.ortak import Sayfa


class AnaMenu(Sayfa):
    def __init__(self, parent, controller):
        # Ana menüde geri dönülecek üst bir başlık çubuğu yok, o yüzden
        # taban sınıfı kullanmak yerine kendi düzenini kuruyoruz.
        ttk.Frame.__init__(self, parent)
        self.controller = controller

        ttk.Label(
            self, text="STOK TAKİP SİSTEMİ", font=("Segoe UI", 18, "bold")
        ).grid(row=0, column=0, columnspan=2, pady=(20, 15))

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=3)
        self.rowconfigure(2, weight=2)

        stok_cerceve = ttk.LabelFrame(self, text="STOK", padding=15)
        stok_cerceve.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)
        self._buton(stok_cerceve, "Stok Giriş", "stok_giris")
        self._buton(stok_cerceve, "Stok Ara / Düzelt", "stok_ara")
        self._buton(stok_cerceve, "Stok Sil", "stok_sil")

        uye_cerceve = ttk.LabelFrame(self, text="ÜYE", padding=15)
        uye_cerceve.grid(row=1, column=1, sticky="nsew", padx=15, pady=10)
        self._buton(uye_cerceve, "Üye Kayıt", "uye_kayit")
        self._buton(uye_cerceve, "Üye Ara / Düzelt", "uye_ara")
        self._buton(uye_cerceve, "Üye Sil", "uye_sil")

        emanet_cerceve = ttk.LabelFrame(self, text="EMANET", padding=15)
        emanet_cerceve.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=15, pady=10)
        emanet_cerceve.columnconfigure(0, weight=1)
        emanet_cerceve.columnconfigure(1, weight=1)
        ttk.Button(
            emanet_cerceve, text="Emanet Ver",
            command=lambda: controller.sayfa_goster("emanet_ver"),
        ).grid(row=0, column=0, sticky="ew", padx=10, pady=10, ipady=8)
        ttk.Button(
            emanet_cerceve, text="Emanet Teslim Al",
            command=lambda: controller.sayfa_goster("emanet_al"),
        ).grid(row=0, column=1, sticky="ew", padx=10, pady=10, ipady=8)

    def _buton(self, parent, metin, hedef):
        ttk.Button(
            parent, text=metin,
            command=lambda: self.controller.sayfa_goster(hedef),
        ).pack(fill="x", pady=6, ipady=6)

    def goster(self):
        pass
