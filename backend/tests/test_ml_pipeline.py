"""
Pruebas unitarias para el motor agronómico, prompts de taxonomía y gestor de galería.
"""

import unittest
from backend.app.ml.taxonomy_prompts import (
    TAXONOMIC_TARGET_PROMPTS,
    BIOLOGICAL_STAGE_PROMPTS,
    POSITIVE_TRIPS_KEYS
)
from backend.app.agronomy.gulupa_cycle import (
    get_gulupa_cycle_estimate,
    calculate_stage_duration_days
)
from backend.app.agronomy.gulupa_mip import get_gulupa_mip_recommendations
from backend.app.ml.gallery_index import gallery_manager

class TestAgronomyAndTaxonomy(unittest.TestCase):
    def test_taxonomy_prompts_integrity(self):
        """Verifica que todos los prompts taxonómicos y de estadios estén bien estructurados."""
        self.assertGreater(len(TAXONOMIC_TARGET_PROMPTS), 5)
        for key in POSITIVE_TRIPS_KEYS:
            self.assertIn(key, TAXONOMIC_TARGET_PROMPTS, f"Clave positiva {key} falta en prompts")
            self.assertIsInstance(TAXONOMIC_TARGET_PROMPTS[key], str)

        expected_stages = ["adulto", "ninfa_1", "ninfa_2", "pupa", "dano_gulupa"]
        for st in expected_stages:
            self.assertIn(st, BIOLOGICAL_STAGE_PROMPTS, f"Estadio {st} falta en BIOLOGICAL_STAGE_PROMPTS")
            self.assertIn("prompt", BIOLOGICAL_STAGE_PROMPTS[st])
            self.assertIn("name", BIOLOGICAL_STAGE_PROMPTS[st])

    def test_thermal_cycle_calculation(self):
        """Verifica el cálculo de duración de ciclo a diferentes temperaturas."""
        # A 20°C (temperatura moderada)
        cycle_20 = get_gulupa_cycle_estimate("ninfa_2", temperature_c=20.0)
        self.assertEqual(cycle_20["urgency_level"], "CRÍTICO")
        self.assertIn("días", cycle_20["days_to_adult"])
        self.assertEqual(cycle_20["detected_stage_key"], "ninfa_2")

        # A 28°C (temperatura alta de invernadero, desarrollo más rápido)
        cycle_28 = get_gulupa_cycle_estimate("adulto", temperature_c=28.0)
        self.assertEqual(cycle_28["urgency_level"], "CRÍTICO")
        self.assertIn("Adulto", cycle_28["detected_stage_name"])

        # Test de grados-día
        days_15c = calculate_stage_duration_days(60.0, 15.0)
        days_25c = calculate_stage_duration_days(60.0, 25.0)
        # A mayor temperatura, menos días de desarrollo
        self.assertGreater(days_15c, days_25c)

    def test_mip_recommendations(self):
        """Verifica que las recomendaciones contengan todas las categorías de MIP."""
        recs = get_gulupa_mip_recommendations("adulto")
        self.assertIn("biological_control", recs)
        self.assertIn("ethological_control", recs)
        self.assertIn("cultural_control", recs)
        self.assertIn("chemical_biorational_control", recs)
        self.assertIn("export_impact_alert", recs)

        # Verificar presencia de menciones a enemigos naturales clave
        bio_text = " ".join(recs["biological_control"])
        self.assertTrue("swirskii" in bio_text or "Orius" in bio_text)

        # Verificar recomendación de trampa azul
        etho_text = " ".join(recs["ethological_control"])
        self.assertTrue("AZULES" in etho_text or "azules" in etho_text)

    def test_gallery_manager_initialization(self):
        """Verifica que la galería se inicialice correctamente y devuelva estadísticas."""
        stats = gallery_manager.get_gallery_stats()
        self.assertIn("total_images", stats)
        self.assertIn("by_stage", stats)
        for stage in ["adulto", "ninfa_1", "ninfa_2", "pupa", "dano_gulupa"]:
            self.assertIn(stage, stats["by_stage"])

if __name__ == "__main__":
    unittest.main()
