"""Dry-run Hired's real Neon storage healthcheck without external credentials."""
import io
import sqlite3
import pytest


def test_remote_storage_roundtrip_uses_receipt_paths(tmp_path, monkeypatch):
    import server

    class FakeS3:
        objects = {}
        def head_bucket(self, **kwargs):
            assert kwargs['Bucket'] == 'private-check-bucket'
        def put_object(self, *, Bucket, Key, Body, ContentType):
            assert Bucket == 'private-check-bucket'
            assert Key.startswith('payment-proofs/') and Key.endswith('.pdf')
            assert ContentType == 'application/pdf'
            self.objects[Key] = Body
        def get_object(self, *, Bucket, Key):
            assert Bucket == 'private-check-bucket'
            return {'Body':io.BytesIO(self.objects[Key])}
        def delete_object(self, *, Bucket, Key):
            del self.objects[Key]

    file = tmp_path/'orders.sqlite3'
    def fake_db():
        con=sqlite3.connect(file)
        con.row_factory=sqlite3.Row
        return con

    fake=FakeS3()
    monkeypatch.setattr(server, 'USE_POSTGRES', True)
    monkeypatch.setattr(server, 'HAS_S3_CONFIG', True)
    monkeypatch.setattr(server, 'S3_BUCKET', 'private-check-bucket')
    monkeypatch.setattr(server, 's3_client', lambda:fake)
    monkeypatch.setattr(server, 'db', fake_db)

    assert server.verify_remote_storage_roundtrip() is True
    assert fake.objects == {}, 'A test receipt was not deleted'
    with fake_db() as con:
        assert con.execute('SELECT count(*) FROM orders').fetchone()[0] == 0


def test_roundtrip_rejects_corrupt_receipt(tmp_path, monkeypatch):
    import server
    class FakeS3:
        def head_bucket(self, **kwargs): pass
        def put_object(self, **kwargs): pass
        def get_object(self, **kwargs):return {'Body': io.BytesIO(b'corrupted')}
        def delete_object(self, **kwargs):pass

    monkeypatch.setattr(server, 'USE_POSTGRES', True)
    monkeypatch.setattr(server, 'HAS_S3_CONFIG', True)
    monkeypatch.setattr(server, 'S3_BUCKET', 'private-check-bucket')
    monkeypatch.setattr(server, 's3_client', lambda:FakeS3())
    monkeypatch.setattr(server, 'setup_db', lambda:None)
    with pytest.raises(RuntimeError,match='Stored receipt'):
        server.verify_remote_storage_roundtrip()
