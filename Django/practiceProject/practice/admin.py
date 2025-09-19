from django.contrib import admin
from .models import PracticeVarity, PracticeReview, School, Certificate

# Register your models here.
class PracticeReviewInline(admin.TabularInline):
  model = PracticeReview
  extra = 2

class PracticeVarietyAdmin(admin.ModelAdmin):
  list_display = ('name', 'type', 'date_added')
  inlines = [PracticeReviewInline]

class SchoolAdmin(admin.ModelAdmin):
  list_display = ('name', 'location')
  filter_horizontal = ('practice_varieties',)

class CertificateAdmin(admin.ModelAdmin):
  list_display = ('practice', 'certificate_number', 'issued_date', 'valid_until')

admin.site.register(PracticeVarity, PracticeVarietyAdmin)
admin.site.register(School, SchoolAdmin)
admin.site.register(Certificate, CertificateAdmin)