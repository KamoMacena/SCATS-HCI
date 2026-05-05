from django.shortcuts import render, redirect, get_object_or_404
from .models import Case, InvestigationUpdate, Evidence, Message, CaseLifecycleStage, LIFECYCLE_STAGES
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth import authenticate, login
from django.contrib import messages as django_messages


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("my_cases")
        else:
            django_messages.error(request, "Invalid credentials")

    return render(request, "login.html")


@login_required
def my_cases(request):
    cases = Case.objects.filter(assigned_to=request.user).order_by("-created_at")
    context = {
        "cases": cases,
        "under_investigation_count": 3,
        "stalled_count": 0,
        "closed_count": 1,
    }
    return render(request, "cases/my_cases.html", {"cases": cases})


@login_required
def case_detail(request, pk):
    case = get_object_or_404(Case, pk=pk, assigned_to=request.user)
    updates = case.updates.all().order_by("-created_at")

    # Create lifecycle stage rows the first time a case is opened
    for key, _ in LIFECYCLE_STAGES:
        CaseLifecycleStage.objects.get_or_create(case=case, stage_key=key)

    lifecycle_stages = case.lifecycle_stages.all()  # ordered by id

    return render(request, "cases/case_detail.html", {
        "case": case,
        "updates": updates,
        "lifecycle_stages": lifecycle_stages,
    })


@login_required
def add_update(request, pk):
    case = get_object_or_404(Case, pk=pk)

    if request.method == "POST":
        InvestigationUpdate.objects.create(
            case=case,
            action_type=request.POST.get("action_type"),
            description=request.POST.get("description"),
            created_by=request.user,
        )
        return redirect("case_detail", pk=pk)


@login_required
def upload_evidence(request, pk):
    case = get_object_or_404(Case, pk=pk)

    if request.method == "POST":
        Evidence.objects.create(
            case=case,
            file=request.FILES.get("file"),
            document_type=request.POST.get("document_type"),
            description=request.POST.get("description"),
        )
        return redirect("upload_evidence", pk=pk)

    evidence = case.evidence.all().order_by("-uploaded_at")
    return render(request, "cases/upload_evidence.html", {
        "case": case,
        "evidence": evidence,
    })


@login_required
def close_case(request, pk):
    case = get_object_or_404(Case, pk=pk)

    # Guard: silently redirect if already closed
    if case.status == "CASE CLOSED":
        return redirect("case_detail", pk=pk)

    if request.method == "POST":
        case.status = "CASE CLOSED"
        case.closure_reason = request.POST.get("closure_reason")
        case.closure_summary = request.POST.get("summary")
        case.save()
        return redirect("my_cases")

    return render(request, "cases/close_case.html", {"case": case})


@login_required
def messages_view(request, pk=None):
    cases = Case.objects.filter(assigned_to=request.user)

    selected_case = None
    messages = None

    if pk:
        selected_case = get_object_or_404(Case, pk=pk)
        messages = selected_case.messages.all().order_by("created_at")

        if request.method == "POST" and request.headers.get("X-Requested-With") == "XMLHttpRequest":
            content = request.POST.get("content", "").strip()
            if content:
                msg = Message.objects.create(
                    case=selected_case,
                    sender=request.user,
                    content=content,
                )
                initials = (msg.sender.get_full_name()[:2] or msg.sender.username[:2]).upper()
                return JsonResponse({
                    "status": "ok",
                    "message": {
                        "id": msg.id,
                        "content": msg.content,
                        "sender": msg.sender.username,
                        "initials": initials,
                        "created_at": msg.created_at.strftime("%d %b, %H:%M"),
                    },
                })
            return JsonResponse({"status": "error", "message": "Empty content"}, status=400)

        if request.method == "POST":
            content = request.POST.get("content", "").strip()
            if content:
                Message.objects.create(
                    case=selected_case,
                    sender=request.user,
                    content=content,
                )
            return redirect("messages_case", pk=pk)

        if request.method == "GET" and request.headers.get("X-Requested-With") == "XMLHttpRequest":
            after_id = int(request.GET.get("after", 0))
            new_msgs = selected_case.messages.filter(id__gt=after_id).order_by("created_at")
            return JsonResponse({
                "messages": [
                    {
                        "id": m.id,
                        "content": m.content,
                        "sender": m.sender.username,
                        "initials": (m.sender.get_full_name()[:2] or m.sender.username[:2]).upper(),
                        "created_at": m.created_at.strftime("%d %b, %H:%M"),
                    }
                    for m in new_msgs
                ]
            })

    return render(request, "cases/messages.html", {
        "cases": cases,
        "selected_case": selected_case,
        "messages": messages,
    })