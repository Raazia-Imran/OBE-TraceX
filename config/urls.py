from django.urls import path
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView
from evaluations import views
urlpatterns = [
 path('intro/', views.welcome, name='welcome'),
 path('about/', views.about, name='about'), path('privacy/', views.privacy, name='privacy'),
 path('account/profile/', views.profile, name='profile'), path('account/avatar/', views.avatar, name='avatar'),
 path('healthz/', views.health, name='health'), path('login/', views.signin, name='login'),
 path('logout/', views.signout, name='logout'), path('', views.entry, name='dashboard'),
 path('groups/<int:pk>/', views.group_detail, name='group'), path('groups/<int:pk>/action/', views.result_action, name='result_action'),
 path('groups/<int:pk>/export/<str:stage>/<str:extension>/', views.export, name='export'),
 path('imports/', views.imports, name='imports'), path('imports/google/', views.sync, name='sync'),
 path('sessions/', views.sessions, name='sessions'), path('sessions/<int:pk>/approve/', views.approve_rules, name='approve_rules'),
 path('corrections/', views.corrections, name='corrections'), path('audit/', views.audit_view, name='audit'),
 path('templates/', views.templates_view, name='templates'),
 path('templates/<str:stage>/sample/<str:extension>/', views.sample_template, name='sample_template'), path('templates/<str:stage>/original/', views.original_template, name='original_template'),
 path('account/password/', PasswordChangeView.as_view(template_name='registration/password_change_form.html', success_url='/account/password/done/'), name='password_change'),
 path('account/password/done/', PasswordChangeDoneView.as_view(template_name='registration/password_change_done.html'), name='password_change_done'),
 path('integrations/n8n/evaluation/', views.webhook, name='webhook'),
]
