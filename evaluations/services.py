"""Transactional grading, revisions and approval boundaries. No source-sheet writes."""
import hashlib
import json
from decimal import Decimal
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from .models import (Assignment, AuditEvent, Evaluation, FrozenResult, PendingChange, ProjectGroup, Student)
from .rubrics import RULESET, RUBRICS, STAGES, display, number, seat_number, weighted

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()

def role(user):
    if not user or not user.is_authenticated or not user.is_active: return ''
    try: return user.profile.role
    except Exception: return ''

def require(user, allowed):
    if role(user) not in allowed: raise PermissionDenied('Your role cannot perform this action.')

def audit(actor, action, target, detail=None):
    AuditEvent.objects.create(actor=actor, action=action, target=str(target), detail=detail or {})

def receive_evaluation(payload, actor=None):
    """One assigned evaluator's response. Identical replay is a no-op; changes require approval."""
    stage = str(payload.get('stage', ''))
    if stage not in RUBRICS: raise ValueError('Unknown rubric stage.')
    criteria = [str(x) for x in weighted(stage, payload.get('percentages', []))]
    seat = seat_number(payload.get('seat', ''))
    evaluator = str(payload.get('evaluator', '')).strip().lower()
    source_id = str(payload.get('source_id', '')).strip()
    if not source_id or len(source_id) > 160: raise ValueError('A stable response source_id is required.')
    if len(str(payload.get('comments', ''))) > 10000: raise ValueError('Comments are too long.')
    qs = Assignment.objects.select_related('student__group__session').filter(
        student__session__label=payload.get('session'), student__seat=seat, stage=stage,
        student__group__attempt=payload.get('attempt', 1), evaluator=evaluator)
    if qs.count() != 1: raise ValueError('No unique roster assignment for this student, stage, evaluator and attempt.')
    assignment = qs.get()
    data = {'criteria': criteria, 'comments': str(payload.get('comments', '')), 'source_id': source_id}
    content_hash = digest(data)
    with transaction.atomic():
        group = ProjectGroup.objects.select_for_update().get(pk=assignment.student.group_id)
        latest = assignment.revisions.order_by('-revision').first()
        if latest and latest.content_hash == content_hash: return 'unchanged'
        now = timezone.now()
        reason = ''
        if FrozenResult.objects.filter(group=group, stage__in=[stage, 'FINAL'], active=True).exists():
            reason = 'Stage or final result is frozen. Coordinator reopening and correction approval required.'
        elif latest:
            reason = 'Existing evaluation changed. Coordinator correction approval required.'
        elif (assignment.opens_at and now < assignment.opens_at) or (assignment.closes_at and now > assignment.closes_at):
            reason = 'Received outside the assigned evaluation period.'
        if reason:
            _, created = PendingChange.objects.get_or_create(assignment=assignment, digest=content_hash,
                defaults={'payload': data, 'reason': reason})
            if created: audit(actor, 'evaluation.held', assignment.pk, {'reason': reason})
            return 'held'
        Evaluation.objects.create(assignment=assignment, revision=1, content_hash=content_hash, **data)
        group.version += 1
        group.save(update_fields=['version'])
        audit(actor, 'evaluation.received', assignment.pk)
    return 'accepted'

@transaction.atomic
def resolve_change(change_id, actor, approve, note):
    require(actor, ['coordinator'])
    if len(note.strip()) < 10: raise ValueError('Explain the correction decision in at least 10 characters.')
    change = PendingChange.objects.select_related('assignment__student').get(pk=change_id)
    group = ProjectGroup.objects.select_for_update().get(pk=change.assignment.student.group_id)
    change = PendingChange.objects.select_for_update().get(pk=change_id)
    if change.status != 'pending': raise ValueError('This correction has already been reviewed.')
    if approve:
        if FrozenResult.objects.filter(group=group, stage__in=[change.assignment.stage, 'FINAL'], active=True).exists():
            raise ValueError('Ask the HOD to reopen this stage before accepting a correction.')
        last = change.assignment.revisions.order_by('-revision').first()
        Evaluation.objects.create(assignment=change.assignment, revision=last.revision + 1 if last else 1,
                                  content_hash=change.digest, **change.payload)
        group.version += 1
        group.save(update_fields=['version'])
    change.status = 'approved' if approve else 'rejected'
    change.save(update_fields=['status'])
    audit(actor, 'correction.' + change.status, change.pk, {'note': note})


def stage_result(group, stage):
    from .models import MasterRecord
    if MasterRecord.objects.filter(student__group=group).exists() or not Assignment.objects.filter(student__group=group).exists():
        from .master_sync import master_stage_result
        return master_stage_result(group, stage)
    errors, students = [], []
    if not group.session.rules_approved: errors.append('Coordinator must approve grading, rounding and evaluator policy for this session.')
    members = list(group.students.all())
    if len(members) != group.expected_members: errors.append('Roster does not match the expected group size.')
    if not 1 <= len(members) <= 4: errors.append('The supplied official templates support one to four members.')
    for student in members:
        assignments = list(Assignment.objects.filter(student=student, stage=stage).order_by('evaluator'))
        values = []
        if not assignments: errors.append(f'{student.seat}: no authorized evaluator assignments.')
        for assignment in assignments:
            latest = assignment.revisions.order_by('-revision').first()
            if latest is None: errors.append(f'{student.seat}: an assigned evaluation is missing.')
            else: values.append(latest)
        if PendingChange.objects.filter(assignment__in=assignments, status='pending').exists():
            errors.append(f'{student.seat}: resolve pending corrections before freezing.')
        if values and len(values) == len(assignments):
            n = Decimal(len(values))
            averages = [sum(number(v.criteria[i]) for v in values) / n for i in range(len(RUBRICS[stage]['maxima']))]
            students.append({'seat': student.seat, 'name': student.name,
                'criteria': [str(x) for x in averages], 'total': str(sum(averages)),
                'display_total': display(sum(averages)), 'evaluators': len(values),
                'revision_ids': [v.pk for v in values]})
    return {'stage': stage, 'ruleset': RULESET, 'project_id': group.project_id, 'project_title': group.title,
            'session': group.session.label, 'course_code': group.session.course_code, 'attempt': group.attempt,
            'students': students, 'errors': errors}

