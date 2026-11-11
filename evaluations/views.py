import hashlib
import hmac
import json
import time
import uuid
from datetime import timedelta
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .forms import SessionForm, UploadForm
from .models import (AcademicSession, Assignment, AuditEvent, FrozenResult, ImportBatch, LoginThrottle,
                     PendingChange, Profile, ProjectGroup, Student, TemplateApproval, WebhookReceipt)
from .rubrics import RULESET, RUBRICS, STAGES
from .services import (audit, digest, freeze_final, freeze_stage, receive_evaluation, reopen, require,
                       resolve_change, role, stage_result)


def health(request): return JsonResponse({'status': 'ok', 'service': 'OBE-TraceX'})

def signin(request):
    if request.user.is_authenticated: return redirect('dashboard')
    error = ''
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()[:150]
        keys = [hashlib.sha256(x.encode()).hexdigest() for x in ['user:' + username.casefold(), 'ip:' + request.META.get('REMOTE_ADDR', '')]]
        now = timezone.now()
        with transaction.atomic():
            records = []
            for key in sorted(keys):
                item, _ = LoginThrottle.objects.get_or_create(key=key, defaults={'window_start': now})
                item = LoginThrottle.objects.select_for_update().get(pk=item.pk)
                if now - item.window_start > timedelta(minutes=15):
                    item.failures, item.window_start = 0, now
                records.append(item)
            blocked = any(x.failures >= (20 if x.key == keys[1] else 5) for x in records)
            user = None if blocked else authenticate(request, username=username, password=request.POST.get('password', ''))
            if user and role(user):
                profile = Profile.objects.select_for_update().get(user=user)
                if profile.mfa_secret:
                    from .mfa import verify
                    try:
                        valid_mfa = verify(profile, request.POST.get('otp', '').strip())
                    except Exception:
                        valid_mfa = False
                    if not valid_mfa:
                        user = None
                elif settings.PRODUCTION:
                    user = None
            if user and role(user):
                for item in records:
                    item.failures = 0
                    item.save()
                login(request, user)
                audit(user, 'account.signed_in', user.pk)
                return redirect('dashboard')
            for item in records:
                item.failures += 1
                item.save()
        error = 'Sign-in unsuccessful. Check your details or wait 15 minutes after repeated attempts.'
    return render(request, 'registration/login.html', {'error': error})

@login_required
@require_POST
def signout(request):
    audit(request.user, 'account.signed_out', request.user.pk)
    logout(request)
    return redirect('login')

def context(request, **kwargs):
    return {'portal_role': role(request.user), 'current_page': request.resolver_match.url_name, 'is_demo': False, **kwargs}

@login_required
def dashboard(request):
    groups = ProjectGroup.objects.select_related('session').prefetch_related('students').order_by('-session_id', 'project_id')
    selected_session = request.GET.get('session','')
    if selected_session.isdigit(): groups = groups.filter(session_id=selected_session)
    elif selected_session != 'all': groups = groups.exclude(session__label__startswith='DEMO ONLY')
    search = request.GET.get('q', '').strip()[:100]
    if search: groups = groups.filter(project_id__icontains=search) | groups.filter(title__icontains=search)
    groups = list(groups)
    for group in groups:
        group.frozen_count = FrozenResult.objects.filter(group=group, active=True, stage__in=STAGES).count()
        group.final = FrozenResult.objects.filter(group=group, active=True, stage='FINAL').first()
        group.completion = round(group.frozen_count / 6 * 100)
        group.progress_class = f'progress-{group.frozen_count}'
    return render(request, 'evaluations/dashboard.html', context(request, groups=groups, query=search, available_sessions=AcademicSession.objects.order_by('-id'), selected_session=selected_session,
        student_count=sum(g.students.count() for g in groups), frozen_count=FrozenResult.objects.filter(group__in=groups, active=True, stage__in=STAGES).count(),
        correction_count=PendingChange.objects.filter(status='pending').count(),
        final_count=FrozenResult.objects.filter(group__in=groups, active=True, stage='FINAL').count(),
        recent=AuditEvent.objects.select_related('actor')[:5], latest_import=ImportBatch.objects.order_by('-id').first()))

