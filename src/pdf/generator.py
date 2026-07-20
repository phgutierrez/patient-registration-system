from pathlib import Path
from typing import Mapping

from .inventory import get_document_spec
from .renderer import render_acroform
from .validators import validate_generated_pdf


def generate_pdf(document_type: str, values: Mapping[str, object], app_root: Path) -> bytes:
    spec = get_document_spec(document_type)
    normalized = {key: str(value or '') for key, value in values.items()}
    output_pages = spec.output_pages(normalized)
    required_fields = spec.required_fields | frozenset(
        name for name in spec.conditional_required_fields
        if normalized.get(name, '').strip()
    )
    result = render_acroform(
        spec.template_path(Path(app_root)),
        normalized,
        expected_template_pages=spec.expected_template_pages,
        output_pages=output_pages,
        required_fields=required_fields,
    )
    validate_generated_pdf(
        result.pdf_bytes,
        output_pages,
        (normalized[name] for name in required_fields),
        required_appearances_verified=(result.verified_appearances == len(required_fields)),
    )
    return result.pdf_bytes
