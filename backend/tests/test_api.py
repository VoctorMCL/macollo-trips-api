"""
Pruebas de endpoints de la API FastAPI.
"""

import unittest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.config import ADMIN_PASSWORD, ADMIN_USERNAME

class TestAPIEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def _login(self):
        return self.client.post(
            "/api/auth/login",
            json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
        )

    def test_health_check(self):
        """Verifica que el endpoint /api/health responda exitosamente."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("gallery_total_images", data)

    def test_auth_required_for_gallery(self):
        """La galería no debe ser accesible sin sesión o API key."""
        response = self.client.get("/api/gallery")
        self.assertEqual(response.status_code, 401)

    def test_login_and_session(self):
        """Verifica el login sin registro y la sesión resultante."""
        bad = self.client.post(
            "/api/auth/login",
            json={"username": ADMIN_USERNAME, "password": "incorrecta"}
        )
        self.assertEqual(bad.status_code, 401)

        login = self._login()
        self.assertEqual(login.status_code, 200)
        self.assertTrue(login.json()["authenticated"])

        me = self.client.get("/api/auth/me")
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["username"], ADMIN_USERNAME)

    def test_gallery_endpoints(self):
        """Verifica que los endpoints de consulta de galería funcionen autenticados."""
        self._login()
        res_stats = self.client.get("/api/gallery")
        self.assertEqual(res_stats.status_code, 200)
        self.assertIn("total_images", res_stats.json())

        res_items = self.client.get("/api/gallery/items")
        self.assertEqual(res_items.status_code, 200)
        self.assertIsInstance(res_items.json(), list)

    def test_api_key_management(self):
        """Verifica la creación y revocación de API keys desde el panel."""
        self._login()
        created = self.client.post("/api/keys", json={"name": "Cliente de prueba"})
        self.assertEqual(created.status_code, 200)
        raw_key = created.json()["raw_key"]
        key_id = created.json()["key"]["id"]
        self.assertTrue(raw_key.startswith("mk_"))

        listed = self.client.get("/api/keys")
        self.assertEqual(listed.status_code, 200)
        self.assertTrue(any(k["id"] == key_id for k in listed.json()["items"]))

        # La clave activa autoriza endpoints de la API sin sesión.
        self.client.cookies.clear()
        authorized = self.client.get(
            "/api/gulupa-handbook",
            headers={"X-API-Key": raw_key}
        )
        self.assertEqual(authorized.status_code, 200)

        # Volver a iniciar sesión para revocarla desde el panel.
        self._login()
        revoked = self.client.delete(f"/api/keys/{key_id}")
        self.assertEqual(revoked.status_code, 200)

        # Una API key revocada ya no autoriza el acceso.
        self.client.cookies.clear()
        denied = self.client.get("/api/gallery", headers={"X-API-Key": raw_key})
        self.assertEqual(denied.status_code, 401)

    def test_gulupa_handbook_endpoint(self):
        """Verifica el manual técnico agronómico de Gulupa."""
        self._login()
        res = self.client.get("/api/gulupa-handbook?temperature_c=22.0")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("Gulupa", data["crop"])
        self.assertIn("sample_recommendations", data)

if __name__ == "__main__":
    unittest.main()
