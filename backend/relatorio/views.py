from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RelatorioForm, ImagemFormSet

@login_required
def relatorio(request):
    template_name = 'relatorio/index.html'
    
    if request.method == 'POST':
        form = RelatorioForm(request.POST)
        formset = ImagemFormSet(request.POST, request.FILES)
        
        if form.is_valid() and formset.is_valid():
            relatorio = form.save(commit=False)
            relatorio.usuario = request.user
            relatorio.save()

            formset.instance = relatorio
            formset.save()
            
            messages.success(request, "Relatório enviado com sucesso!")
            return redirect('relatorio') 
    else:
        form = RelatorioForm()
        formset = ImagemFormSet()

    return render(request, template_name, {
        'form': form,
        'formset': formset,
    })
