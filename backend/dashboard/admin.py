from django.contrib import admin
from .models import AirCentral, OxygenCentral, Hospital, ChatTelegram




@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ['nome']
    search_fields = ['nome']
    list_filter = ['nome']

    fieldsets = [
        (
            None, 
            {'fields': ('nome',)}
        ),
    ]

@admin.register(AirCentral)
class AirCentralAdmin(admin.ModelAdmin):
    list_display = ['hospital']
    search_fields = ['hospital']
    list_filter = ['hospital']

    fieldsets = [
        (
            None, 
            {'fields': ('hospital',)}
        ),
    ]

@admin.register(OxygenCentral)
class OxygenCentralAdmin(admin.ModelAdmin):
    list_display = ['hospital']
    search_fields = ['hospital']
    list_filter = ['hospital']

    fieldsets = [
        (
            None, 
            {'fields': ('hospital',)}
        ),
    ]

@admin.register(ChatTelegram)
class ChatTelegramAdmin(admin.ModelAdmin):
    list_display = ['hospital', 'chat_id']
    search_fields = ['hospital']
    list_filter = ['hospital']

    fieldsets = [
        (
            None,
            {'fields': ('hospital', 'chat_id',)}
        ),
    ]