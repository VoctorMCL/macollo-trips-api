"""
Pruebas del catálogo extensible, perfiles de detección y nuevos endpoints.

No requieren descargar ni cargar BioCLIP: validan la estructura del dominio,
los proveedores agronómicos y la API de catálogo/galería.
"""

import unittest

from fastapi.testclient import TestClient

from backend.app.agronomy.flies import (
    get_fly_cycle_estimate,
    get_fly_mip_recommendations,
)
from backend.app.agronomy.mites import (
    get_mite_cycle_estimate,
    get_mite_mip_recommendations,
)
from backend.app.agronomy.registry import get_agronomy
from backend.app.config import ADMIN_PASSWORD, ADMIN_USERNAME
from backend.app.domain.catalog import (
    GALLERY_LABELS,
    PROFILES,
    build_gallery_label_key,
    get_gallery_label,
    get_profile,
    get_target,
)
from backend.app.main import app


class TestExtensibleCatalog(unittest.TestCase):
    def test_profiles_and_targets_integrity(self):
        """El catálogo debe tener trips, moscas y arañas rojas coherentes."""

        self.assertEqual(set(PROFILES), {"auto", "trips", "moscas", "aranas_rojas"})
        self.assertFalse(get_profile("moscas").experimental)
        self.assertFalse(get_profile("aranas_rojas").experimental)

        for profile in PROFILES.values():
            self.assertTrue(profile.target_keys, profile.key)
            self.assertTrue(profile.positive_target_keys, profile.key)
            self.assertTrue(set(profile.positive_target_keys).issubset(profile.target_keys))
            for target_key in profile.target_keys:
                target = get_target(target_key)
                self.assertTrue(target.prompts)
            for stage_key in profile.stages:
                self.assertTrue(profile.stages[stage_key].prompts)

    def test_legacy_and_generic_gallery_labels(self):
        """La galería conserva trips y añade moscas y arañas rojas."""

        for stage in ["huevo", "larva", "pupa", "adulto", "dano_gulupa"]:
            self.assertIn(stage, GALLERY_LABELS)
            self.assertEqual(get_gallery_label(stage).profile, "trips")

        fly_label_key = build_gallery_label_key(
            "moscas", "mosca_frutal_anastrepha", "adulto"
        )
        self.assertEqual(fly_label_key, "moscas/mosca_frutal_anastrepha/adulto")
        self.assertIn(fly_label_key, GALLERY_LABELS)

        mite_label_key = build_gallery_label_key(
            "aranas_rojas", "arana_roja_tetranychus", "dano"
        )
        self.assertEqual(mite_label_key, "aranas_rojas/arana_roja_tetranychus/dano")
        self.assertIn(mite_label_key, GALLERY_LABELS)

    def test_generic_agronomy_providers(self):
        """Los perfiles moscas y arañas devuelven ciclo y recomendaciones."""

        fly_cycle, fly_recs = get_agronomy("moscas", "larva", 24.0)
        self.assertEqual(fly_cycle["profile"], "moscas")
        self.assertIn("biological_control", fly_recs)
        self.assertIn("export_impact_alert", fly_recs)

        mite_cycle, mite_recs = get_agronomy("aranas_rojas", "adulto", 25.0)
        self.assertEqual(mite_cycle["profile"], "aranas_rojas")
        self.assertIn("cultural_control", mite_recs)

        self.assertIn("urgency_level", get_fly_cycle_estimate("adulto", 22.0))
        self.assertIn("days_to_adult", get_mite_cycle_estimate("huevo", 22.0))
        self.assertIn("biological_control", get_fly_mip_recommendations("adulto"))
        self.assertIn(
            "chemical_biorational_control",
            get_mite_mip_recommendations("dano"),
        )

    def test_profile_lookup_errors(self):
        """Un perfil inexistente debe lanzar KeyError con mensaje útil."""

        with self.assertRaises(KeyError):
            get_profile("enfermedades")


class TestCatalogEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def _login(self):
        return self.client.post(
            "/api/auth/login",
            json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
        )

    def test_catalog_and_profiles_endpoints(self):
        """El catálogo debe exponer todos los perfiles sin autenticación."""

        response = self.client.get("/api/catalog")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        keys = {profile["key"] for profile in data["profiles"]}
        self.assertEqual(keys, {"auto", "trips", "moscas", "aranas_rojas"})

        profile = self.client.get("/api/profiles/moscas")
        self.assertEqual(profile.status_code, 200)
        self.assertEqual(profile.json()["key"], "moscas")

        missing = self.client.get("/api/profiles/enfermedades")
        self.assertEqual(missing.status_code, 404)

    def test_gallery_labels_endpoint(self):
        """Las etiquetas de galería se agrupan por perfil."""

        self._login()
        response = self.client.get("/api/gallery/labels")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("trips", data["by_profile"])
        self.assertIn("moscas", data["by_profile"])
        self.assertIn("aranas_rojas", data["by_profile"])
        self.assertTrue(any(item["key"] == "larva" for item in data["items"]))

    def test_generic_handbook_endpoint(self):
        """La ficha técnica genérica funciona para cualquier perfil."""

        self._login()
        response = self.client.get("/api/handbook?profile=aranas_rojas&temperature_c=24")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["profile"]["key"], "aranas_rojas")
        self.assertIn("sample_recommendations", data)


if __name__ == "__main__":
    unittest.main()
