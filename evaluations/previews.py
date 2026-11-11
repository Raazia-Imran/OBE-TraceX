import io
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from docx import Document
from .models import ProjectGroup, MasterRecord, FrozenResult
from .services import stage_result, require, audit
from .reports import populate,render_pdf
from .rubrics import STAGES
@login_required
@require_POST
def preview(request,pk,stage,extension):
    require(request.user,['coordinator','hod'])
    group=get_object_or_404(ProjectGroup,pk=pk)
    if stage not in (*STAGES,'D7') or extension not in ('docx','pdf'):return HttpResponse(status=404)
    if stage=='D7':
        final=FrozenResult.objects.filter(group=group,stage='FINAL',active=True).first()
        if final:payload=final.payload
        else:
            records=MasterRecord.objects.filter(student__group=group).select_related('student').order_by('student__seat')
            students=[{'name':r.student.name,'seat':r.student.seat,'stages':[r.payload['reported_stages'][s] for s in STAGES],'total':r.payload['final']} for r in records]
            if len(students)!=group.expected_members:return HttpResponse('Complete source marks are required for this preview.',status=409)
            payload={'students':students,'course_code':group.session.course_code,'project_id':group.project_id,'project_title':group.title}
    else:
        payload=stage_result(group,stage)
        if len(payload['students'])!=group.expected_members:return HttpResponse('Complete stage marks are required for this preview.',status=409)
    content=populate(stage,payload)
    doc=Document(io.BytesIO(content))
    header=doc.sections[0].header.paragraphs[0]
    header.text='PREVIEW ONLY | '+group.session.label+' | Not an official approved record'
    for run in header.runs:
        from docx.shared import Pt,RGBColor
        run.font.size=Pt(8);run.font.color.rgb=RGBColor.from_string('A4262C')
    out=io.BytesIO();doc.save(out);content=out.getvalue()
    if extension=='pdf':
        try:content=render_pdf(content)
        except ValueError:return HttpResponse('PDF conversion unavailable. Download the Word preview.',status=503)
    from .archive import save_document
    import hashlib
    save_document(group,stage,'preview',f'PREVIEW_{group.project_id}_{stage}.{extension}',content,extension,'preview:'+str(group.pk)+':'+stage+':'+hashlib.sha256(content).hexdigest())
    audit(request.user,'report.previewed',group.pk,{'stage':stage,'format':extension,'official':False})
    response=HttpResponse(content,content_type='application/pdf' if extension=='pdf' else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition']=f'attachment; filename="PREVIEW_{group.pk}_{stage}.{extension}"'
    return response
