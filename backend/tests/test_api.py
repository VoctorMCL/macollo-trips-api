"""
Pruebas de endpoints de la API FastAPI.
"""

import unittest
from fastapi.testclient import TestClient
from backend.app.main import app

class TestAPIEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_check(self):
        """Verifica que el endpoint /api/health responda exitosamente."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("gallery_total_images", data)

    def test_gallery_endpoints(self):
        """Verifica que los endpoints de consulta de galería funcionen."""
        res_stats = self.client.get("/api/gallery")
        self.assertEqual(res_stats.status_code, 200)
        self.assertIn("total_images", res_stats.json())

        res_items = self.client.get("/api/gallery/items")
        self.assertEqual(res_items.status_code, 200)
        self.assertIsInstance(res_items.json(), list)

    def test_gulupa_handbook_endpoint(self):
        """Verifica el manual técnico agronómico de Gulupa."""
        res = self.client.get("/api/gulupa-handbook?temperature_c=22.0")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("Gulupa", data["crop"])
        self.assertIn("sample_recommendations", data)

if __name__ == "__main__":
    unittest.main()
