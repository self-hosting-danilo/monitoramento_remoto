from django.contrib import admin
from .models import Cliente, Relatorio, Imagem

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nome']
    search_fields = ['nome']
    list_filter = ['nome']
    
    fieldsets = [
        (
            None,
            {'fields': ('nome',)}
        )
    ]


class ImagensInline(admin.TabularInline):
    model = Imagem
    extra = 1  # quantidade de linhas extras vazias


@admin.register(Relatorio)
class RelatorioAdmin(admin.ModelAdmin):
    list_display = ['hospital', 'observacao', 'criado_em', 'usuario']
    search_fields = ['hospital']
    list_filter = ['hospital']
    inlines = [ImagensInline]

    fieldsets = [
        (
            None,
            {'fields': ('hospital', 'observacao')}
        )
    ]