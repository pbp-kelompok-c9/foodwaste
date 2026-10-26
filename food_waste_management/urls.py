from django.urls import path

from food_waste_management import views

app_name = 'food_waste_management'

urlpatterns = [
    path('', views.show_management, name='show_management'),
    path('antrean/', views.verification_queue, name='queue'),
    path('penanganan/', views.handling_list, name='handling'),
    path('laporan/<uuid:report_id>/', views.review_detail, name='detail'),
    path('laporan/<uuid:report_id>/terima/', views.accept_report, name='accept'),
    path('laporan/<uuid:report_id>/tolak/', views.reject_report, name='reject'),
    path('laporan/<uuid:report_id>/status/', views.update_handling, name='update_handling'),
    path('laporan/<uuid:report_id>/tindak-lanjut/', views.set_follow_up, name='follow_up'),
]