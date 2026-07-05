from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.health_check, name="health_check"),
    path("transform/", views.transform_text, name="transform_text"),
    path("resume/export-pdf/", views.export_resume_pdf, name="export_resume_pdf"),
]
