"""Membuat schema database bila belum ada.

Dijalankan sebelum `migrate` saat deployment. Django tidak membuat schema
sendiri, sedangkan settings mengarahkan search_path ke schema `tugas_kelompok`,
sehingga migrate gagal bila schema tersebut belum tersedia di PostgreSQL.
"""

import os
import sys
from pathlib import Path

import django

# Skrip ini dijalankan dari subfolder, sehingga root proyek perlu ditambahkan
# ke sys.path agar paket `foodwaste` bisa diimpor.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "foodwaste.settings")
django.setup()

from django.db import connection  # noqa: E402  (harus setelah django.setup())

schema = os.getenv("SCHEMA", "tugas_kelompok")

if connection.vendor != "postgresql":
    print(f"Database {connection.vendor}: schema tidak diperlukan, dilewati.")
else:
    from psycopg2 import sql

    with connection.cursor() as cursor:
        cursor.execute(
            sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(schema))
        )
    print(f"Schema '{schema}' siap digunakan.")
