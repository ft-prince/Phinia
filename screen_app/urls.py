from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('station/<int:station_id>/media/', views.get_station_media, name='station_media'),
    path('station/<int:station_id>/slider/', views.station_media_slider, name='station_media_slider'),
    # ----------------------------------------------------------------
        path('', views.InspectionListView.as_view(), name='inspection_list'),
    path('inspection/new/', views.inspection_create, name='inspection_create'),
    path('inspection/<int:pk>/', views.InspectionDetailView.as_view(), name='inspection_detail'),
    path('inspection/<int:pk>/edit/', views.inspection_edit, name='inspection_edit'),
    path('inspection/<int:pk>/delete/', views.inspection_delete, name='inspection_delete'),
    path('inspection/<int:inspection_pk>/concern/new/', views.concern_report_create, name='concern_report_create'),
    path('inspection/concern_report/<int:pk>/', views.ConcernReportDetailView.as_view(), name='concern_report_detail'),
    # API endpoints for tool IDs and part numbers
    path('get-tool-ids/', views.get_tool_ids, name='get_tool_ids'),
    path('get-part-numbers/', views.get_part_numbers, name='get_part_numbers'),


]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
