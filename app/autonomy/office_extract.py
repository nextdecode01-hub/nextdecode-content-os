"""Bounded, in-memory Office document extraction using Python's standard library.

This module intentionally does not read paths, extract ZIP members to disk, follow
external relationships, execute macros/formulas, or contact the network.
"""
from __future__ import annotations

import base64
import binascii
import io
import re
import zipfile
import zlib
import xml.etree.ElementTree as ET
from pathlib import PurePosixPath

from .models import TaskRequest, TaskResult

MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_ARCHIVE_MEMBERS = 128
MAX_MEMBER_BYTES = 4 * 1024 * 1024
MAX_TOTAL_UNCOMPRESSED = 8 * 1024 * 1024
MAX_COMPRESSION_RATIO = 100
MAX_TEXT_CHARS = 500_000
MAX_SHEETS = 20
MAX_ROWS = 1_000
MAX_COLUMNS = 100
MAX_CELLS = 50_000
MAX_XML_BYTES = 4 * 1024 * 1024

DOCX_MAIN = "word/document.xml"
XLSX_WORKBOOK = "xl/workbook.xml"
XLSX_RELS = "xl/_rels/workbook.xml.rels"
REL_NS = "{http://schemas.openxmlformats.org/package/2006/relationships}"
SHEET_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
DOC_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
OFFICE_REL_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


