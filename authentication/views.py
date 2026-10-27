from django.contrib.auth.views import LoginView
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .forms import RegistrationForm


def wants_json(request):
    """Klien AJAX meminta JSON lewat header Accept; tanpa itu respons tetap HTML."""
    return 'application/json' in request.headers.get('Accept', '')


@require_http_methods(['GET', 'POST'])
def register(request):
    if request.user.is_authenticated:
        return redirect('discovery_dashboard:discovery')
    form = RegistrationForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        # Only explicitly allowed fields are saved; role/admin flags are not inputs.
        user = form.save()
        if wants_json(request):
            return JsonResponse({'message': 'Akun berhasil dibuat.', 'username': user.username}, status=201)
        return redirect('authentication:registration_complete')
    if request.method == 'POST' and wants_json(request):
        return JsonResponse({'errors': form.errors.get_json_data()}, status=400)
    return render(request, 'authentication/register.html', {'form': form})


class UserLoginView(LoginView):
    template_name = 'authentication/login.html'
    redirect_authenticated_user = True
