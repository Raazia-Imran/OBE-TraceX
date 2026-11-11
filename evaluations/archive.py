import base64,hashlib,hmac,json,re,time,os
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse,JsonResponse
from django.shortcuts import get_object_or_404,render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import StoredDocument,Student,StageForm,SyncState,AuditEvent
from .services import audit,require
MIMES={'html':'text/html','pdf':'application/pdf','docx':'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}
def save_document(group,stage,kind,name,content,extension,source_id,student=None):
    if extension not in MIMES or stage not in ('D1','D2','D3','D4','D5','D6','D7'):raise ValueError('Invalid document type.')
    if not content or len(content)>5*1024*1024:raise ValueError('Document must be between 1 byte and 5 MB.')
    if extension=='pdf' and not content.startswith(b'%PDF-'):raise ValueError('Invalid PDF.')
    if extension=='docx' and not content.startswith(b'PK'):raise ValueError('Invalid Word file.')
    name=re.sub(r'[^A-Za-z0-9_.-]','_',name)[:180]
    digest=hashlib.sha256(content).hexdigest()
    with transaction.atomic():
        obj,created=StoredDocument.objects.get_or_create(source_id=source_id,defaults={'group':group,'student':student,'stage':stage,'kind':kind,'name':name,'content':content,'mime':MIMES[extension],'digest':digest})
        if obj.digest!=digest or obj.group_id!=group.pk or obj.student_id!=(student.pk if student else None) or obj.stage!=stage:
            raise ValueError('Source identity was reused with different document data.')
    return obj,created
@login_required
def documents(request):
    require(request.user,['coordinator','hod'])
    rows=StoredDocument.objects.select_related('group__session','student')
    q=request.GET.get('q','').strip()[:100]
    if q:
        from django.db.models import Q
        rows=rows.filter(Q(group__project_id__icontains=q)|Q(student__seat__icontains=q)|Q(student__name__icontains=q))
    from .views import context
    return render(request,'evaluations/documents.html',context(request,documents=rows[:200],query=q))
@login_required
def download(request,pk):
    require(request.user,['coordinator','hod'])
    item=get_object_or_404(StoredDocument,pk=pk);content=bytes(item.content)
    if hashlib.sha256(content).hexdigest()!=item.digest:return HttpResponse('Document integrity verification failed.',status=409)
    audit(request.user,'document.downloaded',item.pk,{'kind':item.kind})
    response=HttpResponse(content,content_type=item.mime);response['Content-Disposition']=f'attachment; filename="{item.name}"'
    return response
@csrf_exempt
@require_POST
def ingest_report(request):
    secret=os.getenv('OBE_REPORT_WEBHOOK_SECRET',settings.N8N_WEBHOOK_SECRET)
    if len(secret)<32:return JsonResponse({'error':'Report integration not configured.'},status=503)
    if len(request.body)>8*1024*1024:return JsonResponse({'error':'Payload too large.'},status=413)
    expected=hmac.new(secret.encode(),request.body,hashlib.sha256).hexdigest()
    if not hmac.compare_digest(request.headers.get('X-OBE-Signature',''),expected):return JsonResponse({'error':'Invalid signature.'},status=401)
    try:
        data=json.loads(request.body)
        if abs(time.time()-int(data['issued_at']))>300:raise ValueError('Expired envelope.')
        source=str(data['event_id'])
        if not re.fullmatch(r'[A-Za-z0-9:_-]{1,160}',source):raise ValueError('Invalid identity.')
        report=data['report'];student=Student.objects.get(session__label=report['session'],seat=report['seat'],group__attempt=report.get('attempt',1))
        content=base64.b64decode(report['content_base64'],validate=True)
        obj,created=save_document(student.group,report['stage'],'n8n_individual',report['filename'],content,report['extension'],'n8n:'+source,student)
        if created:audit(None,'report.archived',obj.pk,{'source':'n8n','student':student.pk})
        return JsonResponse({'status':'saved' if created else 'unchanged','document_id':obj.pk})
    except (ValueError,TypeError,KeyError,Student.DoesNotExist,Student.MultipleObjectsReturned):
        return JsonResponse({'error':'Invalid report envelope or student identity.'},status=400)
@login_required
def source_hub(request):
    require(request.user,['coordinator','hod'])
    from .views import context
    return render(request,'evaluations/hub.html',context(request,links=StageForm.objects.select_related('session').order_by('-session_id','stage'),states=SyncState.objects.select_related('session')))
@login_required
def workspace_state(request):
    require(request.user,['coordinator','hod'])
    return JsonResponse({'revision':AuditEvent.objects.order_by('-id').values_list('id',flat=True).first() or 0,'states':[{'session':s.session_id,'last_success':s.succeeded_at.isoformat() if s.succeeded_at else None,'error':s.error} for s in SyncState.objects.all()]})

@login_required
def comparison(request):
    require(request.user,['coordinator','hod'])
    from decimal import Decimal,InvalidOperation
    from .models import AcademicSession,MasterRecord
    from .views import context
    refs=MasterRecord.objects.filter(payload__source='faculty_reference_workbook').select_related('student__group').order_by('student__seat')
    available=AcademicSession.objects.filter(student__masterrecord__isnull=False).exclude(pk__in=refs.values_list('student__session_id',flat=True)).exclude(course_code='REHEARSAL').distinct().order_by('-pk')
    selected=request.GET.get('session','')
    live=available.filter(pk=selected).first() if selected.isdigit() else available.filter(label__startswith='Live Google').first()
    rows=[]
    for ref in refs:
        candidate=MasterRecord.objects.filter(student__seat=ref.student.seat,student__session=live).first() if live else None
        expected=ref.payload.get('reported_stages',{})
        actual=candidate.payload.get('reported_stages',{}) if candidate else {}
        parts=[{'stage':code,'expected':expected.get(code),'actual':actual.get(code)} for code in ('D1','D2','D3','D4','D5','D6')]
        match=False;delta=None
        if candidate:
            try:
                delta=Decimal(candidate.payload['final'])-Decimal(ref.payload['final'])
                match=delta==0 and all(Decimal(str(x['actual']))==Decimal(str(x['expected'])) for x in parts)
            except (InvalidOperation,TypeError,KeyError):pass
        rows.append({'student':ref.student,'expected':ref.payload.get('final'),'actual':candidate.payload.get('final') if candidate else None,'delta':delta,'match':match,'parts':parts,'missing':candidate is None,'errors':candidate.errors if candidate else []})
    return render(request,'evaluations/comparison.html',context(request,rows=rows,available=available,selected=live,matched=sum(r['match'] for r in rows),missing=sum(r['missing'] for r in rows)))

@login_required
def workbook(request):
    require(request.user,['coordinator','hod'])
    from .models import AcademicSession,MasterRecord
    from .views import context
    available=AcademicSession.objects.filter(student__masterrecord__isnull=False).distinct().order_by('-pk')
    selected=request.GET.get('session','')
    session=available.filter(pk=selected).first() if selected.isdigit() else available.first()
    rows=MasterRecord.objects.filter(student__session=session).select_related('student__group')
    return render(request,'evaluations/workbook.html',context(request,records=rows,available=available,selected=session))