@login_required
def group_detail(request, pk):
    group = get_object_or_404(ProjectGroup.objects.select_related('session'), pk=pk)
    stages = []
    for code, rubric in RUBRICS.items():
        frozen = FrozenResult.objects.filter(group=group, stage=code, active=True).first()
        data = frozen.payload if frozen else stage_result(group, code)
        stages.append({'code': code, 'title': rubric['title'], 'maximum': sum(rubric['maxima']), 'data': data, 'frozen': frozen})
    return render(request, 'evaluations/group.html', context(request, group=group, stages=stages,
        master_records=__import__('evaluations.models',fromlist=['MasterRecord']).MasterRecord.objects.filter(student__group=group).select_related('student'),
        final=FrozenResult.objects.filter(group=group, stage='FINAL', active=True).first(), report_stages=(*STAGES, 'D7')))

@login_required
@require_POST
def result_action(request, pk):
    group = get_object_or_404(ProjectGroup, pk=pk)
    try:
        action = request.POST.get('action')
        note = request.POST.get('note', '')
        if action == 'freeze': freeze_stage(pk, request.POST.get('stage'), request.user, request.POST.get('version'), note)
        elif action == 'final': freeze_final(pk, request.user, request.POST.get('version'), note)
        elif action == 'reopen': reopen(pk, request.POST.get('stage'), request.user, note)
        else: raise ValueError('Unknown result action.')
        messages.success(request, 'Approval state updated and recorded in the audit history.')
    except (ValueError, TypeError) as error: messages.error(request, str(error))
    return redirect('group', pk=group.pk)

@login_required
def imports(request):
    require(request.user, ['coordinator'])
    form = UploadForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        from .importers import assignments_import, roster_import, workbook_import
        f = form.cleaned_data
        try:
            content = f['file'].read()
            if f['kind'] == 'workbook':
                if not f['file'].name.lower().endswith('.xlsx'): raise ValueError('Choose an XLSX workbook.')
                summary = workbook_import(content, f['session'], request.user)
                messages.success(request, f"Read complete: {summary['accepted']} accepted, {summary['held']} held, {len(summary['issues'])} issues.")
            else:
                if not f['file'].name.lower().endswith('.csv'): raise ValueError('Choose a CSV file.')
                count = (roster_import if f['kind'] == 'roster' else assignments_import)(content, f['session'], request.user)
                messages.success(request, f'{count} records imported.')
            return redirect('imports')
        except (ValueError, ValidationError, UnicodeError, KeyError, OSError) as error: messages.error(request, str(error))
        except Exception:
            messages.error(request, 'Import failed. Check the workbook format, schema and connection; no source file was changed.')
    return render(request, 'evaluations/imports.html', context(request, form=form,
        batches=ImportBatch.objects.select_related('session').order_by('-id')[:15], sessions=AcademicSession.objects.order_by('-id'),
        google_configured=bool(settings.GOOGLE_WORKBOOK_ID)))

@login_required
@require_POST
def sync(request):
    require(request.user, ['coordinator'])
    session = get_object_or_404(AcademicSession, pk=request.POST.get('session'))
    from .google_sync import sync_google
    from .models import MasterRecord
    if any(r.payload.get('source')=='faculty_reference_workbook' for r in MasterRecord.objects.filter(student__session=session)):
        messages.error(request,'This session preserves the saved faculty workbook. Choose a separate live Google session to avoid mixing sources.')
        return redirect('imports')
    try:
        summary = sync_google(session, request.user)
        messages.success(request, f"Google read complete: {summary['accepted']} accepted, {len(summary['issues'])} issues.")
    except Exception: messages.error(request, 'Google read failed. Check server credentials, workbook permissions and schema.')
    return redirect('imports')

@login_required
def sessions(request):
    form = SessionForm(request.POST or None)
    if request.method == 'POST':
        require(request.user, ['coordinator'])
        if form.is_valid():
            session = form.save()
            audit(request.user, 'session.created', session.pk)
            messages.success(request, 'Academic session created. Import its official roster next.')
            return redirect('sessions')
    return render(request, 'evaluations/sessions.html', context(request, form=form,
        sessions=AcademicSession.objects.order_by('-id'), ruleset=RULESET))

