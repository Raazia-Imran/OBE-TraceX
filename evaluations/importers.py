"""Read-only adapters. Raw source responses are never written back or silently repaired."""
import csv
import hashlib
import io
import re
from collections import Counter
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.dateparse import parse_datetime
from .models import AcademicSession, Assignment, FrozenResult, ImportBatch, ProjectGroup, Student
from .rubrics import RUBRICS, STAGES, percentage, seat_number
from .services import audit, receive_evaluation, require

RAW_TABS = {'D1': 'D1_Proposal', 'D2': 'D2_S1_Progress', 'D3': 'D3_S1_Eval',
            'D4': 'D4_S2_Progress', 'D5': 'D5_Final_Report', 'D6': 'D6_Final_Eval'}

def clean_rows(values):
    if not values: return []
    headers = [str(x or '').strip() for x in values[0]]
    if len([x for x in headers if x]) != len(set(x for x in headers if x)):
        raise ValueError('Duplicate source headers are ambiguous.')
    return [dict(zip(headers, row)) for row in values[1:] if any(x is not None and x != '' for x in row)]

def criterion_columns(stage, headers):
    prefixes = {'D1': 'Proposal Evaluation Criteria', 'D2': 'Proposal Evaluation Criteria',
                'D3': 'Mid-Year Evaluation Criteria', 'D4': 'Semester 2 Progress Performance',
                'D5': 'Final Report Evaluation Criteria', 'D6': 'Final Presentation Evaluation'}
    columns = [x for x in headers if x.startswith(prefixes[stage]) or
               (stage == 'D4' and x.startswith('V. Timely Report Submission'))]
    order = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII'][:len(RUBRICS[stage]['maxima'])]
    mapping = {}
    for column in columns:
        match = re.search(r'(?:\[|^)([IVX]+)\.', column)
        if not match or match[1] not in order or match[1] in mapping:
            return []
        mapping[match[1]] = column
    return [mapping[x] for x in order] if set(mapping) == set(order) else []

def inspect_and_import(tabs, session, actor, source_digest):
    require(actor, ['coordinator'])
    summary = {'accepted': 0, 'held': 0, 'unchanged': 0, 'issues': [], 'source': 'read-only response import'}
    for stage, tab in RAW_TABS.items():
        values = tabs.get(tab)
        if not values:
            summary['issues'].append(f'{stage}: missing or empty raw response tab.')
            continue
        rows = clean_rows(values)
        columns = criterion_columns(stage, list(rows[0]) if rows else [])
        if len(columns) != len(RUBRICS[stage]['maxima']):
            summary['issues'].append(f'{stage}: criterion headers do not match the approved schema.')
            continue
        identities = Counter((str(r.get('Seat Number / Roll Number', '')).strip().upper(),
                              str(r.get('Email Address', '')).strip().lower()) for r in rows)
        for index, row in enumerate(rows, 2):
            raw_seat = row.get('Seat Number / Roll Number', '')
            if not raw_seat: continue
            evaluator = str(row.get('Email Address', '')).strip().lower()
            try:
                seat = seat_number(raw_seat)
                validate_email(evaluator)
                if identities[(seat, evaluator)] > 1:
                    raise ValueError('Repeated evaluator email for this seat: resolve duplicate/correction identity before import.')
                timestamp = str(row.get('Timestamp', '')).strip()
                if not timestamp: raise ValueError('Response timestamp is missing; stable response identity is required.')
                attempts = list(Student.objects.filter(session=session, seat=seat).values_list('group__attempt', flat=True))
                if len(attempts) != 1: raise ValueError('Student is missing from roster or attempt is ambiguous.')
                payload = {'session': session.label, 'seat': seat, 'stage': stage, 'evaluator': evaluator,
                           'attempt': attempts[0], 'source_id': hashlib.sha256(f'{tab}:{timestamp}:{evaluator}:{seat}'.encode()).hexdigest(),
                           'percentages': [str(percentage(row.get(c))) for c in columns],
                           'comments': str(row.get('Evaluator/Supervisor Comments (if any)', row.get('Supervisor Comments (if any)', '')) or '')}
                status = receive_evaluation(payload, actor)
                summary[status] += 1
            except (ValueError, ValidationError) as error:
                summary['issues'].append(f'{stage} row {index}: {error}')
    ImportBatch.objects.create(session=session, digest=source_digest, summary=summary, created_by=actor)
    audit(actor, 'source.imported', session.pk, {k: summary[k] for k in ['accepted', 'held', 'unchanged']})
    return summary