@transaction.atomic
def freeze_stage(group_id, stage, actor, expected_version, note):
    require(actor, ['coordinator'])
    if stage not in STAGES: raise ValueError('Unknown rubric stage.')
    if len(note.strip()) < 10: raise ValueError('A review note of at least 10 characters is required.')
    group = ProjectGroup.objects.select_for_update().select_related('session').get(pk=group_id)
    if group.version != int(expected_version): raise ValueError('Results changed since review. Reload before freezing.')
    if FrozenResult.objects.filter(group=group, stage=stage, active=True).exists(): raise ValueError('Stage is already frozen.')
    data = stage_result(group, stage)
    if data['errors']: raise ValueError(' '.join(data['errors']))
    version = (FrozenResult.objects.filter(group=group, stage=stage).aggregate(n=Max('version'))['n'] or 0) + 1
    result = FrozenResult.objects.create(group=group, stage=stage, version=version, payload=data,
                                         digest=digest(data), created_by=actor)
    group.version += 1
    group.save(update_fields=['version'])
    audit(actor, 'stage.frozen', result.pk, {'note': note, 'digest': result.digest})
    return result

@transaction.atomic
def freeze_final(group_id, actor, expected_version, note):
    require(actor, ['coordinator'])
    if len(note.strip()) < 10: raise ValueError('A final approval note is required.')
    group = ProjectGroup.objects.select_for_update().select_related('session').get(pk=group_id)
    if group.version != int(expected_version): raise ValueError('Results changed since review. Reload before approval.')
    if not group.session.rules_approved: raise ValueError('Session rules are not approved.')
    if FrozenResult.objects.filter(group=group, stage='FINAL', active=True).exists(): raise ValueError('Final result is already frozen.')
    if PendingChange.objects.filter(assignment__student__group=group, status='pending').exists():
        raise ValueError('Unresolved corrections prevent final approval.')
    sources = {x.stage: x for x in FrozenResult.objects.filter(group=group, active=True, stage__in=STAGES)}
    if set(sources) != set(STAGES): raise ValueError('All six stages must be frozen before final approval.')
    roster = [(s.seat, s.name) for s in group.students.all()]
    for source in sources.values():
        if [(s['seat'], s['name']) for s in source.payload['students']] != roster:
            raise ValueError('A frozen stage no longer matches the group roster.')
        if digest(source.payload) != source.digest: raise ValueError('Frozen data integrity check failed.')
    students = []
    for seat, name in roster:
        parts = [next(x for x in sources[stage].payload['students'] if x['seat'] == seat)['total'] for stage in STAGES]
        total = sum(number(x) for x in parts)
        from .models import MasterRecord
        master = MasterRecord.objects.filter(student__group=group, student__seat=seat).first()
        if master:
            if master.errors or master.payload.get('final') is None:
                raise ValueError('Master workbook has unresolved reconciliation issues.')
            total = number(master.payload['final'])
        students.append({'seat': seat, 'name': name, 'stages': parts, 'total': str(total), 'display_total': display(total)})
    data = {'students': students, 'stages': {k: str(v.pk) for k, v in sources.items()}, 'ruleset': RULESET,
            'project_id': group.project_id, 'project_title': group.title, 'session': group.session.label,
            'attempt': group.attempt, 'course_code': group.session.course_code, 'rounding': 'display-only-2dp-half-up'}
    version = (FrozenResult.objects.filter(group=group, stage='FINAL').aggregate(n=Max('version'))['n'] or 0) + 1
    result = FrozenResult.objects.create(group=group, stage='FINAL', version=version, payload=data,
                                         digest=digest(data), created_by=actor)
    group.version += 1
    group.save(update_fields=['version'])
    audit(actor, 'final.approved', result.pk, {'note': note, 'digest': result.digest})
    return result

@transaction.atomic
def reopen(group_id, stage, actor, note):
    require(actor, ['coordinator'])
    if stage not in (*STAGES, 'FINAL'): raise ValueError('Unknown stage.')
    if len(note.strip()) < 10: raise ValueError('A reason of at least 10 characters is required.')
    group = ProjectGroup.objects.select_for_update().get(pk=group_id)
    results = list(FrozenResult.objects.filter(group=group, stage__in=[stage, 'FINAL'], active=True))
    if not results: raise ValueError('There is no active frozen result to reopen.')
    FrozenResult.objects.filter(pk__in=[x.pk for x in results]).update(active=False)
    group.version += 1
    group.save(update_fields=['version'])
    audit(actor, 'result.reopened', group.pk, {'stage': stage, 'reason': note, 'superseded': [str(x.pk) for x in results]})
