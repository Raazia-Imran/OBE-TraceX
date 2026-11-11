import os, re
from urllib.parse import urlparse
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import AcademicSession, ProjectGroup, Student, Assignment, FrozenResult, StageForm
from .rubrics import STAGE_CHOICES
from .services import audit, require

class GrantForm(forms.Form):
    group = forms.ModelChoiceField(queryset=ProjectGroup.objects.select_related('session').order_by('-session_id','project_id'))
    stage = forms.ChoiceField(choices=STAGE_CHOICES)
    evaluator = forms.EmailField(label='Approved evaluator email')
    opens_at = forms.DateTimeField(required=False, widget=forms.DateTimeInput(attrs={'type':'datetime-local'}))
    closes_at = forms.DateTimeField(required=False, widget=forms.DateTimeInput(attrs={'type':'datetime-local'}))
    def clean(self):
        d=super().clean()
        if d.get('opens_at') and d.get('closes_at') and d['opens_at']>=d['closes_at']:
            raise forms.ValidationError('Closing time must follow opening time.')
        if d.get('evaluator'): d['evaluator']=d['evaluator'].strip().lower()
        return d

class LinkForm(forms.ModelForm):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        if self.is_bound and str(self.data.get('session','')).isdigit():
            existing=StageForm.objects.filter(session_id=self.data['session'],stage=self.data.get('stage')).first()
            if existing:self.instance=existing
    class Meta:
        model=StageForm
        fields=['session','stage','form_id','responder_url']
        labels={'form_id':'Google Form editor ID (required for permission sync)','responder_url':'Google Form respondent link'}
    def clean_form_id(self):
        value=self.cleaned_data['form_id'].strip()
        if value and not re.fullmatch(r'[A-Za-z0-9_-]{10,160}',value):
            raise forms.ValidationError('Paste the editor form ID, not a full URL.')
        return value
    def clean_responder_url(self):
        url=self.cleaned_data['responder_url']
        if url:
            parsed=urlparse(url)
            if parsed.scheme!='https' or parsed.hostname!='docs.google.com' or not re.fullmatch(r'/forms/d/(?:e/)?[A-Za-z0-9_-]+/viewform',parsed.path):
                raise forms.ValidationError('Use the full https://docs.google.com/forms/d/.../viewform respondent URL.')
        return url
    def validate_unique(self): pass

def google_client():
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.credentials import Credentials
    filename=os.getenv('OBE_GOOGLE_ACCESS_TOKEN_FILE','')
    if not filename: raise ValueError('Google respondent permissions are not connected. Configure the authorized Google token file; portal assignments remain available.')
    return AuthorizedSession(Credentials.from_authorized_user_file(filename))

def permission_list(client, form_id):
    items=[];token=None
    while True:
        params={'includePermissionsForView':'published','fields':'nextPageToken,permissions(id,type,role,view,emailAddress)','pageSize':100}
        if token: params['pageToken']=token
        response=client.get(f'https://www.googleapis.com/drive/v3/files/{form_id}/permissions',params=params,timeout=20)
        response.raise_for_status();data=response.json();items.extend(data.get('permissions',[]));token=data.get('nextPageToken')
        if not token: return items

def sync_permissions(link):
    if not link.form_id: raise ValueError('Configure the editor Form ID first.')
    desired=set(Assignment.objects.filter(student__session=link.session,stage=link.stage,active=True).values_list('evaluator',flat=True))
    client=google_client()
    try:
        metadata=client.get(f'https://forms.googleapis.com/v1/forms/{link.form_id}',timeout=20)
        metadata.raise_for_status();info=metadata.json()
        if not info.get('publishSettings'):raise ValueError('This legacy Form does not support verified respondent controls.')
        if info.get('responderUri','').split('?')[0]!=link.responder_url.split('?')[0]:
            raise ValueError('Editor Form ID and respondent URL do not identify the same Form.')
        permissions=permission_list(client,link.form_id)
        published=[p for p in permissions if p.get('view')=='published']
        if any(p.get('type')!='user' for p in published):
            raise ValueError('This Form permits public, domain or group respondents. Restrict its respondent general access in Google first; no Google permissions were changed.')
        current={p.get('emailAddress','').lower():p for p in published if p.get('role') in ['reader','publishedReader']}
        # Only respondent permissions are touched. Editor and workbook permissions are never granted.
        for email in sorted(desired-set(current)):
            r=client.post(f'https://www.googleapis.com/drive/v3/files/{link.form_id}/permissions',params={'sendNotificationEmail':'false'},json={'type':'user','role':'reader','view':'published','emailAddress':email},timeout=20)
            r.raise_for_status()
        for email in sorted(set(current)-desired):
            r=client.delete(f"https://www.googleapis.com/drive/v3/files/{link.form_id}/permissions/{current[email]['id']}",timeout=20)
            r.raise_for_status()
        verified=permission_list(client,link.form_id)
        actual={p.get('emailAddress','').lower() for p in verified if p.get('view')=='published' and p.get('type')=='user' and p.get('role') in ['reader','publishedReader']}
        if actual!=desired or any(p.get('view')=='published' and p.get('type')!='user' for p in verified):
            raise ValueError('Google respondent access did not match the approved list. Review permissions before sharing.')
        link.verified_at=timezone.now();link.verification_note='Google respondent allowlist verified; no editor access granted.';link.save()
    finally:client.close()

