
from urllib.parse import urlencode

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from food_waste_management.models import ReportReview, ReviewTransitionError
from food_waste_management.permissions import staff_required
from discovery_dashboard.models import PickupClaim


PAGE_SIZE = 10
Handling = ReportReview.Handling
FollowUp = ReportReview.FollowUp


def _reviews():
    return ReportReview.objects.select_related(
        "report",
        "report__reported_by",
        "reviewed_by"
    )


def _base_context(active):
    return {
        "active": active,
        "pending_count": ReportReview.objects.pending().count(),
    }


@staff_required
def show_management(request):
    stats = ReportReview.objects.aggregate(
        pending=Count(
            "pk",
            filter=Q(
                verification_status=ReportReview.Verification.PENDING
            )
        ),
        accepted=Count(
            "pk",
            filter=Q(
                verification_status=ReportReview.Verification.ACCEPTED
            )
        ),
        rejected=Count(
            "pk",
            filter=Q(
                verification_status=ReportReview.Verification.REJECTED
            )
        ),
        done=Count(
            "pk",
            filter=Q(handling_status=Handling.DONE)
        ),
        sold=Count(
            "pk",
            filter=Q(follow_up=FollowUp.SELL)
        ),
        shared=Count(
            "pk",
            filter=Q(follow_up=FollowUp.SHARE)
        ),
        processed=Count(
            "pk",
            filter=Q(follow_up=FollowUp.PROCESS)
        ),
    )

    context = _base_context("summary")

    context.update({
        "title": "Food Waste Management",
        "stats": stats,
        "latest_pending": _reviews().pending().order_by(
            "report__created_at"
        )[:5],
    })

    return render(
        request,
        "management_landing.html",
        context
    )


@staff_required
def verification_queue(request):
    queryset = _reviews().pending().order_by(
        "report__created_at"
    )

    context = _base_context("queue")

    context.update({
        "page_obj": Paginator(
            queryset,
            PAGE_SIZE
        ).get_page(request.GET.get("page")),
        "qs_base": "",
    })

    return render(
        request,
        "food_waste_management/queue.html",
        context
    )


@staff_required
def handling_list(request):
    queryset = _reviews().accepted().order_by(
        "-reviewed_at"
    )

    status = request.GET.get("status", "")

    if status in {
        h.value for h in (
            Handling.AWAITING_PICKUP,
            Handling.CHECKED,
            Handling.DONE
        )
    }:
        queryset = queryset.filter(
            handling_status=status
        )
    else:
        status = ""

    search = request.GET.get("q", "").strip()

    if search:
        queryset = queryset.filter(
            Q(report__food_name__icontains=search)
            | Q(report__location__icontains=search)
            | Q(report__event__icontains=search)
        )

    params = {
        k: v for k, v in (
            ("status", status),
            ("q", search)
        ) if v
    }

    context = _base_context("handling")

    context.update({
        "page_obj": Paginator(
            queryset,
            PAGE_SIZE
        ).get_page(request.GET.get("page")),
        "qs_base": urlencode(params) + "&" if params else "",
        "status": status,
        "search": search,
        "filters": [
            ("", "Semua"),
            (
                Handling.AWAITING_PICKUP.value,
                Handling.AWAITING_PICKUP.label
            ),
            (
                Handling.CHECKED.value,
                Handling.CHECKED.label
            ),
            (
                Handling.DONE.value,
                Handling.DONE.label
            ),
        ],
    })

    return render(
        request,
        "food_waste_management/handling.html",
        context
    )


@staff_required
def review_detail(request, report_id):
    review = get_object_or_404(
        _reviews(),
        report_id=report_id
    )

    pickup_claims = PickupClaim.objects.filter(
        report_id=report_id
    ).select_related("user").order_by("-created_at")

    context = _base_context(
        "queue" if review.is_pending else "handling"
    )

    context.update({
        "review": review,
        "report": review.report,
        "pickup_claims": pickup_claims,
        "follow_up_choices": [
            (v, l) for v, l in FollowUp.choices if v
        ],
        "handling_steps": [
            (h.value, h.label)
            for h in (
                Handling.AWAITING_PICKUP,
                Handling.CHECKED,
                Handling.DONE
            )
        ],
    })

    return render(
        request,
        "food_waste_management/detail.html",
        context
    )


def _apply(request, report_id, action, success_message):
    with transaction.atomic():
        review = get_object_or_404(
            ReportReview.objects.select_for_update(),
            report_id=report_id
        )

        try:
            action(review)
        except ReviewTransitionError as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, success_message)

    if request.POST.get("next") == "queue":
        return redirect("food_waste_management:queue")

    return redirect(
        "food_waste_management:detail",
        report_id=report_id
    )


@staff_required
@require_POST
def accept_report(request, report_id):
    return _apply(
        request,
        report_id,
        lambda r: r.accept(request.user),
        "Laporan diterima dan siap ditindaklanjuti."
    )


@staff_required
@require_POST
def reject_report(request, report_id):
    reason = request.POST.get("reason", "")

    return _apply(
        request,
        report_id,
        lambda r: r.reject(request.user, reason),
        "Laporan ditolak."
    )


@staff_required
@require_POST
def update_handling(request, report_id):
    new_status = request.POST.get(
        "handling_status",
        ""
    )

    return _apply(
        request,
        report_id,
        lambda r: r.set_handling(new_status),
        "Status penanganan diperbarui."
    )


@staff_required
@require_POST
def set_follow_up(request, report_id):
    value = request.POST.get("follow_up", "")

    return _apply(
        request,
        report_id,
        lambda r: r.set_follow_up(value),
        "Tindak lanjut disimpan."
    )


@staff_required
@require_POST
def approve_pickup(request, claim_id):
    with transaction.atomic():
        klaim = get_object_or_404(
            PickupClaim.objects.select_for_update(),
            pk=claim_id
        )

        report_id = klaim.report_id

        if klaim.status != PickupClaim.Status.REVIEW:
            messages.error(
                request,
                "Pengambilan ini tidak sedang menunggu verifikasi."
            )

        elif not klaim.proof_photo:
            messages.error(
                request,
                "Foto bukti pengambilan belum tersedia."
            )

        else:
            klaim.status = PickupClaim.Status.SUCCESS
            klaim.completed_at = timezone.now()

            klaim.save(
                update_fields=[
                    "status",
                    "completed_at"
                ]
            )

            messages.success(
                request,
                "Pengambilan disetujui. Makanan sekarang NOT AVAILABLE."
            )

    return redirect(
        "food_waste_management:detail",
        report_id=report_id
    )


@staff_required
@require_POST
def reject_pickup(request, claim_id):
    with transaction.atomic():
        klaim = get_object_or_404(
            PickupClaim.objects.select_for_update(),
            pk=claim_id
        )

        report_id = klaim.report_id

        if klaim.status != PickupClaim.Status.REVIEW:
            messages.error(
                request,
                "Pengambilan ini tidak sedang menunggu verifikasi."
            )

        else:
            klaim.status = PickupClaim.Status.REJECTED
            klaim.completed_at = None

            klaim.save(
                update_fields=[
                    "status",
                    "completed_at"
                ]
            )

            messages.success(
                request,
                "Bukti pengambilan ditolak. Makanan dapat tersedia kembali."
            )

    return redirect(
        "food_waste_management:detail",
        report_id=report_id
    )
