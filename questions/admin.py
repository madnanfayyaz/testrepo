from django.contrib import admin
from .models import Question, QuestionOption, ControlQuestionMap

admin.site.register(Question)
admin.site.register(QuestionOption)
admin.site.register(ControlQuestionMap)