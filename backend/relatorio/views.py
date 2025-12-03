from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import RelatorioForm, ImagemFormSet

def relatorio(request):
    
    if request.method == 'POST':
        form = RelatorioForm(request.POST)
        formset = ImagemFormSet(request.POST, request.FILES)
        
        if form.is_valid() and formset.is_valid():
            relatorio = form.save()
            formset.instance = relatorio
            formset.save()

            messages.success(request, "Relatório enviado com sucesso!")
            return redirect('relatorio')  
            
    else:
        form = RelatorioForm()
        formset = ImagemFormSet()

    return render(request, 'relatorio/index.html', {'form': form, 'formset': formset})
