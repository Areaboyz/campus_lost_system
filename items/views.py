from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, redirect_to_login
from django.contrib.auth import get_user_model
from django.db.models import Case, IntegerField, Q, Value, When
from django.utils.http import url_has_allowed_host_and_scheme

from .models import LostFoundItem, Category
from .forms import CampusAuthenticationForm, LostFoundItemForm, ProfileSettingsForm, StudentRegistrationForm


def home(request):
    active_items = LostFoundItem.objects.filter(is_resolved=False)

    lost_count = active_items.filter(status='LOST').count()
    found_count = active_items.filter(status='FOUND').count()
    total_count = active_items.count()

    if request.user.is_authenticated:
        my_reports_count = LostFoundItem.objects.filter(user=request.user).count()
    else:
        my_reports_count = 0

    recent_items = active_items.order_by('-date_reported')
    if request.user.is_authenticated:
        profile = getattr(request.user, 'student_profile', None)
        category_terms = {
            'electronics': ('electronic', 'laptop'),
            'IDs': ('id', 'card'),
            'books': ('book', 'course'),
            'keys': ('key', 'wallet'),
            'clothing': ('cloth', 'accessory'),
        }
        terms = category_terms.get(getattr(profile, 'search_category', ''), ())
        if terms:
            preferred_category = Q()
            for term in terms:
                preferred_category |= Q(category__name__icontains=term)
            recent_items = recent_items.annotate(
                preference_order=Case(
                    When(preferred_category, then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField(),
                )
            ).order_by('preference_order', '-date_reported')
    recent_items = recent_items[:5]

    context = {
        'lost_count': lost_count,
        'found_count': found_count,
        'total_count': total_count,
        'my_reports_count': my_reports_count,
        'recent_items': recent_items,
    }

    return render(request, 'items/home.html', context)


class CampusLoginView(LoginView):
    template_name = 'registration/login.html'
    form_class = CampusAuthenticationForm

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.session.set_expiry(
            60 * 60 * 24 * 14 if self.request.POST.get('remember_me') else 0
        )
        return response


@login_required
def dashboard(request):
    """Send each signed-in account to its role's dashboard."""
    if request.user.is_superuser:
        return redirect('administration_dashboard')
    if request.user.is_staff:
        return redirect('admin_dashboard')
    return redirect('student_dashboard')


@login_required
def profile_settings(request):
    if request.method == 'POST':
        form = ProfileSettingsForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile details have been updated.')
            section = request.POST.get('active_section', 'personal-details')
            if section not in {'personal-details', 'emergency-contact'}:
                section = 'personal-details'
            return redirect(f'{reverse("profile_settings")}#{section}')
    else:
        form = ProfileSettingsForm(user=request.user)
    return render(request, 'items/profile_settings.html', {'form': form})


@login_required
def student_dashboard(request):
    if request.user.is_staff:
        return redirect('dashboard')
    reports = LostFoundItem.objects.filter(user=request.user)
    context = {
        'reports': reports[:6],
        'report_count': reports.count(),
        'open_count': reports.filter(is_resolved=False).count(),
        'resolved_count': reports.filter(is_resolved=True).count(),
        'active_items': LostFoundItem.objects.filter(is_resolved=False).count(),
    }
    return render(request, 'items/student_dashboard.html', context)


@login_required
@user_passes_test(lambda user: user.is_staff, login_url='home')
def admin_dashboard(request):
    if request.user.is_superuser:
        return redirect('administration_dashboard')
    active_items = LostFoundItem.objects.filter(is_resolved=False)
    context = {
        'active_count': active_items.count(),
        'lost_count': active_items.filter(status='LOST').count(),
        'found_count': active_items.filter(status='FOUND').count(),
        'resolved_count': LostFoundItem.objects.filter(is_resolved=True).count(),
        'recent_items': LostFoundItem.objects.select_related('user', 'category')[:8],
    }
    return render(request, 'items/admin_dashboard.html', context)


@login_required
@user_passes_test(lambda user: user.is_superuser, login_url='home')
def administration_dashboard(request):
    active_items = LostFoundItem.objects.filter(is_resolved=False)
    context = {
        'user_count': get_user_model().objects.count(),
        'staff_count': get_user_model().objects.filter(is_staff=True).count(),
        'item_count': LostFoundItem.objects.count(),
        'active_count': active_items.count(),
        'category_count': Category.objects.count(),
        'recent_items': LostFoundItem.objects.select_related('user', 'category')[:8],
    }
    return render(request, 'items/administration_dashboard.html', context)


@login_required
@user_passes_test(lambda user: user.is_staff, login_url='home')
def toggle_item_resolution(request, pk):
    if request.method == 'POST':
        item = get_object_or_404(LostFoundItem, pk=pk)
        item.is_resolved = not item.is_resolved
        item.save(update_fields=['is_resolved'])
        state = 'resolved' if item.is_resolved else 'active'
        messages.success(request, f'“{item.title}” is now marked {state}.')
    return redirect('admin_dashboard')


def item_list(request):
    status_filter = request.GET.get('status', '')
    category_filter = request.GET.get('category', '')
    query = request.GET.get('q', '')

    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())

    items = LostFoundItem.objects.filter(
        is_resolved=False
    ).order_by('-date_reported')

    if status_filter:
        items = items.filter(status=status_filter)

    if category_filter:
        items = items.filter(category_id=category_filter)

    if query:
        items = items.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    categories = Category.objects.all()

    context = {
        'items': items,
        'categories': categories,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'query': query,
    }

    return render(request, 'items/item_list.html', context)


@login_required
def report_item(request):
    if request.method == 'POST':
        form = LostFoundItemForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.save()

            return redirect('item_list')

    else:
        requested_status = request.GET.get('status')
        valid_statuses = {value for value, _label in LostFoundItem._meta.get_field('status').choices}
        initial = {'status': requested_status} if requested_status in valid_statuses else None
        form = LostFoundItemForm(initial=initial)

    return render(
        request,
        'items/report_item.html',
        {'form': form}
    )




def item_detail(request, pk):
    item = get_object_or_404(
        LostFoundItem,
        pk=pk
    )

    return render(
        request,
        'items/item_detail.html',
        {'item': item}
    )


def register(request):
    next_url = request.POST.get('next') or request.GET.get('next', '')
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect('dashboard')
    else:
        form = StudentRegistrationForm()

    return render(
        request,
        'items/register.html',
        {'form': form, 'next': next_url}
    )
