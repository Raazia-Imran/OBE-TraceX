from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import *
from .services import receive_evaluation
from .access import LinkForm
class AccessTests(TestCase):
    def setUp(self):
        self.user=get_user_model().objects.create_user('c',password='test-password-unrelated')
        Profile.objects.create(user=self.user,role='coordinator')
        self.hod=get_user_model().objects.create_user('h',password='test-password-unrelated')
        Profile.objects.create(user=self.hod,role='hod')
        self.session=AcademicSession.objects.create(label='Test access',course_code='FYDP')
        self.group=ProjectGroup.objects.create(session=self.session,project_id='P1',title='A project',expected_members=1)
        self.student=Student.objects.create(group=self.group,session=self.session,seat='SE-21077',name='A student')
        self.client.force_login(self.user)
    def grant(self,**extra):
        data={'action':'grant','group':self.group.pk,'stage':'D1','evaluator':'Faculty@Example.test'}
        data.update(extra);return self.client.post('/evaluators/',data)
    def test_grant_normalizes_and_assigns(self):
        self.assertEqual(self.grant().status_code,302)
        self.assertEqual(Assignment.objects.get().evaluator,'faculty@example.test')
    def test_invalid_window_creates_nothing(self):
        self.grant(opens_at='2026-11-12T12:00',closes_at='2026-11-11T12:00')
        self.assertEqual(Assignment.objects.count(),0)
    def test_hod_cannot_manage(self):
        self.client.force_login(self.hod)
        self.assertEqual(self.grant().status_code,403)
    def test_anonymous_redirects(self):
        self.client.logout();self.assertEqual(self.client.get('/evaluators/').status_code,302)
    def test_revoked_response_is_blocked(self):
        self.grant();a=Assignment.objects.get()
        self.client.post('/evaluators/',{'action':'revoke','assignment':a.pk})
        with self.assertRaisesMessage(ValueError,'revoked'):
            receive_evaluation({'session':self.session.label,'seat':self.student.seat,'stage':'D1','evaluator':a.evaluator,'source_id':'a','percentages':[75]*4})
        self.assertEqual(Evaluation.objects.count(),0)
    def test_frozen_group_rejects_assignment_change(self):
        FrozenResult.objects.create(group=self.group,stage='D1',version=1,payload={},digest='x',created_by=self.user)
        self.grant();self.assertEqual(Assignment.objects.count(),0)
    def test_google_link_host_validation(self):
        data={'session':self.session.pk,'stage':'D1','form_id':'abcdefghijklmnop','responder_url':'https://evil.example/forms/d/abc/viewform'}
        self.assertFalse(LinkForm(data).is_valid())
    def test_google_credentials_failure_is_not_success(self):
        link=StageForm.objects.create(session=self.session,stage='D1',form_id='abcdefghijklmnop')
        with patch('evaluations.access.google_client',side_effect=ValueError('Not connected')):
            self.client.post('/evaluators/',{'action':'sync','link':link.pk})
        link.refresh_from_db();self.assertIsNone(link.verified_at)
    def test_form_update_invalidates_verification(self):
        from django.utils import timezone
        link=StageForm.objects.create(session=self.session,stage='D1',verified_at=timezone.now())
        self.client.post('/evaluators/',{'action':'link','session':self.session.pk,'stage':'D1','form_id':'abcdefghijklmnop','responder_url':'https://docs.google.com/forms/d/abcdefghijklmnop/viewform'})
        link.refresh_from_db();self.assertIsNone(link.verified_at)
    def test_preview_is_labelled_and_not_official(self):
        from .services import digest
        payload={'stages':{},'reported_stages':dict.fromkeys(['D1','D2','D3','D4','D5','D6'],'0'),'final':'0'}
        MasterRecord.objects.create(student=self.student,payload=payload,digest=digest(payload))
        r=self.client.post(f'/groups/{self.group.pk}/preview/D7/docx/')
        self.assertEqual(r.status_code,200)
        import io
        from docx import Document
        self.assertIn('PREVIEW ONLY',Document(io.BytesIO(r.content)).sections[0].header.paragraphs[0].text)
        self.assertEqual(TemplateApproval.objects.count(),0)
