from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, AirCentral, OxygenCentral, Hospital, ChatTelegram

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Informações Adicionais', {'fields': ('hospital',)}),
    ) #type: ignore
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'hospital'),
        }),
    )
admin.site.register(CustomUser, CustomUserAdmin)


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