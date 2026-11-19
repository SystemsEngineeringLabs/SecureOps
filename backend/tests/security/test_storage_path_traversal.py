"""Evidence storage must never write or read outside the tenant's directory."""

import uuid

import pytest

from app.services.storage.local import LocalStorage

DEEP = "../" * 10
TRAVERSAL_NAMES = [
    f"{DEEP}escape.pdf",
    "..\\" * 10 + "escape.pdf",
    "/etc/passwd",
    f"sub/dir/{DEEP}escape.pdf",
    f"{'../' * 5}other-tenant/escape.pdf",
    "..",
    "",
]


@pytest.fixture
def backend(tmp_path):
    return LocalStorage(base_path=str(tmp_path / "store"))


@pytest.mark.security
class TestUploadContainment:
    @pytest.mark.parametrize("name", TRAVERSAL_NAMES)
    async def test_upload_stays_inside_tenant_dir(self, backend, tmp_path, name):
        tenant = str(uuid.uuid4())
        rel = await backend.upload(tenant, name, b"data", "application/pdf")

        tenant_root = (tmp_path / "store" / tenant).resolve()
        written = (tmp_path / "store" / rel).resolve()
        assert written.is_relative_to(tenant_root)
        assert written.is_file()
        # nothing was created outside the store
        assert not (tmp_path / "escape.pdf").exists()
        assert {p.name for p in tmp_path.iterdir()} == {"store"}

    async def test_normal_name_is_preserved(self, backend):
        rel = await backend.upload(str(uuid.uuid4()), "SOC2 report.pdf", b"x", "application/pdf")
        assert rel.endswith("_SOC2 report.pdf")


@pytest.mark.security
class TestReadDeleteContainment:
    @pytest.mark.parametrize("path", ["../outside.txt", "/etc/passwd", "a/../../outside.txt"])
    async def test_download_rejects_escaping_path(self, backend, tmp_path, path):
        (tmp_path / "outside.txt").write_text("secret")
        with pytest.raises((ValueError, FileNotFoundError)):
            await backend.download(path)

    async def test_delete_rejects_escaping_path(self, backend, tmp_path):
        victim = tmp_path / "outside.txt"
        victim.write_text("keep")
        with pytest.raises(ValueError):
            await backend.delete("../outside.txt")
        assert victim.exists()
