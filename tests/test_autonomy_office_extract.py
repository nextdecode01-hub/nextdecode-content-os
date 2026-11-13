from __future__ import annotations

import base64
import io
import json
import zipfile

import pytest

from app.autonomy.models import TaskRequest
from app.autonomy.office_extract import extract_office, validate_office_payload
from app.autonomy.registry import build_default_registry


def _zip_bytes(parts: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, value in parts.items():
            archive.writestr(name, value)
    return buffer.getvalue()


def _payload(name: str, raw: bytes) -> dict:
    return {"file_name": name, "content_base64": base64.b64encode(raw).decode("ascii")}


def test_docx_extracts_paragraphs_and_tables_as_text_without_returning_bytes():
    raw = _zip_bytes({
        "[Content_Types].xml": b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>',
        "word/document.xml": (
            b'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            b'<w:body><w:p><w:r><w:t>First paragraph</w:t></w:r></w:p>'
            b'<w:tbl><w:tr><w:tc><w:p><w:r><w:t>Table cell</w:t></w:r></w:p></w:tc></w:tr></w:tbl>'
            b'<w:p><w:r><w:t>Final line</w:t></w:r></w:p></w:body></w:document>'
        ),
    })
    normalized = validate_office_payload(_payload("brief.docx", raw))
    json.dumps(normalized)  # API queue payloads must remain JSON-serializable.
    result = extract_office(TaskRequest("documents.office.extract", normalized))
    assert result.status == "succeeded"
    assert result.output["format"] == "docx"
    assert "First paragraph" in result.output["extracted_text"]
    assert "Table cell" in result.output["extracted_text"]
    assert result.output["paragraph_count"] == 3
    assert "content_base64" not in result.output
    assert result.evidence["filesystem_access"] is False
    assert result.evidence["network_access"] is False


def test_xlsx_extracts_shared_and_inline_strings_and_numeric_values():
    raw = _zip_bytes({
        "[Content_Types].xml": b'<Types/>',
        "xl/workbook.xml": (
            b'<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            b'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            b'<sheets><sheet name="Metrics" sheetId="1" r:id="rId1"/></sheets></workbook>'
        ),
        "xl/_rels/workbook.xml.rels": (
            b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            b'<Relationship Id="rId1" Type="worksheet" Target="worksheets/sheet1.xml"/>'
            b'</Relationships>'
        ),
        "xl/sharedStrings.xml": (
            b'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            b'<si><t>views</t></si><si><t>likes</t></si></sst>'
        ),
        "xl/worksheets/sheet1.xml": (
            b'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            b'<sheetData><row r="1"><c r="A1" t="s"><v>0</v></c>'
            b'<c r="B1" t="s"><v>1</v></c></row>'
            b'<row r="2"><c r="A2"><v>100</v></c><c r="B2"><v>10</v></c></row>'
            b'<row r="3"><c r="A3" t="inlineStr"><is><t>200</t></is></c>'
            b'<c r="B3" t="b"><v>1</v></c></row></sheetData></worksheet>'
        ),
    })
    result = extract_office(TaskRequest("documents.office.extract", _payload("metrics.xlsx", raw)))
    assert result.status == "succeeded"
    assert result.output["format"] == "xlsx"
    assert "[Metrics]" in result.output["extracted_text"]
    assert "views" in result.output["extracted_text"]
    assert "100" in result.output["extracted_text"]
    assert result.output["sheet_count"] == 1
    assert result.output["cell_count"] == 6
    assert result.evidence["formula_evaluation"] is False


@pytest.mark.parametrize("payload", [
    {"file_name": "../secret.docx", "content_base64": "eA=="},
    {"file_name": "folder/file.docx", "content_base64": "eA=="},
    {"file_name": "file.pdf", "content_base64": "eA=="},
    {"file_name": "file.docx", "content_base64": "not base64!"},
    {"file_name": "file.docx", "content_base64": "eA==", "path": "/etc/passwd"},
    {"file_name": "file.docx", "content_base64": "eA==", "format": "xlsx"},
])
def test_office_payload_rejects_paths_unsupported_formats_and_malformed_base64(payload):
    with pytest.raises(ValueError):
        validate_office_payload(payload)


def test_office_archive_rejects_path_traversal_and_external_xlsx_relationships():
    from app.autonomy.office_extract import _archive_members, _xlsx_text

    traversal = _zip_bytes({"../escape": b"no"})
    with pytest.raises(ValueError, match="path_or_encryption"):
        _archive_members(traversal)

    external = _zip_bytes({
        "xl/workbook.xml": b'<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheets/></workbook>',
        "xl/_rels/workbook.xml.rels": (
            b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            b'<Relationship Id="rId1" Target="https://evil.example/book.xml" TargetMode="External"/>'
            b'</Relationships>'
        ),
    })
    with pytest.raises(ValueError, match="external_relationship"):
        _xlsx_text(_archive_members(external))


def test_office_archive_rejects_dtd_and_high_compression_ratio():
    from app.autonomy.office_extract import _archive_members, _xml

    with pytest.raises(ValueError, match="dtd_forbidden"):
        _xml(b'<!DOCTYPE x [<!ENTITY e "boom">]><x>&e;</x>')
    with pytest.raises(ValueError, match="dtd_forbidden"):
        _xml(b" " * 5000 + b'<!DOCTYPE x [<!ENTITY e "boom">]><x>&e;</x>')

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("payload.xml", b"A" * 100_000)
    with pytest.raises(ValueError, match="compression_ratio_limit"):
        _archive_members(buffer.getvalue())


def test_office_extractor_is_direct_task_only_and_has_no_external_permissions():
    capability = build_default_registry().get("documents.office.extract")
    assert capability.enabled is True
    assert capability.planner_allowed is False
    assert capability.network_access is False
    assert capability.permission_scopes == ("input:read", "document:extract")
    assert capability.sandbox_profile == "in-process-bounded"
