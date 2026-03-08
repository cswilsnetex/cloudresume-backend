import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import azure.functions as func

# Set env vars before importing function_app
os.environ["CosmosDBConnectionString"] = "DefaultEndpointsProtocol=https;AccountName=fake;AccountKey=ZmFrZQ==;TableEndpoint=https://fake.table.cosmos.azure.com:443/;"
os.environ["CORS_ORIGIN"] = "https://cloudresume.n0csw.com"

# Add parent directory to path so we can import function_app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestCounter(unittest.TestCase):

    @patch("function_app.TableClient")
    def test_counter_increments_existing(self, mock_table_cls):
        mock_client = MagicMock()
        mock_table_cls.from_connection_string.return_value = mock_client
        mock_client.get_entity.return_value = {"count": 5}

        import function_app
        req = func.HttpRequest(method="POST", url="/api/counter", body=b"")
        resp = function_app.counter(req)
        body = json.loads(resp.get_body())

        self.assertEqual(body["count"], 6)
        mock_client.upsert_entity.assert_called_once()

    @patch("function_app.TableClient")
    def test_counter_initializes_on_first_visit(self, mock_table_cls):
        mock_client = MagicMock()
        mock_table_cls.from_connection_string.return_value = mock_client
        mock_client.get_entity.side_effect = Exception("Not found")

        import function_app
        req = func.HttpRequest(method="GET", url="/api/counter", body=b"")
        resp = function_app.counter(req)
        body = json.loads(resp.get_body())

        self.assertEqual(body["count"], 1)

    @patch("function_app.TableClient")
    def test_response_is_json(self, mock_table_cls):
        mock_client = MagicMock()
        mock_table_cls.from_connection_string.return_value = mock_client
        mock_client.get_entity.return_value = {"count": 10}

        import function_app
        req = func.HttpRequest(method="POST", url="/api/counter", body=b"")
        resp = function_app.counter(req)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("application/json", resp.headers.get("Content-Type", ""))
        json.loads(resp.get_body())  # Should not raise

    @patch("function_app.TableClient")
    def test_cors_header_matches_origin(self, mock_table_cls):
        mock_client = MagicMock()
        mock_table_cls.from_connection_string.return_value = mock_client
        mock_client.get_entity.return_value = {"count": 1}

        import function_app
        req = func.HttpRequest(method="POST", url="/api/counter", body=b"")
        resp = function_app.counter(req)

        self.assertEqual(
            resp.headers.get("Access-Control-Allow-Origin"),
            "https://cloudresume.n0csw.com",
        )


if __name__ == "__main__":
    unittest.main()