@login_required
@require_POST
@transaction.atomic
def approve_rules(request, pk):
    require(request.user, ['coordinator'])
    session = get_object_or_404(AcademicSession.objects.select_for_update(), pk=pk)
    note = request.POST.get('note', '').strip()
    if len(note) < 20 or request.POST.get('confirm') != 'yes':
        messages.error(request, 'Confirm the stated rules and record the faculty approval reference.')
    else:
        session.rules_approved, session.rules_approved_by, session.rules_approval_note = True, request.user, note
        session.save()
        audit(request.user, 'rules.approved', session.pk, {'ruleset': RULESET, 'note': note})
        messages.success(request, 'Session policy approved.')
    return redirect('sessions')

@login_required
def corrections(request):
    if request.method == 'POST':
        try:
            resolve_change(request.POST.get('change_id'), request.user, request.POST.get('decision') == 'approve', request.POST.get('note', ''))
            messages.success(request, 'Correction decision recorded.')
        except ValueError as error: messages.error(request, str(error))
        return redirect('corrections')
    return render(request, 'evaluations/corrections.html', context(request,
        changes=PendingChange.objects.select_related('assignment__student__group').order_by('-id')[:100]))

@login_required
def audit_view(request):
    return render(request, 'evaluations/audit.html', context(request, events=AuditEvent.objects.select_related('actor')[:200]))

@login_required
def templates_view(request):
    from .reports import template_path
    rows = []
    for code in (*STAGES, 'D7'):
        tdigest = hashlib.sha256(template_path(code).read_bytes()).hexdigest()
        rows.append({'stage': code, 'digest': tdigest, 'approved': TemplateApproval.objects.filter(stage=code, digest=tdigest).first()})
    if request.method == 'POST':
        require(request.user, ['coordinator'])
        stage, note = request.POST.get('stage'), request.POST.get('note', '').strip()
        match = next((x for x in rows if x['stage'] == stage), None)
        if not match or request.POST.get('digest') != match['digest'] or len(note) < 20 or request.POST.get('confirm') != 'yes':
            messages.error(request, 'Verify the exact template and record the approval reference.')
        else:
            TemplateApproval.objects.update_or_create(stage=stage, defaults={'digest': match['digest'], 'approved_by': request.user, 'note': note})
            audit(request.user, 'template.approved', stage, {'digest': match['digest'], 'note': note})
            messages.success(request, 'Template approval recorded for this exact file hash.')
        return redirect('templates')
    return render(request, 'evaluations/templates.html', context(request, templates=rows))

