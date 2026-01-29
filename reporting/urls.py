"""Reporting URLs"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DashboardViewSet, DashboardWidgetViewSet,
    ReportViewSet, ReportScheduleViewSet, MetricsViewSet
)

router = DefaultRouter()
router.register(r'dashboards', DashboardViewSet, basename='dashboard')
router.register(r'dashboard-widgets', DashboardWidgetViewSet, basename='widget')
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'report-schedules', ReportScheduleViewSet, basename='schedule')
router.register(r'metrics', MetricsViewSet, basename='metrics')

urlpatterns = [
    path('', include(router.urls)),
]