"""
Question Bank URLs - API Routing
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    QuestionBankViewSet, QuestionBankOptionViewSet,
    ControlQuestionMapViewSet, QuestionApplicabilityRuleViewSet
)

router = DefaultRouter()
router.register(r'questions', QuestionBankViewSet, basename='questionbank')
router.register(r'question-options', QuestionBankOptionViewSet, basename='questionoption')
router.register(r'control-question-maps', ControlQuestionMapViewSet, basename='controlquestionmap')
router.register(r'question-rules', QuestionApplicabilityRuleViewSet, basename='questionrule')

urlpatterns = [
    path('', include(router.urls)),
]