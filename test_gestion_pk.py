import os
import sys

import django

# Setup Django environment
sys.path.append("/home/daniel/Aprendiendo/Django/cappuccino2_")
sys.path.append(
    "/home/daniel/Aprendiendo/Django/cappuccino2_/cappuccino2",
)  # Add inner app dir just in case
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from datetime import date

from cappuccino2.horario.models import Gestión


def test_gestion_pk_generation():
    print("Testing Gestión PK generation...")

    # Create a new Gestión instance
    # Note: We don't save it yet to check if save() populates the ID
    gestion = Gestión(
        año=2025, semestre="1", inicio=date(2025, 1, 20), fin=date(2025, 6, 20),
    )

    print(f"Before save: id={gestion.id}")

    # Save should trigger the ID generation
    # We use a transaction or just try/except because we might not have migrations applied
    # and the DB table might not have the 'id' column yet.
    # However, for unit testing the logic of the save method, we can mock or just check the object state before DB insertion errors out.
    # But wait, if the DB table doesn't have the column, save() will fail at the DB level.
    # But the 'id' assignment happens BEFORE super().save().
    # So we can check if 'id' is set even if the DB save fails.

    try:
        gestion.save()
        print(f"After save: id={gestion.id}")
    except Exception as e:
        print(f"Save failed (expected if migrations not applied): {e}")
        print(f"After failed save attempt: id={gestion.id}")

    expected_id = "2025/1"
    if gestion.id == expected_id:
        print("SUCCESS: PK generated correctly.")
    else:
        print(f"FAILURE: Expected {expected_id}, got {gestion.id}")


if __name__ == "__main__":
    test_gestion_pk_generation()