@login_required
def original_template(request, stage):
    from .reports import template_path
    try: path = template_path(stage)
    except ValueError: return HttpResponse(status=404)
    response = HttpResponse(path.read_bytes(), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = f'attachment; filename="{stage}_original.docx"'
    return response

@login_required
@require_POST
def export(request, pk, stage, extension):
    from .reports import export_report
    group = get_object_or_404(ProjectGroup, pk=pk)
    try: content, name = export_report(group, stage, extension, request.user)
    except ValueError as error:
        messages.error(request, str(error))
        return redirect('group', pk=pk)
    response = HttpResponse(content, content_type='application/pdf' if extension == 'pdf' else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    # Project IDs may be administrator-entered. Keep filename header free of special characters.
    import re
    name = re.sub(r'[^A-Za-z0-9_.-]', '_', name)
    response['Content-Disposition'] = f'attachment; filename="{name}"'
    return response

@csrf_exempt
@require_POST
def webhook(request):
    secret = settings.N8N_WEBHOOK_SECRET
    if len(secret) < 32: return JsonResponse({'error': 'Integration not configured.'}, status=503)
    if len(request.body) > 65536: return JsonResponse({'error': 'Payload too large.'}, status=413)
    signature = request.headers.get('X-OBE-Signature', '')
    expected = hmac.new(secret.encode(), request.body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected): return JsonResponse({'error': 'Invalid signature.'}, status=401)
    try:
        data = json.loads(request.body)
        if not isinstance(data, dict): raise ValueError('Expected an object.')
        if abs(time.time() - int(data['issued_at'])) > 300: raise ValueError('Expired event.')
        event_id = uuid.UUID(str(data['event_id']))
        body_digest = hashlib.sha256(request.body).hexdigest()
        with transaction.atomic():
            existing = WebhookReceipt.objects.filter(pk=event_id).first()
            if existing:
                if existing.digest != body_digest: raise ValueError('Event ID reused with a different payload.')
                return JsonResponse({'status': 'unchanged'})
            WebhookReceipt.objects.create(event_id=event_id, digest=body_digest)
            status = receive_evaluation(data['evaluation'])
        return JsonResponse({'status': status})
    except (ValueError, TypeError, KeyError, OverflowError): return JsonResponse({'error': 'Invalid or unassigned event.'}, status=400)

@login_required
@require_POST
def sample_template(request, stage, extension):
    from .reports import populate, render_pdf
    if stage not in (*STAGES, 'D7') or extension not in ('docx', 'pdf'):
        return HttpResponse(status=404)
    students = []
    for i in range(4):
        student = {'seat': f'SE-9900{i+1}', 'name': f'Sample Student {i+1}',
                   'total': '200' if stage == 'D7' else str(sum(RUBRICS[stage]['maxima']))}
        if stage == 'D7': student['stages'] = ['12', '20', '48', '48', '32', '40']
        else: student['criteria'] = [str(x) for x in RUBRICS[stage]['maxima']]
        students.append(student)
    content = populate(stage, {'students': students, 'course_code': 'SAMPLE',
                              'project_id': 'SAMPLE-ONLY', 'project_title': 'Template verification sample'})
    if extension == 'pdf':
        try: content = render_pdf(content)
        except ValueError as error:
            messages.error(request, str(error)); return redirect('templates')
    response = HttpResponse(content, content_type='application/pdf' if extension == 'pdf' else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = f'attachment; filename="SAMPLE_ONLY_{stage}.{extension}"'
    return response


def about(request):
    return render(request, 'evaluations/about.html')


def privacy(request):
    return render(request, 'evaluations/privacy.html')


@login_required
def profile(request):
    from .forms import ProfileForm
    from django.contrib.auth import get_user_model
    form = ProfileForm(request.POST or None, request.FILES or None, user=request.user,
                       initial={'first_name':request.user.first_name, 'last_name':request.user.last_name, 'email':request.user.email})
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            user = get_user_model().objects.select_for_update().get(pk=request.user.pk)
            person = Profile.objects.select_for_update().get(user=user)
            # Recheck after locking, so a concurrent email change cannot bypass confirmation.
            if form.cleaned_data['email'] != user.email and not user.check_password(form.cleaned_data['current_password']):
                form.add_error('current_password', 'Confirm your current password.')
            else:
                fields = ['first_name', 'last_name', 'email']
                changed = [field for field in fields if getattr(user, field) != form.cleaned_data[field]]
                for field in fields: setattr(user, field, form.cleaned_data[field])
                user.save(update_fields=fields)
                if form.cleaned_data['photo'] is not None or form.cleaned_data['remove_photo']:
                    person.avatar = form.cleaned_data['photo']
                    person.save(update_fields=['avatar'])
                    changed.append('photo')
                if changed: audit(request.user, 'account.profile_updated', user.pk, {'fields':changed})
                messages.success(request, 'Your profile has been saved.')
                return redirect('profile')
    return render(request, 'evaluations/profile.html', context(request, form=form))


@login_required
def avatar(request):
    image = request.user.profile.avatar
    if not image: return HttpResponse(status=404)
    response = HttpResponse(bytes(image), content_type='image/jpeg')
    response['X-Content-Type-Options'] = 'nosniff'
    return response


def entry(request):
    if request.user.is_authenticated:
        return dashboard(request)
    return redirect('welcome')


def welcome(request):
    return render(request, 'evaluations/welcome.html')
