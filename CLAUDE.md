# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

"Stok Takip Sistemi" (Stock Tracking System) — a desktop Tkinter/ttk app backed by SQLite, for tracking
shelved inventory (`urun`), members (`uye`), and items lent out to members (`emanet`, i.e. "custody/loan"
records). All identifiers, UI text, and error messages are in Turkish; comments and docstrings are Turkish too.
Match that convention when writing or editing code here.

## Running

```
python main.py
```

No build step, no test suite, no linter, and no `requirements.txt` — the app only depends on the Python
standard library (`tkinter`, `sqlite3`). There is no packaging/dist step; run directly from source.

## Architecture

Three-layer split, strictly enforced:

- **`veritabani.py`** (data layer) — owns *all* SQLite access and business rules. UI code never writes SQL
  directly; it only calls functions exported from this module. Every write path opens a connection via the
  `baglanti()` context manager, which enables `PRAGMA foreign_keys = ON` and commits/rolls back automatically.
  Business-rule violations (e.g. deleting a product/member that has open loans, exceeding available quantity,
  duplicate TC/stock name) raise `ValueError` with a Turkish message — the UI layer catches this and shows it
  via `messagebox`. `sema_kur()` creates the schema on first run (called once from `main.py` before the Tk
  event loop starts).

- **`arayuz/`** (UI layer, package) — one Tkinter `ttk.Frame` subclass per screen, all pages instantiated
  once up front and swapped via `tkraise()` (see `main.py`'s `sayfa_goster`):
  - `ortak.py` — shared base class `Sayfa` (header bar + "Ana Menü" back button + content frame), plus shared
    widget helpers (`tablo_olustur` for Treeview+scrollbar tables, `form_satiri` for label+entry rows,
    `hata`/`bilgi`/`onay` for message dialogs) and `turkce_klavye_duzelt` (see Known quirks below).
  - `ana_menu.py` — the home screen (`AnaMenu`), not a `Sayfa` subclass since it has no back button.
  - `stok.py`, `uye.py`, `emanet.py` — one module per domain, each holding multiple `Sayfa` subclasses
    (e.g. `StokGiris`/`StokAraDuzelt`/`StokSil` for create/search-edit/delete of products).
  - Every `Sayfa` subclass overrides `goster()`, called each time `main.py` switches to that page, to
    reset/refresh the page's state (e.g. clear a form, reload a table).

- **`main.py`** — app entry point. Builds the `Uygulama(tk.Tk)` window, instantiates every page from a
  name→class map, and calls `db.sema_kur()` before starting the mainloop.

### Data model

- `urun` (product/stock item): `sira_no` PK, `raf_no` (shelf), `stok_adi` (name, must be unique
  case/Turkish-insensitively — enforced in Python via `_stok_adi_cakisiyor`, not a SQL constraint),
  `stok_adedi` (total quantity), `pert_adedi` (how many of those units are broken/defective, defaults 0),
  `giris_tarihi`. `pert_adedi` is a *subset* of `stok_adedi` — the item is physically on the shelf but
  unusable — so pert units are never lendable.
- `uye` (member): `uye_no` PK, `uye_adi`, `tc` (11-digit Turkish ID, unique), `telefon` (10-digit), `adres`.
- `emanet` (loan/custody record): `emanet_no` PK, FKs to `uye_no` and `sira_no`, `adet` (quantity loaned),
  `iade_adedi` (quantity returned so far, defaults 0), `veris_tarihi`, `teslim_tarihi` (set only once fully
  returned, i.e. `iade_adedi >= adet`). Loans support partial returns — `emanet_teslim_al` accepts an amount
  and adds to `iade_adedi` rather than closing the record outright.
- "Available" (`musait`) quantity for a product is always computed, not stored:
  `stok_adedi - emanette - pert_adedi`, where `emanette` sums `adet - iade_adedi` across all open loan rows
  for that product (see `_URUN_SECIM_SQL` / `urun_emanette_adedi`). Because pert units are subtracted here,
  `emanet_ver` rejects lending them without needing a separate rule. Reducing a product's `stok_adedi`
  below `emanette + pert_adedi`, or setting `pert_adedi` above `stok_adedi`, is rejected in
  `urun_guncelle`/`urun_ekle`.
- Deleting a product or member is blocked while it has open (not fully returned) loans. Once safe to delete,
  the code first purges that entity's *closed* loan history rows before deleting the entity itself, since
  `emanet.uye_no`/`emanet.sira_no` are `NOT NULL REFERENCES` with no `ON DELETE` clause.

### Known quirks worth preserving

- **Turkish keyboard/codepage fix**: `arayuz/ortak.py`'s `turkce_klavye_duzelt` binds a `<KeyRelease>`
  handler to Entry/Text widgets that detects and corrects mis-mapped Turkish characters (ş/ı/ğ and their
  uppercase forms arriving as Latin-1 lookalikes þ/ý/ð due to codepage mismatches on some Windows/Tcl-Tk
  setups). `main.py` also forces `self.tk.call("encoding", "system", "utf-8")` on startup. Any new
  text-entry widget should go through `form_satiri()` (which already wires this up) rather than creating a
  raw `ttk.Entry`.
- **Turkish-aware string comparisons**: use `db._tr_kucult`/`db._icerir` (or the public search functions)
  instead of Python's built-in `.lower()`/`in`, since `.lower()` mishandles Turkish İ/I.
- Dates are stored as `YYYY-MM-DD HH:MM:SS` strings (`db.bugun()`) and rendered for display via
  `db.tarih_goster()` (`DD.MM.YYYY HH:MM`) — don't reformat dates ad hoc in UI code.

## Database file

`stok.db` (SQLite) lives at the repo root next to `veritabani.py` and is gitignored — it's local runtime
state, not source. `sema_kur()` recreates the schema (via `CREATE TABLE IF NOT EXISTS`) if it's missing.
