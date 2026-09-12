"""Tests unitaires de l'historique des emplacements de culture."""
import unittest
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.models.all_models import Culture, CultureEmplacement, EspaceCulture
from app.routers.culture_helpers import corriger_date_emplacement, espace_id_at


class CultureEmplacementTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)

        self.growth = EspaceCulture(nom="Box Croissance")
        self.flower = EspaceCulture(nom="Box Floraison")
        self.db.add_all([self.growth, self.flower])
        self.db.flush()

        self.culture = Culture(
            nom="Critical Kush",
            id_espace=self.flower.id_espace,
            date_debut=date(2026, 8, 28),
            statut="active",
        )
        self.db.add(self.culture)
        self.db.flush()

        self.initial = CultureEmplacement(
            id_culture=self.culture.id_culture,
            id_espace=self.growth.id_espace,
            date_debut=date(2026, 8, 28),
            date_fin=date(2026, 9, 10),
        )
        self.current = CultureEmplacement(
            id_culture=self.culture.id_culture,
            id_espace=self.flower.id_espace,
            date_debut=date(2026, 9, 10),
            date_fin=None,
        )
        self.db.add_all([self.initial, self.current])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_espace_id_at_uses_half_open_intervals(self):
        rows = [self.initial, self.current]

        self.assertEqual(
            espace_id_at(rows, date(2026, 9, 9)),
            self.growth.id_espace,
        )
        self.assertEqual(
            espace_id_at(rows, date(2026, 9, 10)),
            self.flower.id_espace,
        )
        self.assertEqual(
            espace_id_at(rows, date(2026, 8, 1)),
            self.growth.id_espace,
        )

    def test_corriger_date_emplacement_recalcule_previous_end(self):
        corriger_date_emplacement(
            self.db,
            self.culture,
            self.current.id_emplacement,
            date(2026, 9, 7),
        )
        self.db.commit()
        self.db.refresh(self.initial)
        self.db.refresh(self.current)
        self.db.refresh(self.culture)

        self.assertEqual(self.initial.date_debut, date(2026, 8, 28))
        self.assertEqual(self.initial.date_fin, date(2026, 9, 7))
        self.assertEqual(self.current.date_debut, date(2026, 9, 7))
        self.assertIsNone(self.current.date_fin)
        self.assertEqual(self.culture.id_espace, self.flower.id_espace)

    def test_corriger_date_rejects_invalid_boundaries(self):
        with self.assertRaises(Exception):
            corriger_date_emplacement(
                self.db,
                self.culture,
                self.current.id_emplacement,
                date(2026, 8, 28),
            )

        with self.assertRaises(Exception):
            corriger_date_emplacement(
                self.db,
                self.culture,
                self.initial.id_emplacement,
                date(2026, 9, 20),
            )


if __name__ == "__main__":
    unittest.main()
