import hashlib
import hmac
import io
import json
import os
import time
import uuid
from decimal import Decimal
from unittest.mock import patch
from cryptography.fernet import Fernet
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import Client, TestCase, override_settings
from django.utils import timezone
from docx import Document
from .models import *
from .services import *
from .rubrics import *
from .reports import export_report, populate, template_path
from .importers import assignments_import, roster_import, workbook_import
from .mfa import cipher, generate_secret, token, verify

class PortalTests(TestCase):
    def setUp(self):
        self.coordinator = get_user_model().objects.create_user('qa-coordinator', password=uuid.uuid4().hex)
        self.hod = get_user_model().objects.create_user('qa-hod', password=uuid.uuid4().hex)
        Profile.objects.create(user=self.coordinator, role='coordinator')
        Profile.objects.create(user=self.hod, role='hod')
        self.session = AcademicSession.objects.create(label='Synthetic QA', course_code='SE-QA', rules_approved=True)
        self.group = ProjectGroup.objects.create(session=self.session, project_id='QA-01', title='Synthetic test project', expected_members=2)
        self.students = [Student.objects.create(session=self.session, group=self.group, seat=f'SE-9900{i+1}', name=f'Sample {i+1}') for i in range(2)]
        for student in self.students:
            for stage in STAGES:
                Assignment.objects.create(student=student, stage=stage, evaluator='reviewer@example.test')
    def payload(self, stage='D1', student=0, percent=100, source='response-1'):
        return {'session': self.session.label, 'stage': stage, 'seat': self.students[student].seat,
                'evaluator': 'reviewer@example.test', 'source_id': source, 'percentages': [percent] * len(RUBRICS[stage]['maxima'])}
    def complete(self, stage):
        for i in range(2): receive_evaluation(self.payload(stage, i))
    def freeze(self, stage):
        self.group.refresh_from_db()
        return freeze_stage(self.group.pk, stage, self.coordinator, self.group.version, 'Coordinator reviewed synthetic responses.')
    def final(self):
        for stage in STAGES: self.complete(stage); self.freeze(stage)
        self.group.refresh_from_db()
        return freeze_final(self.group.pk, self.coordinator, self.group.version, 'HOD approves synthetic test results.')
    def test_weighted_d4_and_maximum(self):
        self.assertEqual(sum(weighted('D4', [50,50,50,50,0])), Decimal('20'))
        self.assertEqual(sum(weighted('D4', [75,75,75,75,0])), Decimal('30'))
        self.assertEqual(sum(sum(weighted(s, [100]*len(r['maxima']))) for s,r in RUBRICS.items()), 200)
    def test_blank_zero_invalid_and_format(self):
        for invalid in ['', None, True, 'NaN', 'Infinity']:
            with self.assertRaises(ValueError): number(invalid)
        self.assertEqual(number(0), 0)
        self.assertEqual(seat_number(' se-99001 '), 'SE-99001')
        self.assertEqual(display('2.4999999999999996'), '2.50')
        with self.assertRaises(ValueError): seat_number('SE99001')
        with self.assertRaises(ValueError): weighted('D4', [50]*5)
    def test_replay_and_correction(self):
        self.assertEqual(receive_evaluation(self.payload()), 'accepted')
        self.assertEqual(receive_evaluation(self.payload()), 'unchanged')
        self.assertEqual(receive_evaluation(self.payload(percent=50)), 'held')
        self.assertEqual(Evaluation.objects.count(), 1)
        change = PendingChange.objects.get()
        resolve_change(change.pk, self.coordinator, True, 'Authorized correction reference.')
        self.assertEqual(Evaluation.objects.count(), 2)
        self.assertEqual(Evaluation.objects.order_by('-id').first().criteria, ['1.5']*4)
    def test_unassigned_rejected(self):
        p=self.payload(); p['evaluator']='intruder@example.test'
        with self.assertRaises(ValueError): receive_evaluation(p)
    def test_incomplete_and_roster_blocks(self):
        with self.assertRaises(ValueError): self.freeze('D1')
        self.complete('D1'); self.group.expected_members=3; self.group.save()
        with self.assertRaises(ValueError): self.freeze('D1')
    def test_policy_required(self):
        self.complete('D1'); self.session.rules_approved=False; self.session.save()
        with self.assertRaises(ValueError): self.freeze('D1')
    def test_stale_review_blocks(self):
        self.complete('D1')
        with self.assertRaises(ValueError): freeze_stage(self.group.pk, 'D1', self.coordinator, 1, 'Test review note long enough.')
    def test_frozen_change_preserves_snapshot(self):
        self.complete('D1'); frozen=self.freeze('D1'); original=frozen.payload
        self.assertEqual(receive_evaluation(self.payload(percent=50)), 'held')
        with self.assertRaises(ValueError): resolve_change(PendingChange.objects.get().pk,self.coordinator,True,'Correction approved after a review.')
        frozen.refresh_from_db(); self.assertEqual(frozen.payload, original)
    def test_role_separation(self):
        self.complete('D1')
        with self.assertRaises(PermissionDenied): freeze_stage(self.group.pk,'D1',self.hod,1,'Review reference note.')
        with self.assertRaises(PermissionDenied): freeze_final(self.group.pk,self.hod,1,'Review reference note.')
    def test_final_requires_all_stages(self):
        with self.assertRaises(ValueError): freeze_final(self.group.pk,self.coordinator,1,'Review reference note.')
    def test_complete_final_and_reopen_history(self):
        final=self.final()
        self.assertEqual(final.payload['students'][0]['total'], '200')
        reopen(self.group.pk,'D1',self.coordinator,'Correction reopening approved by HOD.')
        final.refresh_from_db(); self.assertFalse(final.active)
        self.assertEqual(final.payload['students'][0]['total'], '200')
        self.assertEqual(FrozenResult.objects.count(),7)
    def test_variable_evaluator_average(self):
        Assignment.objects.create(student=self.students[0],stage='D1',evaluator='second@example.test')
        self.complete('D1'); p=self.payload(percent=50);p['evaluator']='second@example.test'
        receive_evaluation(p)
        result=self.freeze('D1')
        self.assertEqual(result.payload['students'][0]['total'],'9.00')
        self.assertEqual(result.payload['students'][0]['evaluators'],2)
    def test_pending_change_blocks_final(self):
        self.final(); reopen(self.group.pk,'FINAL',self.coordinator,'Reopen final for pending review.')
        receive_evaluation(self.payload(percent=50))
        self.group.refresh_from_db()
        with self.assertRaises(ValueError): freeze_final(self.group.pk,self.coordinator,self.group.version,'Review reference note.')
    def test_schedule(self):
        assignment=Assignment.objects.get(student=self.students[0],stage='D1')
        assignment.closes_at=timezone.now()-timezone.timedelta(days=1);assignment.save()
        self.assertEqual(receive_evaluation(self.payload()),'held')
    def test_exports_require_final_and_verified_template(self):
        with self.assertRaises(ValueError): export_report(self.group,'D1','docx',self.coordinator)
        self.final()
        with self.assertRaises(ValueError): export_report(self.group,'D1','docx',self.coordinator)
        TemplateApproval.objects.create(stage='D1',digest=hashlib.sha256(template_path('D1').read_bytes()).hexdigest(),approved_by=self.hod,note='Verified synthetic report against source.')
        content,name=export_report(self.group,'D1','docx',self.coordinator)
        document=Document(io.BytesIO(content))
        self.assertEqual(document.tables[0].rows[2].cells[2].text,'SE-99001')
        self.assertEqual(document.tables[0].rows[3].cells[2].text,'SE-99002')
        self.assertEqual(document.tables[0].rows[2].cells[-1].text,'12.00')
        original=Document(template_path('D1'))
        self.assertEqual(document.tables[0]._tbl.tblPr.xml,original.tables[0]._tbl.tblPr.xml)
        self.assertEqual(document.tables[0]._tbl.tblGrid.xml,original.tables[0]._tbl.tblGrid.xml)
        self.assertEqual(len(document.sections),len(original.sections))
        self.assertEqual(Report.objects.count(),1)
    def test_template_overflow_blocks(self):
        data={'students':[{}]*5}
        with self.assertRaises(ValueError): populate('D7',data)
    def test_authentication_routes_and_csrf(self):
        client=Client(enforce_csrf_checks=True)
        self.assertEqual(client.get('/').status_code,302)
        self.assertEqual(client.post('/login/',{'username':'x','password':'x'}).status_code,403)
        client.force_login(self.coordinator)
        for path in ['/','/sessions/','/imports/','/corrections/','/audit/','/templates/',f'/groups/{self.group.pk}/','/account/password/']:
            response=client.get(path); self.assertEqual(response.status_code,200,path)
            self.assertEqual(response['Cache-Control'],'no-store, private')
        self.assertEqual(client.get('/logout/').status_code,405)
    def test_hod_cannot_import(self):
        self.client.force_login(self.hod)
        self.assertEqual(self.client.get('/imports/').status_code,403)
    def test_login_throttle(self):
        for _ in range(7): self.client.post('/login/',{'username':'missing','password':'bad'})
        self.assertFalse('_auth_user_id' in self.client.session)
        self.assertTrue(LoginThrottle.objects.filter(failures__gte=5).exists())
    def test_password_hash_not_plaintext(self):
        self.assertTrue(self.coordinator.password.startswith('argon2$'))
    def test_webhook_disabled(self):
        with override_settings(N8N_WEBHOOK_SECRET=''):
            self.assertEqual(self.client.post('/integrations/n8n/evaluation/',data='{}',content_type='application/json').status_code,503)
    @override_settings(N8N_WEBHOOK_SECRET='s'*40)
    def test_signed_webhook_replay(self):
        data={'event_id':str(uuid.uuid4()),'issued_at':int(time.time()),'evaluation':self.payload()}
        body=json.dumps(data).encode(); sig=hmac.new(b's'*40,body,hashlib.sha256).hexdigest()
        for status in ['accepted','unchanged']:
            response=self.client.post('/integrations/n8n/evaluation/',data=body,content_type='application/json',HTTP_X_OBE_SIGNATURE=sig)
            self.assertEqual(response.status_code,200);self.assertEqual(response.json()['status'],status)
        self.assertEqual(Evaluation.objects.count(),1)
    @override_settings(N8N_WEBHOOK_SECRET='s'*40)
    def test_bad_and_stale_signatures(self):
        self.assertEqual(self.client.post('/integrations/n8n/evaluation/',data='{}',content_type='application/json').status_code,401)
        body=json.dumps({'event_id':str(uuid.uuid4()),'issued_at':0,'evaluation':self.payload()}).encode()
        sig=hmac.new(b's'*40,body,hashlib.sha256).hexdigest()
        self.assertEqual(self.client.post('/integrations/n8n/evaluation/',data=body,content_type='application/json',HTTP_X_OBE_SIGNATURE=sig).status_code,400)
    def test_roster_import_is_atomic(self):
        session=AcademicSession.objects.create(label='Import QA',course_code='QA')
        content=b'seat,name,project_id,project_title,expected_members,attempt\nSE-99003,Sample Three,P1,Sample project,1,1\ninvalid,Invalid,P2,Other project,1,1\n'
        with self.assertRaises(ValueError): roster_import(content,session,self.coordinator)
        self.assertFalse(ProjectGroup.objects.filter(session=session).exists())
    def test_mfa_replay(self):
        with patch.dict(os.environ,{'OBE_MFA_KEY':Fernet.generate_key().decode()}):
            profile=self.coordinator.profile; secret=generate_secret()
            profile.mfa_secret=cipher().encrypt(secret.encode()).decode();profile.save()
            code=token(secret,int(time.time())//30)
            self.assertTrue(verify(profile,code))
            self.assertFalse(verify(profile,code))
    def test_headers_and_no_public_signup(self):
        response=self.client.get('/login/')
        self.assertIn("frame-ancestors 'none'",response['Content-Security-Policy'])
        self.assertEqual(response['X-Frame-Options'],'DENY')
        self.assertEqual(self.client.get('/signup/').status_code,404)

    def test_raw_import_matches_roster_and_preserves_official_identity(self):
        from .importers import inspect_and_import
        headers=['Timestamp','Email Address','Seat Number / Roll Number','Project ID','Student Name'] + [f'Proposal Evaluation Criteria [{r}. Criterion]' for r in ['IV','II','I','III']]
        tabs={'D1_Proposal':[headers,['2026-01-01','reviewer@example.test',' se-99001 ','misTyped-project','wrong spelling','Excellent (100%)','Basic (50%)','Good (75%)','Excellent (100%)']]}
        summary=inspect_and_import(tabs,self.session,self.coordinator,'synthetic')
        self.assertEqual(summary['accepted'],1)
        self.assertEqual(Evaluation.objects.get().criteria,['2.25','1.5','3','3'])
        self.students[0].refresh_from_db(); self.assertEqual(self.students[0].name,'Sample 1')
    def test_duplicate_raw_evaluator_is_not_counted_twice(self):
        from .importers import inspect_and_import
        headers=['Timestamp','Email Address','Seat Number / Roll Number'] + [f'Proposal Evaluation Criteria [{r}. Criterion]' for r in ['I','II','III','IV']]
        row=['2026-01-01','reviewer@example.test','SE-99001',100,100,100,100]
        summary=inspect_and_import({'D1_Proposal':[headers,row,row]},self.session,self.coordinator,'synthetic')
        self.assertEqual(summary['accepted'],0)
        self.assertEqual(Evaluation.objects.count(),0)
        self.assertTrue(any('Repeated evaluator' in x for x in summary['issues']))
    def test_bad_criterion_labels_are_not_guessed(self):
        from .importers import criterion_columns
        self.assertEqual(criterion_columns('D4',['Semester 2 Progress Performance [I. A]']*5),[])
    def test_sample_download_is_distinct_from_official_export(self):
        self.client.force_login(self.hod)
        response=self.client.post('/templates/D7/sample/docx/')
        self.assertEqual(response.status_code,200)
        self.assertIn('SAMPLE_ONLY_D7.docx',response['Content-Disposition'])
        self.assertEqual(Report.objects.count(),0)
        self.assertContains(self.client.get('/templates/'),'Synthetic sample Word')
    def test_demo_command_keeps_policy_unapproved(self):
        from django.core.management import call_command
        call_command('seed_demo',coordinator=self.coordinator.username,confirm_synthetic=True,stdout=io.StringIO())
        demo=AcademicSession.objects.get(label__startswith='DEMO ONLY')
        self.assertFalse(demo.rules_approved)
        self.assertEqual(Student.objects.filter(session=demo).count(),7)
        call_command('seed_demo',coordinator=self.coordinator.username,confirm_synthetic=True,stdout=io.StringIO())
        self.assertEqual(Student.objects.filter(session=demo).count(),7)
    def test_n8n_live_files_are_not_part_of_source_repository(self):
        from pathlib import Path
        self.assertFalse(list(Path(settings.BASE_DIR).glob('Workflow*.json')))
    def test_reopening_during_document_generation_blocks_export(self):
        self.final()
        TemplateApproval.objects.create(stage='D1',digest=hashlib.sha256(template_path('D1').read_bytes()).hexdigest(),approved_by=self.hod,note='Synthetic template verification reference.')
        def render_and_reopen(stage,payload):
            content=populate(stage,payload)
            reopen(self.group.pk,'D1',self.coordinator,'HOD reopened during synthetic export test.')
            return content
        with patch('evaluations.reports.populate',side_effect=render_and_reopen):
            with self.assertRaises(ValueError): export_report(self.group,'D1','docx',self.coordinator)
        self.assertEqual(Report.objects.count(),0)

    def test_master_import_preserves_existing_totals_and_needs_no_evaluator_assignment(self):
        from .master_sync import import_master,MASTER_TAB,SCORE_HEADERS
        Assignment.objects.all().delete()
        tabs={MASTER_TAB:[['Seat Number / Roll Number',*SCORE_HEADERS,'TOTAL (200)'],['SE-99001',10.5,20,42.6,48,32,40,193],['SE-99002',10.5,20,42.6,48,32,40,193]]}
        from .master_sync import AVERAGED
        for stage,name in AVERAGED.items():
            vals={'D1':[2.5,2.5,2.75,2.75],'D3':[9.6,10.8,11.4,10.8],'D5':[4]*8,'D6':[8]*5}[stage]
            tabs[name]=[['Seat Number',*[f'Avg {i}' for i in range(len(vals))]],['SE-99001',*vals],['SE-99002',*vals]]
        for stage in ['D2','D4']:
            prefix='Proposal Evaluation Criteria' if stage=='D2' else 'Semester 2 Progress Performance'
            cols=[f'{prefix} [{r}. Criterion]' for r in ['I','II','III','IV']]
            if stage=='D4':cols+=['V. Timely Report Submission (PLO-11)']
            tabs['D2_S1_Progress' if stage=='D2' else 'D4_S2_Progress']=[['Seat Number / Roll Number',*cols],['SE-99001',*['Excellent (100%)']*len(cols)],['SE-99002',*['Excellent (100%)']*len(cols)]]
        result=import_master(tabs,self.session,self.coordinator,'source-file-hash')
        self.assertEqual(result['issues'],[])
        for stage in STAGES:self.freeze(stage)
        self.group.refresh_from_db();final=freeze_final(self.group.pk,self.coordinator,self.group.version,'Approve existing source master totals.')
        self.assertEqual(final.payload['students'][0]['total'],'193')
        self.assertEqual(Evaluation.objects.count(),0)
        self.assertEqual(final.payload['students'][0]['stages'][2],'42.6')
    def test_master_discrepancies_are_flagged_not_repaired(self):
        from .master_sync import import_master,MASTER_TAB,SCORE_HEADERS
        tabs={MASTER_TAB:[['Seat Number / Roll Number',*SCORE_HEADERS,'TOTAL (200)'],['SE-99001',9,20,48,19.2,32,40,168.2]]}
        result=import_master(tabs,self.session,self.coordinator,'bad-source')
        self.assertTrue(result['issues'])
        record=MasterRecord.objects.get(student=self.students[0])
        self.assertEqual(record.payload['reported_stages']['D4'],'19.2')
        with self.assertRaises(ValueError):self.freeze('D4')

    def test_hod_is_read_download_only(self):
        self.client.force_login(self.hod)
        response=self.client.post(f'/sessions/{self.session.pk}/approve/',{'note':'Unauthorized policy change attempt','confirm':'yes'})
        self.assertEqual(response.status_code,403)
        self.assertEqual(self.client.post('/templates/',{'stage':'D1'}).status_code,403)
        self.assertEqual(self.client.get('/templates/').status_code,200)
        with self.assertRaises(PermissionDenied):reopen(self.group.pk,'D1',self.hod,'An unauthorized reopening attempt.')

class GoogleBridgeTests(TestCase):
    def test_reader_extracts_only_successful_google_node(self):
        from tools.refresh_n8n_master import extract_result
        payload={'spreadsheetId':'known','valueRanges':[]}
        result={'data':{'resultData':{'runData':{'Read Master':[{'data':{'main':[[{'json':payload}]]}}]}}}}
        self.assertEqual(extract_result('Startup log\n'+json.dumps(result)),payload)
        with self.assertRaises(ValueError): extract_result('Startup only')
        with self.assertRaises(ValueError): extract_result(json.dumps({'data':{'resultData':{'error':{'message':'private'}}}}))

    def test_google_ranges_must_be_complete_and_in_expected_order(self):
        from .google_sync import validated_tabs
        from .master_sync import READ_TABS
        result=[{'range':f"'{name}'!A1:Z9999",'values':[]} for name in READ_TABS]
        self.assertEqual(list(validated_tabs(result)),list(READ_TABS))
        with self.assertRaises(ValueError): validated_tabs(result[:-1])
        with self.assertRaises(ValueError): validated_tabs(list(reversed(result)))

    @override_settings(OBE_N8N_BRIDGE='reader.py',OBE_MASTER_SNAPSHOT='snapshot.json',GOOGLE_WORKBOOK_ID='expected')
    def test_bridge_rejects_wrong_workbook_without_importing(self):
        from .google_sync import sync_google
        with patch('subprocess.run'),patch('pathlib.Path.read_text',return_value=json.dumps({'spreadsheetId':'wrong','valueRanges':[]})),patch('evaluations.google_sync.import_master') as importer:
            with self.assertRaises(ValueError): sync_google(None,None)
            importer.assert_not_called()

    @override_settings(OBE_N8N_BRIDGE='reader.py',OBE_MASTER_SNAPSHOT='snapshot.json',GOOGLE_WORKBOOK_ID='expected')
    def test_failed_refresh_never_imports_an_old_snapshot(self):
        import subprocess
        from .google_sync import sync_google
        with patch('subprocess.run',side_effect=subprocess.CalledProcessError(1,'reader')),patch('pathlib.Path.read_text') as read:
            with self.assertRaises(ValueError):sync_google(None,None)
            read.assert_not_called()

    def test_formula_only_tail_is_trimmed_but_boundary_student_is_rejected(self):
        from .google_sync import validated_tabs
        from .master_sync import READ_TABS
        result=[{'range':f"'{name}'!A1:Z10000",'values':[['Seat Number','Total'],['SE21077',10]]+[['',0]]*9998} for name in READ_TABS]
        self.assertTrue(all(len(rows)==2 for rows in validated_tabs(result).values()))
        result[0]['values'][-1]=['SE21078',20]
        with self.assertRaises(ValueError):validated_tabs(result)

class ProfileExperienceTests(TestCase):
    def setUp(self):
        self.user=get_user_model().objects.create_user('profile-coordinator',password='Private-test-password-2026')
        self.hod=get_user_model().objects.create_user('profile-hod',password='Private-test-password-2026')
        for user,role in [(self.user,'coordinator'),(self.hod,'hod')]:Profile.objects.create(user=user,role=role)

    def test_intro_and_privacy_are_public_without_forcing_a_view(self):
        for url in ['/about/','/privacy/','/login/']:
            response=self.client.get(url)
            self.assertEqual(response.status_code,200)
        response=self.client.get('/about/')
        self.assertContains(response,'Play the story')
        self.assertContains(response,'Skip to sign in')
        self.assertNotContains(response,'<iframe')

    def test_both_roles_update_only_their_own_profile_and_keep_authorization(self):
        for user in [self.user,self.hod]:
            self.client.force_login(user)
            response=self.client.post('/account/profile/',{'first_name':'Updated','last_name':'Name','email':'','role':'coordinator','username':'intruder','is_superuser':'true','user_id':self.user.pk})
            self.assertRedirects(response,'/account/profile/')
            user.refresh_from_db()
            self.assertEqual(user.first_name,'Updated')
            self.assertFalse(user.is_superuser)
        self.hod.refresh_from_db()
        self.assertEqual(self.hod.username,'profile-hod')
        self.assertEqual(self.hod.profile.role,'hod')
        self.assertEqual(self.client.get('/imports/').status_code,403)

    def test_email_requires_current_password_and_changes_are_audited(self):
        self.client.force_login(self.user)
        self.client.post('/account/profile/',{'email':'new@example.test'})
        self.user.refresh_from_db();self.assertEqual(self.user.email,'')
        self.client.post('/account/profile/',{'first_name':'A','email':'new@example.test','current_password':'Private-test-password-2026'})
        self.user.refresh_from_db();self.assertEqual(self.user.email,'new@example.test')
        event=AuditEvent.objects.get(action='account.profile_updated')
        self.assertNotIn('new@example.test',str(event.detail if hasattr(event,'detail') else event.metadata))

    def test_photo_is_rasterized_and_available_only_after_sign_in(self):
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        buffer=io.BytesIO();Image.new('RGB',(320,200),'red').save(buffer,format='PNG')
        self.client.force_login(self.hod)
        response=self.client.post('/account/profile/',{'photo':SimpleUploadedFile('photo.png',buffer.getvalue()+b'<script>bad()</script>',content_type='image/png')})
        self.assertRedirects(response,'/account/profile/')
        picture=self.client.get('/account/avatar/')
        self.assertEqual(picture['Content-Type'],'image/jpeg')
        self.assertEqual(Image.open(io.BytesIO(picture.content)).size,(256,256))
        self.assertNotIn(b'<script>',picture.content)
        self.client.logout();self.assertEqual(self.client.get('/account/avatar/').status_code,302)
        self.client.force_login(self.user);self.assertEqual(self.client.get('/account/avatar/').status_code,404)
        self.client.force_login(self.hod);self.client.post('/account/profile/',{'remove_photo':'on'})
        self.assertEqual(self.client.get('/account/avatar/').status_code,404)

    def test_fake_or_oversized_photos_are_rejected_and_csrf_remains_required(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.client.force_login(self.user)
        for content in [b'<svg onload="alert(1)"/>',b'0'*(2*1024*1024+1)]:
            self.client.post('/account/profile/',{'photo':SimpleUploadedFile('photo.png',content,content_type='image/png')})
            self.user.profile.refresh_from_db();self.assertFalse(self.user.profile.avatar)
        protected=Client(enforce_csrf_checks=True);protected.force_login(self.user)
        self.assertEqual(protected.post('/account/profile/',{'first_name':'Forged'}).status_code,403)

class OpeningSequenceTests(TestCase):
    def test_anonymous_entry_starts_with_name_then_links_to_existing_story_and_login(self):
        self.assertRedirects(self.client.get('/'),'/intro/')
        opening=self.client.get('/intro/')
        self.assertContains(opening,'written-brand')
        self.assertContains(opening,'data-opening-next href="/about/"')
        self.assertContains(opening,'Skip to sign in')
        story=self.client.get('/about/')
        self.assertContains(story,'One journey.')
        self.assertContains(story,'Play the story')
        self.assertContains(story,'Continue to sign in')
        self.assertEqual(self.client.get('/login/').status_code,200)
