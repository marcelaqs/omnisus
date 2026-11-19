"""Bounded record staging; DBC decompression still materializes the entire DBF.

Each batch is spooled to Arrow IPC so null-first and absent columns can be
reconciled before a second, bounded pass writes Parquet. Peak disk includes
DBF, IPC and Parquet; no list of frames or lazy references to deleted files.
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from omnisus.sources.datasus_ftp import dbc
from omnisus.sources.datasus_ftp.datasets import Release
from omnisus.sources.datasus_ftp.dbf_batches import (
    open_dbf_batches,
    physical_arrow_schema,
    physical_arrow_types,
)
from omnisus.transforms.dictionaries import Dicionario, load_dicionario


@dataclass(frozen=True)
class StagingResult:
    rows: int
    bytes: int


_DECLARED_TYPE = {"string": pa.string(), "date": pa.string(), "number": pa.float64()}
"""What a whole number of the file is staged as, by the ``type`` the dictionary declares."""


def _staged_types(
    physical: dict[str, pa.DataType], dic: Dicionario, replaced: set[str]
) -> dict[str, pa.DataType]:
    """The type each header field is staged with: its descriptor's, with one exception.

    A field the header declares ``N`` with no decimals is a whole number. When the
    dictionary declares it ``string`` or ``date`` (a date is text in the file), it is
    staged as text, the number as written and with no zeros added: ``0`` becomes
    ``"0"``, not the ``"0000"`` a ``C(4)`` month has (#40). When the dictionary declares
    it ``number``, it is staged as a number with decimals. Staged as published, such a
    field has one type in some files and another in the rest, and the lake refuses the
    second: ``num_proc``, ``insc_pn`` and ``seq_aih5`` of the RD are ``N`` in some
    months of 1992-2007, and 17 fields are ``N1.0`` in RDAC0909 alone (#219).

    Nothing else is converted: text the dictionary declares ``integer`` stays text.
    ``replaced`` are the columns staging overwrites with the scope's partition value.
    """
    declared = {field["name"]: _DECLARED_TYPE.get(field.get("type", "")) for field in dic.fields}
    return {
        name: declared.get(name) or kind
        if pa.types.is_integer(kind) and name not in replaced
        else kind
        for name, kind in physical.items()
    }


def _merge_schema(existing: pa.Schema, incoming: pa.Schema) -> pa.Schema:
    fields = {field.name: field for field in existing}
    for field in incoming:
        previous = fields.get(field.name)
        if previous is None or pa.types.is_null(previous.type):
            fields[field.name] = field
        elif pa.types.is_null(field.type) or previous.type == field.type:
            continue
        elif pa.types.is_signed_integer(previous.type) and pa.types.is_signed_integer(field.type):
            fields[field.name] = pa.field(field.name, pa.int64())
        elif pa.types.is_unsigned_integer(previous.type) and pa.types.is_unsigned_integer(
            field.type
        ):
            fields[field.name] = pa.field(field.name, pa.uint64())
        elif pa.types.is_floating(previous.type) and pa.types.is_floating(field.type):
            fields[field.name] = pa.field(field.name, pa.float64())
        else:
            raise TypeError(
                f"Incompatible batch types for {field.name}: {previous.type} / {field.type}"
            )
    return pa.schema(list(fields.values()))


def _staged_type_for_null_columns(schema: pa.Schema, staged: dict[str, pa.DataType]) -> pa.Schema:
    """Give a column that is blank in *this* file the type its field is staged with.

    A DATE column that happens to be empty in one year would otherwise stage as
    Arrow ``null``, pin the lake column to that type, and make the next year's
    real dates an unsafe schema change (``sinan_hanseniase``: ``dt_transrm`` is
    blank in all of HANSBR23). Every value is null, so any type is vacuously
    correct for *this* file; the one that keeps the lake column usable is the
    type a sibling file stages when the column is populated, which is
    :func:`_staged_types` of the header. Fields whose type we cannot map stay
    ``null``.
    """
    return pa.schema(
        [
            pa.field(field.name, staged[field.name])
            if pa.types.is_null(field.type) and field.name in staged
            else field
            for field in schema
        ]
    )


def _require_partition_value(column: pa.ChunkedArray, name: str, value: int | str) -> None:
    """A file column named like a partition must hold the scope's value in every row.

    Staging replaces it with the partition column. ER publishes its own ``ANO`` and
    ``MES``; in all 4,931 ER files on the server (2011-01 to 2026-07) they equal the
    file's year and month, so the replacement loses nothing. A file where they differ
    is refused instead of relabelled. Text is compared trimmed, and as a number
    when the partition is one, so ``"01"`` equals month 1.
    """
    text = pc.utf8_trim_whitespace(column.cast(pa.string()))
    if isinstance(value, int):
        digits = pc.fill_null(pc.match_substring_regex(text, "^[0-9]+$"), False)
        numbers = pc.cast(pc.if_else(digits, text, "-1"), pa.int64())
        same = pc.equal(numbers, value)
    else:
        same = pc.equal(text, value)
    differing = pc.filter(text, pc.invert(pc.fill_null(same, False)))
    if len(differing):
        raise ValueError(
            f"DBF column {name} holds {differing[0].as_py()!r} where the scope's {name} "
            f"is {value!r} ({len(differing)} rows); the file is not staged"
        )


def dbc_bytes_to_parquet(
    raw: bytes | Sequence[bytes],
    path: Path | str,
    *,
    dataset: str,
    ano: int | None = None,
    uf: str | None = None,
    dictionary: Path | None = None,
    mes: int | None = None,
    source_ano: int | None = None,
    release: Release | None = None,
) -> StagingResult:
    """Validate and stage records atomically; leave existing target intact on error.

    ``raw`` is one DBC, or the parts of one scope in part order; parts are
    staged into one Parquet and must share one DBF layout. Each part's record
    count is checked against its own header.

    Memory is bounded by the compressed payloads, one part's full decompressed
    DBF, and a record batch (not by all parsed frames). IPC spool trades extra
    disk I/O for lossless schema reconciliation. Caller owns the resulting
    Parquet lifetime.
    """
    from omnisus.sources.datasus_ftp import parse

    payloads = [raw] if isinstance(raw, (bytes, bytearray)) else list(raw)
    if not payloads:
        raise ValueError("no DBC payload to stage")
    dic = load_dicionario(dictionary if dictionary is not None else dataset)
    partitions = [
        (name, value, dtype)
        for name, value, dtype in [
            ("ano", ano, pa.uint16()),
            ("uf", uf, pa.string()),
            ("mes", mes, pa.uint8()),
            ("_source_ano", source_ano, pa.uint16()),
            ("_source_release", release, pa.string()),
        ]
        if value is not None
    ]
    physical: dict[str, pa.DataType] | None = None
    staged: dict[str, pa.DataType] = {}
    converted: dict[str, pa.DataType] = {}
    empty_schema = pa.schema([])
    path = Path(path)
    parsed = 0
    batches = 0
    schema = pa.schema([])
    with tempfile.TemporaryDirectory(prefix=".dbc-stage-", dir=path.parent) as directory:
        root = Path(directory)

        def spool(batch: pa.RecordBatch) -> None:
            nonlocal batches, schema
            table = pa.Table.from_batches([batch])
            # Descriptors pad names with NULs, but PSRR2401 spells "TIPPRE" plus two
            # spaces; both readers keep them. The header types strip them too.
            lowered = [name.strip().lower() for name in table.column_names]
            if len(set(lowered)) != len(lowered):
                raise ValueError("DBF column names collide after trimming and lowercasing")
            table = table.rename_columns(lowered)
            if "_source_ano" in lowered:
                raise ValueError("DBF uses reserved source column _source_ano")
            if "_source_release" in lowered:
                raise ValueError("DBF uses reserved source column _source_release")
            for index, field in enumerate(table.schema):
                if field.name in converted and not pa.types.is_null(field.type):
                    column = table.column(index).cast(converted[field.name])
                    table = table.set_column(index, field.name, column)
            for name, value, dtype in partitions:
                column = pa.array([value] * len(table), type=dtype, safe=True)
                index = table.schema.get_field_index(name)
                if index >= 0:
                    _require_partition_value(table.column(index), name, value)
                table = (
                    table.set_column(index, name, column)
                    if index >= 0
                    else table.append_column(name, column)
                )
            schema = _merge_schema(schema, table.schema)
            with (
                pa.OSFile(str(root / f"{batches}.arrow"), "wb") as sink,
                pa.ipc.new_file(sink, table.schema) as writer,
            ):
                writer.write_table(table)
            batches += 1

        for payload in payloads:
            dbf_bytes = dbc.decompress_bytes(payload)
            parse._check_dbf_length(dbf_bytes, dataset=dataset)
            if physical is None:
                physical = physical_arrow_types(dbf_bytes)
                staged = _staged_types(physical, dic, {name for name, _, _ in partitions})
                converted = {name: kind for name, kind in staged.items() if kind != physical[name]}
                empty_schema = physical_arrow_schema(dbf_bytes)
            elif physical_arrow_types(dbf_bytes) != physical:
                raise ValueError("parts of one scope have different DBF layouts")
            in_part = 0
            with open_dbf_batches(
                dbf_bytes, encoding=dic.encoding, batch_rows=parse.BATCH_ROWS
            ) as stream:
                for batch in stream:
                    in_part += batch.num_rows
                    spool(batch)
            parse._check_record_count(dbf_bytes, in_part, dataset=dataset)
            parsed += in_part
            del dbf_bytes
        assert physical is not None, "payloads is not empty"
        if not batches:
            schema = pa.schema(
                [
                    pa.field(field.name, staged.get(field.name, field.type))
                    for field in empty_schema
                ]
            )
            for name, _, dtype in partitions:
                index = schema.get_field_index(name)
                field = pa.field(name, dtype)
                schema = schema.set(index, field) if index >= 0 else schema.append(field)
        schema = _staged_type_for_null_columns(schema, staged)
        output = root / "output.parquet"
        with pq.ParquetWriter(output, schema) as writer:
            for number in range(batches):
                # Read into memory, not pa.memory_map: a zero-copy table keeps the
                # mapping alive past the with-block, and Windows refuses to unlink
                # a mapped file ("[WinError 5] Access is denied"). One batch at a
                # time, so memory stays bounded by a record batch.
                with pa.OSFile(str(root / f"{number}.arrow"), "rb") as source:
                    table = pa.ipc.open_file(source).read_all()
                    # column_names builds a new list on each access, so testing it per
                    # field is quadratic in the column count. spool keeps names unique,
                    # so the dict loses no column.
                    columns = dict(zip(table.column_names, table.columns, strict=True))
                    aligned = pa.Table.from_arrays(
                        [
                            columns[field.name].cast(field.type, safe=True)
                            if field.name in columns
                            else pa.nulls(len(table), type=field.type)
                            for field in schema
                        ],
                        schema=schema,
                    )
                    writer.write_table(aligned)
                (root / f"{number}.arrow").unlink()
        size = output.stat().st_size
        os.replace(output, path)
    return StagingResult(rows=parsed, bytes=size)
