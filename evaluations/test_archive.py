import base64,hashlib,hmac,json,time
from unittest.mock import patch
from django.test import TestCase,override_settings
from django.core.management import call_command,CommandError
from django.contrib.auth import get_user_model
from .models import *
from .archive import save_document
class ArchiveTests(TestCase):
 def setUp(self):
  self.user=get_user_model().objects.create_user('coordinator')
  Profile.objects.create(user=self.user,role='coordinator')
  self.session=AcademicSession.objects.create(label='Live test',course_code='FYDP')
  self.group=ProjectGroup.objects.create(session=self.session,project_id='P1',title='Title',expected_members=1)
  self.student=Student.objects.create(group=self.group,session=self.session,seat='SE-21077',name='Student')
  self.client.force_login(self.user)
 def envelope(self,**kw):
  d={'issued_at':int(time.time()),'event_id':'execution:1','report':{'session':self.session.label,'seat':self.student.seat,'stage':'D1','filename':'report.html','extension':'html','content_base64':base64.b64encode(b'<h1>Exact n8n report</h1>').decode()}}
  d.update(kw);return json.dumps(d).encode()
 def send(self,body):
  return self.client.post('/integrations/n8n/report/',body,content_type='application/json',HTTP_X_OBE_SIGNATURE=hmac.new(b'x'*40,body,hashlib.sha256).hexdigest())
 @override_settings(N8N_WEBHOOK_SECRET='x'*40)
 def test_signed_report_archives_exact_bytes_and_replay_is_idempotent(self):
  b=self.envelope();self.assertEqual(self.send(b).json()['status'],'saved')
  self.assertEqual(self.send(b).json()['status'],'unchanged')
  self.assertEqual(StoredDocument.objects.count(),1)
  self.assertEqual(bytes(StoredDocument.objects.get().content),b'<h1>Exact n8n report</h1>')
 @override_settings(N8N_WEBHOOK_SECRET='x'*40)
 def test_invalid_signature_rejected(self):
  self.assertEqual(self.client.post('/integrations/n8n/report/',self.envelope(),content_type='application/json').status_code,401)
 @override_settings(N8N_WEBHOOK_SECRET='x'*40)
 def test_expired_envelope_rejected(self):
  self.assertEqual(self.send(self.envelope(issued_at=1)).status_code,400)
 @override_settings(N8N_WEBHOOK_SECRET='x'*40)
 def test_unknown_student_rejected(self):
  b=json.loads(self.envelope());b['report']['seat']='SE-99999'
  self.assertEqual(self.send(json.dumps(b).encode()).status_code,400)
 def test_report_download_is_attachment_and_requires_auth(self):
  doc,_=save_document(self.group,'D1','preview','report.html',b'<script>alert(1)</script>','html','local:1',self.student)
  response=self.client.get(f'/documents/{doc.pk}/download/')
  self.assertTrue(response['Content-Disposition'].startswith('attachment;'))
  self.client.logout();self.assertEqual(self.client.get(f'/documents/{doc.pk}/download/').status_code,302)
 def test_tampered_document_blocked(self):
  doc,_=save_document(self.group,'D1','preview','r.html',b'original','html','local:1')
  StoredDocument.objects.filter(pk=doc.pk).update(content=b'changed')
  self.assertEqual(self.client.get(f'/documents/{doc.pk}/download/').status_code,409)
 def test_identity_collision_rejected(self):
  save_document(self.group,'D1','preview','r.html',b'original','html','local:1')
  with self.assertRaises(ValueError):save_document(self.group,'D1','preview','r.html',b'changed','html','local:1')
 def test_worker_preserves_records_on_failure(self):
  with patch('evaluations.management.commands.watch_master.sync_google',side_effect=ValueError('offline')):
   call_command('watch_master',session=self.session.pk,coordinator='coordinator',once=True)
  state=SyncState.objects.get();self.assertIsNone(state.succeeded_at);self.assertTrue(state.error)
 def test_worker_records_success(self):
  with patch('evaluations.management.commands.watch_master.sync_google',return_value={'accepted':1,'issues':[]}):
   call_command('watch_master',session=self.session.pk,coordinator='coordinator',once=True)
  self.assertIsNotNone(SyncState.objects.get().succeeded_at)
 def test_worker_refuses_rehearsal_session(self):
  self.session.course_code='REHEARSAL';self.session.save()
  with self.assertRaises(CommandError):call_command('watch_master',session=self.session.pk,coordinator='coordinator',once=True)
