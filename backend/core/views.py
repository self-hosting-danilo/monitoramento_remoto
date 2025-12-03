from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout

def custom_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        
        try: 
            hospital = str(request.user.hospital)
        except:
            pass
        
        if user is not None:
            login(request, user)
            if hospital == 'Tecnico':
                return redirect('relatorio')
            else:
                return redirect('admin_dashboard')
        else:
            return render(request, 'core/login.html', {'error': 'Usuário ou senha inválidos'})

    return render(request, 'core/login.html')

def custom_logout(request):
    logout(request)
    return redirect('login')