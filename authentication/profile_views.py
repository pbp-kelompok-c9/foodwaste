from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render, resolve_url
from django.views.decorators.http import require_http_methods, require_POST, require_safe

from .forms import DeleteAccountForm, ProfileForm
from .models import Profile
from .views import wants_json

PAGE_SIZE = 12


def _own_profile(user):
    # Profil dibuat oleh signal; get_or_create menjaga akun yang terlewat.
    return Profile.objects.get_or_create(user=user)[0]


def _directory(request):
    query = request.GET.get('q', '').strip()[:100]
    city = request.GET.get('kota', '').strip()[:60]
    profiles = Profile.objects.select_related('user').filter(user__is_active=True).search(query, city)
    page = Paginator(profiles, PAGE_SIZE).get_page(request.GET.get('page'))
    return page, query, city


def _public_profile(username):
    return get_object_or_404(
        Profile.objects.select_related('user'), user__username=username, user__is_active=True
    )


# ------------------------------------------------------------ profil sendiri
@login_required
@require_safe
def profile_detail(request):
    profile = _own_profile(request.user)
    return render(request, 'authentication/profile.html', {
        'profile': profile,
        'form': ProfileForm(instance=profile),
    })


@login_required
@require_safe
def profile_json(request):
    return JsonResponse({'profile': _own_profile(request.user).to_dict(include_contact=True)})


@login_required
@require_POST
def profile_update(request):
    profile = _own_profile(request.user)
    form = ProfileForm(request.POST, instance=profile)
    if form.is_valid():
        form.save()
        if wants_json(request):
            return JsonResponse({
                'message': 'Profil berhasil diperbarui.',
                'profile': profile.to_dict(include_contact=True),
            })
        messages.success(request, 'Profil berhasil diperbarui.')
        return redirect('authentication:profile')
    if wants_json(request):
        return JsonResponse({'errors': form.errors.get_json_data()}, status=400)
    profile.refresh_from_db()
    return render(request, 'authentication/profile.html', {'profile': profile, 'form': form}, status=400)


@login_required
@require_http_methods(['GET', 'POST'])
def profile_delete(request):
    form = DeleteAccountForm(request.user, request.POST if request.method == 'POST' else None)
    if request.method == 'POST':
        if form.is_valid():
            try:
                with transaction.atomic():
                    request.user.delete()
            except ProtectedError:
                form.add_error(None, 'Akun tidak bisa dihapus karena masih memiliki acara. '
                                     'Hapus acaramu terlebih dahulu.')
            else:
                logout(request)
                destination = resolve_url(settings.LOGOUT_REDIRECT_URL)
                if wants_json(request):
                    return JsonResponse({'message': 'Akun berhasil dihapus.', 'redirect': destination})
                messages.success(request, 'Akun berhasil dihapus.')
                return redirect(destination)
        if wants_json(request):
            return JsonResponse({'errors': form.errors.get_json_data()}, status=400)
    return render(request, 'authentication/profile_confirm_delete.html', {'form': form})


# ------------------------------------------------------- direktori pengguna
@require_safe
def user_list(request):
    page, query, city = _directory(request)
    return render(request, 'authentication/user_list.html', {
        'page_obj': page,
        'q': query,
        'kota': city,
        'cities': Profile.objects.filter(user__is_active=True).cities(),
    })


@require_safe
def user_list_json(request):
    page, _, _ = _directory(request)
    show_contact = request.user.is_authenticated
    return JsonResponse({
        'results': [profile.to_dict(include_contact=show_contact) for profile in page.object_list],
        'page': page.number,
        'num_pages': page.paginator.num_pages,
        'count': page.paginator.count,
    })


@require_safe
def user_detail(request, username):
    profile = _public_profile(username)
    return render(request, 'authentication/user_detail.html', {
        'profile': profile,
        'is_owner': profile.user_id == request.user.pk,
    })


@require_safe
def user_detail_json(request, username):
    profile = _public_profile(username)
    return JsonResponse({'profile': profile.to_dict(include_contact=request.user.is_authenticated)})