def validate_office_payload(payload: dict) -> dict:
    if (not isinstance(payload, dict)
            or set(payload) not in ({"file_name", "content_base64"},
                                    {"file_name", "content_base64", "format"})):
        raise ValueError("office payload requires only file_name, content_base64 and optional normalized format")
    file_name = payload["file_name"]
    encoded = payload["content_base64"]
    if not isinstance(file_name, str) or not 1 <= len(file_name) <= 160:
        raise ValueError("file_name must contain 1..160 characters")
    if PurePosixPath(file_name.replace("\\", "/")).name != file_name.replace("\\", "/"):
        raise ValueError("file_name must not contain a path")
    suffix = PurePosixPath(file_name).suffix.lower()
    if suffix not in {".docx", ".xlsx"}:
        raise ValueError("only DOCX and XLSX files are supported")
    if payload.get("format", suffix[1:]) != suffix[1:]:
        raise ValueError("office format does not match file extension")
    if not isinstance(encoded, str) or not 1 <= len(encoded) <= ((MAX_INPUT_BYTES + 2) // 3) * 4:
        raise ValueError("content_base64 exceeds the bounded input size")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        raise ValueError("content_base64 is invalid") from None
    if not raw or len(raw) > MAX_INPUT_BYTES:
        raise ValueError("decoded file must be 1 byte..2 MiB")
    # Keep the queue payload JSON-serializable; decode again only in the worker.
    return {"file_name": file_name, "content_base64": encoded, "format": suffix[1:]}


def _archive_members(raw: bytes) -> dict[str, bytes]:
    try:
        archive = zipfile.ZipFile(io.BytesIO(raw), "r")
    except (zipfile.BadZipFile, OSError):
        raise ValueError("office_archive_invalid") from None
    with archive:
        infos = archive.infolist()
        if not infos or len(infos) > MAX_ARCHIVE_MEMBERS:
            raise ValueError("office_archive_member_limit")
        total = 0
        names: set[str] = set()
        result: dict[str, bytes] = {}
        for info in infos:
            name = info.filename
            path = PurePosixPath(name)
            if (name in names or path.is_absolute() or ".." in path.parts
                    or "\\" in name or info.flag_bits & 0x1):
                raise ValueError("office_archive_path_or_encryption_rejected")
            names.add(name)
            if info.is_dir():
                continue
            if info.file_size > MAX_MEMBER_BYTES:
                raise ValueError("office_archive_member_too_large")
            if info.file_size and (info.compress_size == 0 or
                    info.file_size / info.compress_size > MAX_COMPRESSION_RATIO):
                raise ValueError("office_archive_compression_ratio_limit")
            # Do not trust ZIP central-directory sizes: stream and cap actual
            # decompressed bytes so forged metadata cannot trigger a ZIP bomb.
            chunks: list[bytes] = []
            member_size = 0
            try:
                with archive.open(info, "r") as stream:
                    while True:
                        chunk = stream.read(min(64 * 1024, MAX_MEMBER_BYTES + 1 - member_size))
                        if not chunk:
                            break
                        member_size += len(chunk)
                        if member_size > MAX_MEMBER_BYTES:
                            raise ValueError("office_archive_member_too_large")
                        if total + member_size > MAX_TOTAL_UNCOMPRESSED:
                            raise ValueError("office_archive_uncompressed_limit")
                        chunks.append(chunk)
            except (zipfile.BadZipFile, RuntimeError, EOFError, OSError, zlib.error):
                raise ValueError("office_archive_corrupt") from None
            data = b"".join(chunks)
            if len(data) != info.file_size:
                raise ValueError("office_archive_size_mismatch")
            if data and (info.compress_size == 0 or
                    len(data) / info.compress_size > MAX_COMPRESSION_RATIO):
                raise ValueError("office_archive_compression_ratio_limit")
            total += len(data)
            if total > MAX_TOTAL_UNCOMPRESSED:
                raise ValueError("office_archive_uncompressed_limit")
            result[name] = data
        return result


def _xml(data: bytes) -> ET.Element:
    if not data or len(data) > MAX_XML_BYTES:
        raise ValueError("office_xml_size_limit")
    upper = data.upper()  # bounded by MAX_XML_BYTES; scan the entire document for DTD/entity declarations.
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise ValueError("office_xml_dtd_forbidden")
    try:
        return ET.fromstring(data)
    except ET.ParseError:
        raise ValueError("office_xml_invalid") from None


def _docx_text(members: dict[str, bytes]) -> str:
    if DOCX_MAIN not in members or "[Content_Types].xml" not in members:
        raise ValueError("docx_required_parts_missing")
    root = _xml(members[DOCX_MAIN])
    paragraphs: list[str] = []
    for paragraph in root.iter(DOC_NS + "p"):
        chunks = []
        for node in paragraph.iter():
            if node.tag == DOC_NS + "t" and node.text:
                chunks.append(node.text)
            elif node.tag == DOC_NS + "tab":
                chunks.append("\t")
            elif node.tag in {DOC_NS + "br", DOC_NS + "cr"}:
                chunks.append("\n")
        value = "".join(chunks).strip()
        if value:
            paragraphs.append(value)
        if sum(len(item) for item in paragraphs) > MAX_TEXT_CHARS:
            raise ValueError("document_text_limit")
    text = "\n".join(paragraphs)
    if not text:
        raise ValueError("docx_no_extractable_text")
    return text[:MAX_TEXT_CHARS]


def _column_index(reference: str) -> int:
    match = re.match(r"^([A-Z]{1,3})[1-9][0-9]*$", reference.upper())
    if not match:
        raise ValueError("xlsx_cell_reference_invalid")
    value = 0
    for char in match.group(1):
        value = value * 26 + ord(char) - 64
    if value > MAX_COLUMNS:
        raise ValueError("xlsx_column_limit")
    return value - 1


def _xlsx_text(members: dict[str, bytes]) -> tuple[str, dict]:
    if XLSX_WORKBOOK not in members or XLSX_RELS not in members:
        raise ValueError("xlsx_required_parts_missing")
    if any(name.startswith("xl/externalLinks/") for name in members):
        raise ValueError("xlsx_external_links_forbidden")
    if any(name.lower().endswith("vbaproject.bin") for name in members):
        raise ValueError("xlsx_macro_content_forbidden")

    workbook = _xml(members[XLSX_WORKBOOK])
    relationships = _xml(members[XLSX_RELS])
    targets: dict[str, str] = {}
    for rel in relationships.findall(REL_NS + "Relationship"):
        if rel.attrib.get("TargetMode", "").lower() == "external":
            raise ValueError("xlsx_external_relationship_forbidden")
        target = rel.attrib.get("Target", "")
        if target.startswith("/") or ".." in PurePosixPath(target).parts or "\\" in target:
            raise ValueError("xlsx_relationship_path_rejected")
        targets[rel.attrib.get("Id", "")] = str(PurePosixPath("xl") / target)

    shared: list[str] = []
    if "xl/sharedStrings.xml" in members:
        shared_root = _xml(members["xl/sharedStrings.xml"])
        for item in shared_root.findall(SHEET_NS + "si"):
            shared.append("".join(node.text or "" for node in item.iter(SHEET_NS + "t")))
            if sum(map(len, shared)) > MAX_TEXT_CHARS:
                raise ValueError("xlsx_shared_string_limit")

    sheets = workbook.find(SHEET_NS + "sheets")
    if sheets is None:
        raise ValueError("xlsx_sheets_missing")
    sheet_outputs: list[str] = []
    cell_count = 0
    for sheet in list(sheets):
        if len(sheet_outputs) >= MAX_SHEETS:
            raise ValueError("xlsx_sheet_limit")
        rel_id = sheet.attrib.get(OFFICE_REL_NS + "id")
        target = targets.get(rel_id or "")
        if not target or target not in members:
            raise ValueError("xlsx_sheet_relationship_invalid")
        root = _xml(members[target])
        rows_text: list[str] = []
        for row in root.iter(SHEET_NS + "row"):
            cells: list[tuple[int, str]] = []
            for cell in row.findall(SHEET_NS + "c"):
                cell_count += 1
                if cell_count > MAX_CELLS:
                    raise ValueError("xlsx_cell_limit")
                column = _column_index(cell.attrib.get("r", ""))
                kind = cell.attrib.get("t", "n")
                value_node = cell.find(SHEET_NS + "v")
                inline_node = cell.find(SHEET_NS + "is")
                if kind == "s":
                    if value_node is None or not (value_node.text or "").isdigit():
                        raise ValueError("xlsx_shared_string_index_invalid")
                    index = int(value_node.text)
                    if index >= len(shared):
                        raise ValueError("xlsx_shared_string_index_invalid")
                    value = shared[index]
                elif kind == "inlineStr" and inline_node is not None:
                    value = "".join(node.text or "" for node in inline_node.iter(SHEET_NS + "t"))
                elif kind == "b":
                    value = "TRUE" if value_node is not None and value_node.text == "1" else "FALSE"
                else:
                    value = value_node.text if value_node is not None and value_node.text else ""
                cells.append((column, value))
            if cells:
                max_col = max(index for index, _ in cells)
                if max_col >= MAX_COLUMNS:
                    raise ValueError("xlsx_column_limit")
                values = [""] * (max_col + 1)
                for index, value in cells:
                    values[index] = value
                rows_text.append("\t".join(values).rstrip())
                if len(rows_text) > MAX_ROWS:
                    raise ValueError("xlsx_row_limit")
        sheet_name = sheet.attrib.get("name", "Sheet")
        sheet_outputs.append(f"[{sheet_name}]\n" + "\n".join(rows_text))
    text = "\n\n".join(sheet_outputs)
    if not text.strip():
        raise ValueError("xlsx_no_extractable_text")
    if len(text) > MAX_TEXT_CHARS:
        raise ValueError("document_text_limit")
    return text, {"sheet_count": len(sheet_outputs), "cell_count": cell_count}


def extract_office(request: TaskRequest) -> TaskResult:
    payload = validate_office_payload(request.payload)
    raw = base64.b64decode(payload["content_base64"], validate=True)
    members = _archive_members(raw)
    if payload["format"] == "docx":
        text = _docx_text(members)
        details = {"paragraph_count": sum(1 for _ in _xml(members[DOCX_MAIN]).iter(DOC_NS + "p"))}
    else:
        text, details = _xlsx_text(members)
    words = re.findall(r"\b[\w'-]+\b", text.casefold())
    output = {
        "file_name": payload["file_name"],
        "format": payload["format"],
        "character_count": len(text),
        "word_count": len(words),
        "line_count": len(text.splitlines()),
        "extracted_text": text,
        **details,
    }
    return TaskResult(
        "succeeded", output,
        evidence={"execution_mode": "in_process_bounded_stdlib", "network_access": False,
                  "filesystem_access": False, "macro_execution": False,
                  "formula_evaluation": False, "external_relationships_followed": False},
    )
