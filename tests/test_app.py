import tempfile
import unittest
from pathlib import Path
import app as cloudops_app

class CloudOpsTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        cloudops_app.DB_PATH = Path(self.temp_dir.name) / "test.db"
        cloudops_app.init_db()
        cloudops_app.app.config["TESTING"] = True
        self.client = cloudops_app.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_dashboard_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Deployment overview", response.data)

    def test_health_endpoint(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_add_deployment(self):
        response = self.client.post("/deployments", data={
            "project_name": "Test App",
            "environment": "Development",
            "status": "Success",
            "failure_type": "None",
            "notes": "Created by test"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Test App", response.data)

if __name__ == "__main__":
    unittest.main()