def workbook_import(content, session, actor):
    import openpyxl
    import zipfile
    if len(content) > 12 * 1024 * 1024: raise ValueError('Workbook exceeds 12 MB.')
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        if sum(x.file_size for x in archive.infolist()) > 100 * 1024 * 1024: raise ValueError('Workbook expands beyond the import limit.')
    workbook = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    try:
        tabs = {}
        from .master_sync import READ_TABS
        for name in READ_TABS:
            if name in workbook:
                sheet = workbook[name]
                rows = []
                for i, row in enumerate(sheet.iter_rows(max_row=50001, max_col=26, values_only=True)):
                    seat_column=3 if name in RAW_TABS.values() else 2
                    if i and (len(row)<=seat_column or row[seat_column] is None or not str(row[seat_column]).strip()): continue
                    if i>=50000 or len(rows)>=10000: raise ValueError('Populated source data exceeds the import boundary.')
                    rows.append(list(row))
                tabs[name] = rows
        from .master_sync import import_master
        return import_master(tabs, session, actor, hashlib.sha256(content).hexdigest())
    finally: workbook.close()

@transaction.atomic
def roster_import(content, session, actor):
    require(actor, ['coordinator'])
    rows = list(csv.DictReader(io.StringIO(content.decode('utf-8-sig'))))
    if not rows or len(rows) > 2000: raise ValueError('Provide 1–2000 roster rows.')
    seen, checked, groups = set(), [], {}
    for row in rows:
        seat = seat_number(row.get('seat', ''))
        if seat in seen: raise ValueError('Duplicate seat number in the roster upload.')
        seen.add(seat)
        project = str(row.get('project_id', '')).strip().upper()
        name, title = str(row.get('name', '')).strip(), str(row.get('project_title', '')).strip()
        size = int(row.get('expected_members', 0))
        attempt = int(row.get('attempt', 1))
        if not project or not title or not name or not 1 <= size <= 4 or attempt < 1:
            raise ValueError('Roster requires project ID/title, official name, attempt and 1–4 expected members.')
        if len(name) > 160 or len(title) > 240 or len(project) > 80: raise ValueError('Roster field too long.')
        key = (project, attempt)
        if key in groups and groups[key] != (title, size): raise ValueError('Conflicting group title or size.')
        groups[key] = (title, size)
        checked.append((seat, name, key))
    if Student.objects.filter(session=session).exists():
        raise ValueError('Roster already exists. This pilot accepts one roster import per session; use a new test session for corrections.')
    for (project, attempt), (title, size) in groups.items():
        ProjectGroup.objects.create(session=session, project_id=project, title=title, attempt=attempt, expected_members=size)
    for seat, name, (project, attempt) in checked:
        group = ProjectGroup.objects.get(session=session, project_id=project, attempt=attempt)
        Student.objects.create(group=group, session=session, seat=seat, name=name)
    audit(actor, 'roster.imported', session.pk, {'students': len(checked), 'groups': len(groups)})
    return len(checked)

@transaction.atomic
def assignments_import(content, session, actor):
    require(actor, ['coordinator'])
    rows = list(csv.DictReader(io.StringIO(content.decode('utf-8-sig'))))
    if not rows or len(rows) > 20000: raise ValueError('Provide 1–20,000 assignment rows.')
    count = 0
    # Lock all affected groups before creating assignments to serialize against freeze operations.
    list(ProjectGroup.objects.select_for_update().filter(session=session).order_by('pk'))
    for row in rows:
        seat, stage = seat_number(row.get('seat', '')), row.get('stage', '').strip().upper()
        email = row.get('evaluator', '').strip().lower()
        validate_email(email)
        if stage not in STAGES: raise ValueError('Unknown stage.')
        students = Student.objects.filter(session=session, seat=seat, group__attempt=int(row.get('attempt', 1)))
        if students.count() != 1: raise ValueError('Assignment must match exactly one student and attempt.')
        student = students.get()
        if FrozenResult.objects.filter(group=student.group, active=True).exists(): raise ValueError('Assignments cannot change after any stage is frozen.')
        dates = {}
        for key in ['opens_at', 'closes_at']:
            value = row.get(key, '').strip()
            parsed = parse_datetime(value) if value else None
            if value and (parsed is None or parsed.tzinfo is None): raise ValueError('Schedule timestamps require ISO 8601 with a time zone.')
            dates[key] = parsed
        if dates['opens_at'] and dates['closes_at'] and dates['opens_at'] >= dates['closes_at']: raise ValueError('Closing time must follow opening time.')
        _, created = Assignment.objects.get_or_create(student=student, stage=stage, evaluator=email, defaults=dates)
        count += int(created)
    audit(actor, 'assignments.imported', session.pk, {'added': count})
    return count
