import uuid
from django.conf import settings
from django.db import models
from .rubrics import STAGE_CHOICES
class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=16, choices=[('coordinator', 'FYDP Coordinator'), ('hod', 'Head of Department')])
    mfa_secret = models.TextField(blank=True)
    mfa_counter = models.BigIntegerField(default=-1)
class AcademicSession(models.Model):
    label = models.CharField(max_length=80, unique=True)
    course_code = models.CharField(max_length=40)
    rules_approved = models.BooleanField(default=False)
    rules_approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    rules_approval_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.label
class ProjectGroup(models.Model):
    session = models.ForeignKey(AcademicSession, on_delete=models.PROTECT)
    project_id = models.CharField(max_length=80)
    title = models.CharField(max_length=240)
    attempt = models.PositiveSmallIntegerField(default=1)
    expected_members = models.PositiveSmallIntegerField(default=4)
    version = models.PositiveIntegerField(default=1)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['session', 'project_id', 'attempt'], name='unique_group_attempt')]
    def __str__(self): return self.project_id
class Student(models.Model):
    group = models.ForeignKey(ProjectGroup, related_name='students', on_delete=models.PROTECT)
    session = models.ForeignKey(AcademicSession, on_delete=models.PROTECT)
    seat = models.CharField(max_length=8)
    name = models.CharField(max_length=160)
    class Meta:
        ordering = ['seat']
        constraints = [models.UniqueConstraint(fields=['session', 'seat', 'group'], name='unique_student_attempt')]
class Assignment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.PROTECT)
    stage = models.CharField(max_length=2, choices=STAGE_CHOICES)
    evaluator = models.EmailField()
    opens_at = models.DateTimeField(null=True, blank=True)
    closes_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['student', 'stage', 'evaluator'], name='unique_assigned_evaluation')]
class Evaluation(models.Model):
    assignment = models.ForeignKey(Assignment, related_name='revisions', on_delete=models.PROTECT)
    revision = models.PositiveIntegerField()
    criteria = models.JSONField()
    comments = models.TextField(blank=True)
    source_id = models.CharField(max_length=160)
    content_hash = models.CharField(max_length=64)
    received_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['assignment', 'revision'], name='unique_evaluation_revision')]
class FrozenResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(ProjectGroup, on_delete=models.PROTECT)
    stage = models.CharField(max_length=5)
    version = models.PositiveIntegerField()
    payload = models.JSONField()
    digest = models.CharField(max_length=64)
    active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['group', 'stage', 'version'], name='unique_frozen_version'),
                       models.UniqueConstraint(fields=['group', 'stage'], condition=models.Q(active=True), name='one_active_frozen_result')]
class PendingChange(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.PROTECT)
    payload = models.JSONField()
    digest = models.CharField(max_length=64)
    reason = models.CharField(max_length=200)
    status = models.CharField(max_length=10, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['assignment', 'digest'], name='unique_pending_change')]
class AuditEvent(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    action = models.CharField(max_length=80)
    target = models.CharField(max_length=120)
    detail = models.JSONField(default=dict)
    at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['-at', '-id']
class ImportBatch(models.Model):
    session = models.ForeignKey(AcademicSession, on_delete=models.PROTECT)
    digest = models.CharField(max_length=64)
    summary = models.JSONField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
class TemplateApproval(models.Model):
    stage = models.CharField(max_length=2, unique=True)
    digest = models.CharField(max_length=64)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    note = models.TextField()
    at = models.DateTimeField(auto_now_add=True)
class Report(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    result = models.ForeignKey(FrozenResult, on_delete=models.PROTECT)
    stage = models.CharField(max_length=2)
    template_digest = models.CharField(max_length=64)
    file_digest = models.CharField(max_length=64)
    format = models.CharField(max_length=4)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
class LoginThrottle(models.Model):
    key = models.CharField(max_length=64, unique=True)
    failures = models.PositiveIntegerField(default=0)
    window_start = models.DateTimeField()
class WebhookReceipt(models.Model):
    event_id = models.UUIDField(primary_key=True)
    digest = models.CharField(max_length=64)
    received_at = models.DateTimeField(auto_now_add=True)

class MasterRecord(models.Model):
    student = models.OneToOneField(Student, on_delete=models.PROTECT)
    payload = models.JSONField()
    digest = models.CharField(max_length=64)
    errors = models.JSONField(default=list)
    synced_at = models.DateTimeField(auto_now=True)
