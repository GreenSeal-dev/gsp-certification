"""Load, validate and score GSP requirements from gsp_requirements.yml.

Shared by the Excel converter (convert_cert_2.py) and the website builder
(build_site.py).
"""
import yaml


def calculate_linear_scores(scale_list):
    """Spread scores linearly from 1.0 (first option) to 0.0 (last option)."""
    n = len(scale_list)
    if n <= 1:
        return {scale_list[0]: 1.0} if n == 1 else {}
    return {item: round(1.0 - (i / (n - 1)), 2) for i, item in enumerate(scale_list)}


def scores_for(req):
    """Score per assessment option: the custom `scoring` map, or linear scores."""
    return req.get('scoring') or calculate_linear_scores(req.get('assessment_scale', []))


def parse_requirements(text):
    """Parse YAML text and validate it. Returns the parsed document."""
    data = yaml.safe_load(text)
    seen = set()
    for category in data.get('categories', []):
        for req in category.get('requirements', []):
            req_id = req.get('id')
            # 'levels' is mandatory — fail fast with a clear message
            if 'levels' not in req:
                raise ValueError(
                    f"Requirement '{req_id}' is missing the required 'levels' field. "
                    f"Add 'levels: [1]', 'levels: [2]', or 'levels: [1, 2]'."
                )
            if req_id in seen:
                raise ValueError(f"Duplicate requirement id '{req_id}'.")
            seen.add(req_id)
    return data


def load_requirements(path):
    """Read and validate a requirements YAML file."""
    with open(path, 'r', encoding='utf-8') as f:
        return parse_requirements(f.read())


def iter_requirements(data, level=None):
    """Yield (category, requirement) pairs in file order, optionally for one level."""
    for category in data.get('categories', []):
        for req in category.get('requirements', []):
            if level is None or level in req['levels']:
                yield category, req
