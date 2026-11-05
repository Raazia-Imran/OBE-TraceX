"""Populate supplied DOCX originals, retaining table geometry, sections and artwork."""
import hashlib
import io
import subprocess
import tempfile
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn
from django.conf import settings
from django.db import transaction
from .models import FrozenResult, ProjectGroup, Report, TemplateApproval
from .rubrics import STAGES, display
from .services import audit, digest, require

def template_path(stage):
    if stage not in (*STAGES, 'D7'): raise ValueError('Unknown official template.')
    return settings.REPORT_TEMPLATE_DIR / f'{stage}.docx'

def replace_text(paragraph, old, new):
    """Replace a span across runs without replacing paragraph/run formatting."""
    text = paragraph.text
    start = text.find(old)
    if start < 0: return
    end = start + len(old)
    position, inserted = 0, False
    for run in paragraph.runs:
        current = run.text
        a, b = position, position + len(current)
        if a < end and b > start:
            before = current[:max(0, start-a)]
            after = current[max(0, end-a):]
            run.text = before + (new if not inserted else '') + after
            inserted = True
        position = b

def put_cell(cell, text):
    paragraph = cell.paragraphs[0]
    if paragraph.runs:
        paragraph.runs[0].text = str(text)
        for run in paragraph.runs[1:]: run.text = ''
    else: paragraph.add_run(str(text))
    for extra in cell.paragraphs[1:]:
        for run in extra.runs: run.text = ''

def populate(stage, payload):
    document = Document(template_path(stage))
    students = payload['students']
    if not 1 <= len(students) <= 4: raise ValueError('Original templates support at most four members. Faculty approval is required for a different layout.')
    summary_nodes = []
    for node in document.element.body:
        if node.tag == qn('w:tbl'): break
        summary_nodes.append(node)
    for paragraph in document.paragraphs:
        replace_text(paragraph, '<FYDP Course Code>', payload['course_code'])
        replace_text(paragraph, '____________________ Engineering', 'Software Engineering')
        text = paragraph.text
        # Only the group-summary project field belongs to this export. Supplementary
        # evaluator rubric pages remain blank masters; filling their tight identity
        # line without per-student context can both mislabel them and change pagination.
        if 'Project ID:' in text and paragraph._p in summary_nodes:
            import re
            match = re.search(r'(?<=Project ID:)[ \t]*_+', text)
            if match: replace_text(paragraph, match.group(), '  ' + payload['project_id'])
        if paragraph.text.strip().startswith('Project Title:') and not paragraph.text.split('Project Title:', 1)[1].strip():
            # The source has a tab with a right-hand stop. Fill the field before that tab,
            # rather than appending beyond it and pushing the project title off the page.
            replace_text(paragraph, 'Project Title:', 'Project Title: ' + payload['project_title'])
    table = document.tables[0]
    for index, student in enumerate(students):
        cells = table.rows[index + 2].cells
        values = [str(index + 1), student['name'], student['seat']]
        if stage == 'D7': values += [display(x) for x in student['stages']] + [display(student['total'])]
        else: values += [display(x) for x in student['criteria']] + [display(student['total'])]
        if len(values) != len(cells): raise ValueError('Template columns do not match the rubric mapping.')
        for cell, value in zip(cells, values): put_cell(cell, value)
    data = io.BytesIO()
    document.save(data)
    return data.getvalue()

def render_pdf(content):
    with tempfile.TemporaryDirectory(prefix='obe-report-') as folder:
        source = Path(folder) / 'rubric.docx'
        source.write_bytes(content)
        try:
            subprocess.run([settings.SOFFICE_PATH, '--headless', f'-env:UserInstallation=file://{folder}/profile',
                            '--convert-to', 'pdf', '--outdir', folder, str(source)],
                           check=True, capture_output=True, timeout=75)
        except (subprocess.SubprocessError, OSError) as error:
            raise ValueError('PDF conversion unavailable. Check the server LibreOffice installation.') from error
        pdf = Path(folder) / 'rubric.pdf'
        if not pdf.exists() or not pdf.read_bytes().startswith(b'%PDF-'): raise ValueError('Renderer did not produce a valid PDF.')
        return pdf.read_bytes()

def export_report(group, stage, extension, actor):
    require(actor, ['coordinator', 'hod'])
    if extension not in ('docx', 'pdf'): raise ValueError('Unsupported report format.')
    final = FrozenResult.objects.filter(group=group, stage='FINAL', active=True).first()
    if not final: raise ValueError('HOD final approval is required before official QEC export.')
    if digest(final.payload) != final.digest: raise ValueError('Frozen data integrity check failed.')
    tdigest = hashlib.sha256(template_path(stage).read_bytes()).hexdigest()
    if not TemplateApproval.objects.filter(stage=stage, digest=tdigest).exists():
        raise ValueError('HOD must verify this exact template before official export.')
    if stage == 'D7': payload = final.payload
    else:
        result = FrozenResult.objects.get(pk=final.payload['stages'][stage], active=True)
        if digest(result.payload) != result.digest: raise ValueError('Stage data integrity check failed.')
        payload = result.payload
    content = populate(stage, payload)
    if extension == 'pdf': content = render_pdf(content)
    # PDF conversion can take time. Re-check approval under the same group lock used by
    # reopening, rather than publishing a result that was superseded during rendering.
    with transaction.atomic():
        ProjectGroup.objects.select_for_update().get(pk=group.pk)
        if not FrozenResult.objects.filter(pk=final.pk, active=True, digest=final.digest).exists():
            raise ValueError('Approval changed while the report was generated. Reload the group.')
        if hashlib.sha256(template_path(stage).read_bytes()).hexdigest() != tdigest:
            raise ValueError('The template changed while the report was generated. Verify it again.')
        report = Report.objects.create(result=final, stage=stage, template_digest=tdigest,
            file_digest=hashlib.sha256(content).hexdigest(), format=extension, created_by=actor)
        audit(actor, 'report.exported', report.pk, {'stage': stage, 'final_version': final.version, 'format': extension})
    return content, f'{group.project_id}_{stage}_v{final.version}.{extension}'