@login_required
def access(request):
    require(request.user,['coordinator'])
    grant=GrantForm(request.POST if request.POST.get('action')=='grant' else None)
    linkform=LinkForm(request.POST if request.POST.get('action')=='link' else None)
    if request.method=='POST':
        action=request.POST.get('action')
        try:
            if action=='grant' and grant.is_valid():
                d=grant.cleaned_data
                with transaction.atomic():
                    group=ProjectGroup.objects.select_for_update().get(pk=d['group'].pk)
                    if FrozenResult.objects.filter(group=group,active=True).exists():raise ValueError('Reopen frozen results before changing evaluator assignments.')
                    if not group.students.exists():raise ValueError('Import group members first.')
                    for student in group.students.all():
                        Assignment.objects.update_or_create(student=student,stage=d['stage'],evaluator=d['evaluator'],defaults={'active':True,'opens_at':d['opens_at'],'closes_at':d['closes_at']})
                    StageForm.objects.filter(session=group.session,stage=d['stage']).update(verified_at=None)
                    audit(request.user,'evaluator.authorized',group.pk,{'stage':d['stage'],'email':d['evaluator']})
                messages.success(request,'Evaluator assigned to every group member. Use Sync respondents to apply the Google Form allowlist.')
                return redirect('evaluator_access')
            elif action=='revoke':
                with transaction.atomic():
                    assignment=get_object_or_404(Assignment,pk=request.POST.get('assignment'))
                    group=ProjectGroup.objects.select_for_update().get(pk=assignment.student.group_id)
                    if FrozenResult.objects.filter(group=group,active=True).exists():raise ValueError('Reopen frozen results before changing evaluator assignments.')
                    Assignment.objects.filter(student__group=group,stage=assignment.stage,evaluator=assignment.evaluator).update(active=False)
                    StageForm.objects.filter(session=group.session,stage=assignment.stage).update(verified_at=None)
                    audit(request.user,'evaluator.revoked',group.pk,{'stage':assignment.stage,'email':assignment.evaluator})
                messages.success(request,'Portal access revoked. Sync respondents to remove Google respondent access.')
                return redirect('evaluator_access')
            elif action=='link' and linkform.is_valid():
                d=linkform.cleaned_data
                StageForm.objects.update_or_create(session=d['session'],stage=d['stage'],defaults={'form_id':d['form_id'],'responder_url':d['responder_url'],'verified_at':None,'verification_note':''})
                audit(request.user,'form.configured',d['session'].pk,{'stage':d['stage']})
                messages.success(request,'Form saved. Respondent permissions still require verification.')
                return redirect('evaluator_access')
            elif action=='sync':
                link=get_object_or_404(StageForm,pk=request.POST.get('link'))
                link.verified_at=None;link.save(update_fields=['verified_at'])
                sync_permissions(link)
                audit(request.user,'form.respondents_verified',link.pk)
                messages.success(request,'Google respondent permissions synchronized and verified.')
                return redirect('evaluator_access')
        except ValueError as e:messages.error(request,str(e))
        except Exception:messages.error(request,'Google access could not be verified. Check account authorization and Form ownership; never share a form with unverified access.')
    rows=Assignment.objects.select_related('student__group__session').order_by('-student__session_id','student__group_id','stage','evaluator','student__seat')
    unique=[];seen=set()
    for row in rows:
        key=(row.student.group_id,row.stage,row.evaluator)
        if key not in seen:unique.append(row);seen.add(key)
    from .views import context
    return render(request,'evaluations/access.html',context(request,grant_form=grant,link_form=linkform,assignments=unique,links=StageForm.objects.select_related('session').order_by('-session_id','stage')))
