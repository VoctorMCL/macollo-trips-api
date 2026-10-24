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

        expected_stages = ["huevo", "larva", "pupa", "adulto", "dano_gulupa"]
        for st in expected_stages:
            self.assertIn(st, BIOLOGICAL_STAGE_PROMPTS, f"Estadio {st} falta en BIOLOGICAL_STAGE_PROMPTS")
            self.assertIn("prompt", BIOLOGICAL_STAGE_PROMPTS[st])
            self.assertIn("name", BIOLOGICAL_STAGE_PROMPTS[st])

        # El ciclo biológico tiene 4 fases: huevo, larva (ninfa única), pupa y adulto.
        # No deben existir dos estadios de ninfa separados.
        for old_key in ["ninfa_1", "ninfa_2"]:
            self.assertNotIn(old_key, BIOLOGICAL_STAGE_PROMPTS, f"{old_key} no debe existir: solo hay una fase larva/ninfa")
        self.assertIn("larva", BIOLOGICAL_STAGE_PROMPTS)

    def test_thermal_cycle_calculation(self):
        """Verifica el cálculo de duración de ciclo a diferentes temperaturas."""
        # A 20°C (temperatura moderada)
        cycle_20 = get_gulupa_cycle_estimate("larva", temperature_c=20.0)
        self.assertEqual(cycle_20["urgency_level"], "CRÍTICO")
        self.assertIn("días", cycle_20["days_to_adult"])
        self.assertEqual(cycle_20["detected_stage_key"], "larva")

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

    def test_mip_damage_manifestation_handling(self):
        """Verifica que las recomendaciones incluyan directrices especiales si solo hay daño visible."""
        recs_damage = get_gulupa_mip_recommendations("dano_gulupa", is_damage_only=True)
        cultural_text = " ".join(recs_damage["cultural_control"])
        self.assertIn("cacarizado", cultural_text.lower())
        self.assertIn("exportación", cultural_text.lower())

    def test_auth_token_tampering(self):
        """Verifica que tokens de sesión alterados sean rechazados."""
        from backend.app.auth import create_session_token, verify_session_token
        token = create_session_token("admin")
        self.assertEqual(verify_session_token(token), "admin")

        # Token corrupto o alterado
        tampered = token + "xyz"
        self.assertIsNone(verify_session_token(tampered))
        self.assertIsNone(verify_session_token("invalid.token.structure"))
        self.assertIsNone(verify_session_token(None))

    def test_gallery_manager_initialization(self):
        """Verifica que la galería se inicialice correctamente y devuelva estadísticas."""
        stats = gallery_manager.get_gallery_stats()
        self.assertIn("total_images", stats)
        self.assertIn("by_stage", stats)
        for stage in ["huevo", "larva", "pupa", "adulto", "dano_gulupa"]:
            self.assertIn(stage, stats["by_stage"])

if __name__ == "__main__":
    unittest.main()
