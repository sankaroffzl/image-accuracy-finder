import io
import json
import cv2
import numpy as np
import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["UPLOAD_FOLDER"] = "/tmp/test-uploads"
    with app.test_client() as client:
        yield client


def _make_image_bytes(color=128, fmt="PNG"):
    """Create a simple test image as bytes."""
    from PIL import Image
    import numpy as np
    arr = np.ones((50, 50, 3), dtype=np.uint8) * color
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    return buf


def test_home_page_returns_200(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"<!DOCTYPE html>" in resp.data or b"<html" in resp.data


def test_compare_with_valid_images(client):
    img_a = _make_image_bytes(200)
    img_b = _make_image_bytes(200)
    resp = client.post("/compare", data={
        "image_a": (img_a, "a.png"),
        "image_b": (img_b, "b.png"),
    })
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["success"] is True
    assert "overall" in data
    assert "verdict" in data
    assert "details" in data


def test_compare_missing_file_returns_400(client):
    img_a = _make_image_bytes(100)
    resp = client.post("/compare", data={
        "image_a": (img_a, "a.png"),
    })
    assert resp.status_code == 400
    data = json.loads(resp.data)
    assert data["success"] is False


def test_compare_invalid_file_type_returns_400(client):
    buf = io.BytesIO(b"not an image")
    img_a = io.BytesIO(b"not an image")
    resp = client.post("/compare", data={
        "image_a": (img_a, "a.txt"),
        "image_b": (buf, "b.txt"),
    })
    assert resp.status_code == 400
    data = json.loads(resp.data)
    assert data["success"] is False


def test_results_page_returns_200(client):
    """First upload, then visit results page."""
    img_a = _make_image_bytes(150)
    img_b = _make_image_bytes(150)
    resp = client.post("/compare", data={
        "image_a": (img_a, "a.png"),
        "image_b": (img_b, "b.png"),
    })
    data = json.loads(resp.data)
    result_id = data["id"]

    resp = client.get(f"/results/{result_id}")
    assert resp.status_code == 200
    assert b"<!DOCTYPE html>" in resp.data or b"<html" in resp.data


class TestBatchCompare:
    def setup_method(self):
        self.ref = cv2.imencode('.jpg', np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8))[1].tobytes()
        self.candidate = cv2.imencode('.jpg', np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8))[1].tobytes()

    def test_batch_compare_success(self, client):
        data = {
            'reference': (io.BytesIO(self.ref), 'ref.jpg'),
            'candidates': [
                (io.BytesIO(self.candidate), 'cand1.jpg'),
                (io.BytesIO(self.candidate), 'cand2.jpg'),
            ]
        }
        resp = client.post('/compare-batch', data=data, content_type='multipart/form-data')
        assert resp.status_code == 200
        json_data = resp.get_json()
        assert json_data['success'] is True
        assert json_data['count'] == 2
        assert json_data['total'] == 2
        assert json_data['failed'] == 0
        assert len(json_data['results']) == 2

    def test_batch_compare_missing_reference(self, client):
        data = {
            'candidates': [(io.BytesIO(self.candidate), 'cand1.jpg')]
        }
        resp = client.post('/compare-batch', data=data, content_type='multipart/form-data')
        assert resp.status_code == 400

    def test_batch_compare_no_candidates(self, client):
        data = {
            'reference': (io.BytesIO(self.ref), 'ref.jpg'),
        }
        resp = client.post('/compare-batch', data=data, content_type='multipart/form-data')
        assert resp.status_code == 400

    def test_batch_compare_invalid_file_type(self, client):
        data = {
            'reference': (io.BytesIO(self.ref), 'ref.jpg'),
            'candidates': [(io.BytesIO(b'not an image'), 'bad.txt')]
        }
        resp = client.post('/compare-batch', data=data, content_type='multipart/form-data')
        assert resp.status_code == 400


def test_batch_results_page(client):
    """Test batch results page loads."""
    resp = client.get('/batch-results')
    assert resp.status_code == 200
    assert b'Batch Results' in resp.data or b'Rank' in resp.data
