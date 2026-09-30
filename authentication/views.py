from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .forms import RegistrationForm


@require_http_methods(['GET', 'POST'])
def register(request):
    if request.user.is_authenticated:
        return redirect('main_landing')
    form = RegistrationForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        # Only explicitly allowed fields are saved; role/admin flags are not inputs.
        form.save()
        return redirect('authentication:registration_complete')
    return render(request, 'authentication/register.html', {'form': form})


class UserLoginView(LoginView):
    template_name = 'authentication/login.html'
    redirect_authenticated_user = True
