from django.shortcuts import render, redirect
from .forms import RelatorioForm, ImagemFormSet

def index(request):
    template_name = 'relatorio/index.html'
    
    if request.method == 'POST':
        form = RelatorioForm(request.POST)
        formset = ImagemFormSet(request.POST, request.FILES)
        
        if form.is_valid() and formset.is_valid():
            relatorio = form.save()
            
            formset.instance = relatorio
            formset.save()
            
            return redirect('relatorio_sucesso')
            
    else:
        form = RelatorioForm()
        formset = ImagemFormSet()

    context = {
        'form': form,
        'formset': formset,
    }
    return render(request, template_name, context)