from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count,Q
from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from io import BytesIO
import zipfile, os
from collections import defaultdict
from django.http import HttpResponse
from reportlab.lib import colors
from functools import wraps
from django.http import JsonResponse
from .models import User, Team, Membership, Message, JoinRequest
from django.urls import reverse
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

def role_required(allowed_roles=None):
    if allowed_roles is None:
        allowed_roles = []

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseForbidden("You must be logged in.")
            
            if request.user.role not in allowed_roles:
                return HttpResponseForbidden("You do not have permission to access this page.")
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def create_admin(request):
    User.objects.create_user(
        username='sami',
        password='sami',
        role='admin',
        full_name='Sami Admin',
        email='sami@example.com',
        is_active= True
    )
    return HttpResponse("Admin user 'sami' created successfully!")


def home(request):
    teams = Team.objects.all().annotate(member_count=Count('membership')).order_by('name')
    team_data = []
    for team in teams:
        is_member = request.user.is_authenticated and Membership.objects.filter(user=request.user, team=team, active=True).exists()
        team_data.append({'team': team, 'member_count': team.member_count, 'is_member': is_member})
    return render(request, 'home.html', {'team_data': team_data})



@login_required
def custom_password_change(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user) 
            messages.success(request, 'Your password was changed successfully!')
            return redirect('home')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, 'change_password.html', {'form': form})

def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user and user.is_active:
            auth_login(request, user)
            if user.role == 'admin': return redirect('admin_dashboard')
            if user.role == 'leader': return redirect('leader_dashboard')
            if user.role == 'member': return redirect('member_dashboard')
            return redirect('home')
        messages.error(request, "Invalid credentials")

    return render(request, 'login.html')


def custom_logout(request):
    auth_logout(request)
    return redirect('home')


@login_required
@role_required(allowed_roles=['admin'])
def admin_dashboard(request):
    if request.user.role != 'admin':
        return redirect('home')

    teams = Team.objects.annotate(
        member_count=Count('membership__id', filter=Q(membership__active=True))
    )
    team = Team.objects.all()
    return render(request, 'admin_dashboard.html', {
        'teams': teams,
        'team': team,
    })


@login_required
@role_required(allowed_roles=['admin'])
def admin_view_team_members(request, team_id):
    if request.user.role != 'admin':
        return redirect('home')

    team = get_object_or_404(Team, id=team_id)
    members = Membership.objects.filter(team=team, active=True).select_related('user')

    return render(request, 'admin_team_members.html', {
        'team': team,
        'members': members,
    })


@login_required
@role_required(allowed_roles=['admin'])
def create_team(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden("Only admin can create teams.")

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        image = request.FILES.get('image')  

        if name and description and image:
            Team.objects.create(
                name=name,
                description=description,
                image=image
            )
            messages.success(request, "Team created successfully.")
            return redirect('admin_dashboard')
        
        messages.error(request, "All fields (including image) are required.")

    return render(request, 'create_team.html')

@login_required
@role_required(allowed_roles=['admin'])
def manage_leaders(request):
    if request.user.role != 'admin':
        return redirect('home')

    if request.method == 'POST':
        team_id = request.POST.get('team')
        leader_id = request.POST.get('leader')
        team = get_object_or_404(Team, id=team_id)
        leader = get_object_or_404(User, id=leader_id)
        team.leaders.add(leader)
        if leader.role != 'leader':
            leader.role = 'leader'
            leader.save()
        messages.success(request, "Leader assigned successfully.")
        return redirect('manage_leaders')

    teams = Team.objects.all()
    leaders = User.objects.filter(role='member')
    return render(request, 'manage_leaders.html', {'teams': teams, 'leaders': leaders})

@login_required
@role_required(allowed_roles=['admin'])
def manage_leaders_to_remove(request):
    teams = Team.objects.annotate(member_count=Count('members'))
    return render(request, 'list_of_leaders.html', {'teams': teams})

@login_required
@role_required(allowed_roles=['admin'])
def remove_leaders(request, team_id, leader_id):
    if request.user.role != 'admin':
        return redirect('home')

    team = get_object_or_404(Team, id=team_id)
    leader = get_object_or_404(User, id=leader_id)

    if request.method == 'POST':
        # Remove from leaders
        team.leaders.remove(leader)

        # Add to members if not already there
        if not team.members.filter(id=leader.id).exists():
            team.members.add(leader)

        # Change their role from leader to member
        if leader.role == 'leader':
            leader.role = 'member'
            leader.save()

        messages.success(request, f"Leader {leader.username} removed from {team.name} and assigned as a member.")
        return redirect('list_of_leaders')

    return render(request, 'remove_leaders.html', {
        'team': team,
        'leader': leader
    })

@login_required
@role_required(allowed_roles=['admin'])
def register_leader(request):
    if request.user.role != 'admin':
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        team_id = request.POST.get('team')

        if username and password and team_id:
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already exists.")
            else:
                user = User.objects.create_user(username=username, password=password, role='leader')
                team = get_object_or_404(Team, id=team_id)
                team.leaders.add(user)
                messages.success(request, f"Leader '{username}' assigned to '{team.name}'.")
                return redirect('admin_dashboard')
        else:
            messages.error(request, "All fields are required.")

    teams = Team.objects.all()
    return render(request, 'register_leader.html', {'teams': teams})


def register_member(request):
    # Member self-registration (no team assigned yet)
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        full_name = request.POST.get('full_name')
        batch = request.POST.get('batch')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        profile_image = request.FILES.get('profile_image')

        if not all([username, password, full_name, batch]):
            messages.error(request, "Please fill in all required fields.")
            return render(request, 'register_member.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, 'register_member.html')

        user = User.objects.create_user(
            username=username,
            password=password,
            role='member',
            full_name=full_name,
            batch=batch,
            phone=phone,
            address=address,
            profile_image=profile_image,
        )
        messages.success(request, "Account created successfully. Please log in.")
        return redirect('login')

    return render(request, 'register_member.html')


@login_required
@role_required(allowed_roles=['leader', 'admin'])
def leader_dashboard(request):
    if request.user.role != 'leader':
        return redirect('home')

    # Get all teams the user leads
    teams = request.user.leading_teams.annotate(member_count=Count('membership'))
    join_requests = JoinRequest.objects.filter(team__in=teams, approved=False, processed=False)
    messages_list = Message.objects.filter(team__in=teams).order_by('-created_at')
    for req in join_requests:
        req.user_teams = req.user.membership_set.filter(active=True).select_related('team')


    if request.method == 'POST':
        # 🟩 Handle new message post
        if 'content' in request.POST:
            content = request.POST.get('content')
            # 🟨 Choose the first team (or define a default_team field in User)
            team = teams.first()
            if not team:
                messages.error(request, "You are not assigned to any team.")
            else:
                Message.objects.create(team=team, author=request.user, content=content)
                messages.success(request, "Message posted.")
            return redirect('leader_dashboard')

        # 🟩 Handle approving join request
        if 'approve_request_id' in request.POST:
            req_id = request.POST.get('approve_request_id')
            join_req = get_object_or_404(JoinRequest, id=req_id, team__leaders=request.user)
            if not join_req.approved:
                join_req.approved = True
                join_req.processed = True
                join_req.save()
                Membership.objects.create(user=join_req.user, team=join_req.team, active=True)
                messages.success(request, f"Approved {join_req.user.username}.")
            return redirect('leader_dashboard')

    return render(request, 'leader_dashboard.html', {
        'teams': teams,
        'join_requests': join_requests,
        'messages_list': messages_list
    })





@login_required
@role_required(allowed_roles=['leader', 'admin'])
def view_team_members(request, team_id):
    
    team = get_object_or_404(Team, id=team_id, leaders=request.user)
    members = Membership.objects.filter(team=team, active=True).select_related('user')

    # base URL should be like: /leader/member/
    base_detail_url = reverse('member_detail', args=[0]).replace("0/", "")

    return render(request, 'leader_team_members.html', {
        'team': team,
        'members': members,
        'base_detail_url': base_detail_url,  # pass to JS
    })

@login_required
@role_required(allowed_roles=['leader', 'admin'])
def ajax_search_team_members(request, team_id):
    if not Team.objects.filter(id=team_id, leaders=request.user).exists():
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    query = request.GET.get('q', '')
    memberships = Membership.objects.filter(team_id=team_id, active=True).select_related('user')

    if query:
        memberships = memberships.filter(
            Q(user__username__icontains=query) |
            Q(user__full_name__icontains=query) |
            Q(user__email__icontains=query)
        )

    members_data = [
        {
            'id': m.user.id,
            'username': m.user.username,
            'full_name': m.user.full_name,
            'email': m.user.email,
        }
        for m in memberships
    ]

    return JsonResponse({'members': members_data})


@login_required
@role_required(allowed_roles=['leader', 'admin'])
def member_detail(request, user_id):
    member = get_object_or_404(User, id=user_id)

    # Ensure current user is leader of member's team
    membership = Membership.objects.filter(user=member, team__leaders=request.user, active=True).select_related('team').first()
    if not membership:
        return redirect('home')

    team = membership.team

    # Get all other team members (except the current one), ordered by username
    other_members = Membership.objects.filter(
        team=team,
        active=True
    ).exclude(user=member).select_related('user').order_by('user__username')

    return render(request, 'member_detail.html', {
        'member': member,
        'team': team,
        'other_members': other_members
    })

@login_required
@role_required(allowed_roles=['leader', 'admin'])
def download_team_members_by_batch_zip(request, team_id):
    if request.user.role != 'leader':
        return HttpResponse("Only leaders can access this.")

    try:
        team = Team.objects.get(id=team_id, leaders=request.user)
    except Team.DoesNotExist:
        return HttpResponse("You are not assigned to this team or team does not exist.")

    members = Membership.objects.filter(team=team).select_related('user')

    # Group members by batch
    members_by_batch = defaultdict(list)
    for membership in members:
        batch_value = getattr(membership.user, 'batch', None)  # ✅ use user.batch
        batch = str(batch_value) if batch_value is not None else "Unknown Batch"
        members_by_batch[batch].append(membership.user)

    # Create ZIP in memory
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:

        for batch, batch_members in members_by_batch.items():
            pdf_buffer = BytesIO()
            p = canvas.Canvas(pdf_buffer, pagesize=A4)
            width, height = A4

            # Header
            p.setFont("Helvetica-Bold", 18)
            p.setFillColor(colors.HexColor("#2c3e50"))
            p.drawString(40, height - 40, f"WSUEVASUE Fellowship - Batch: {batch}")
            p.setFont("Helvetica", 12)
            p.setFillColor(colors.black)
            p.drawString(40, height - 60, f"Team: {team.name} | Batch: {batch}")
            p.setStrokeColor(colors.HexColor("#2c3e50"))
            p.setLineWidth(1)
            p.line(40, height - 65, width - 40, height - 65)

            # Table header
            y_position = height - 90
            p.setFont("Helvetica-Bold", 10)
            p.drawString(40, y_position, "Full Name")
            p.drawString(160, y_position, "Username")
            p.drawString(300, y_position, "Role")
            p.drawString(360, y_position, "Phone")
            p.drawString(430, y_position, "Address")
            y_position -= 15
            p.line(40, y_position, width - 40, y_position)
            y_position -= 10

            # Members list
            p.setFont("Helvetica", 9)
            for user in batch_members:
                if y_position < 80:  # leave space for footer
                    p.showPage()
                    y_position = height - 40
                    p.setFont("Helvetica", 9)

                # Text fields
                full_name = user.full_name or f"{user.first_name} {user.last_name}".strip() or "N/A"
                p.drawString(40, y_position, full_name[:20])  # truncate if too long
                p.drawString(160, y_position, user.username or "N/A")
                p.drawString(300, y_position, getattr(user, 'get_role_display', lambda: user.role)())
                p.drawString(360, y_position, user.phone or "N/A")
                p.drawString(430, y_position, (user.address[:20] + "...") if user.address and len(user.address) > 20 else (user.address or "N/A"))

                # Profile image (if available)
                if user.profile_image and user.profile_image.path:
                    try:
                        img_path = user.profile_image.path
                        p.drawImage(img_path, width - 80, y_position - 5, width=35, height=35, preserveAspectRatio=True, mask='auto')
                    except Exception:
                        pass  # skip broken images

                y_position -= 40  # bigger gap to fit image

            # Footer
            p.setFont("Helvetica-Oblique", 9)
            p.setFillColor(colors.grey)
            p.drawString(40, 25, f"@WSUEVASUE - Team: {team.name}")

            p.save()
            pdf_buffer.seek(0)

            # Add PDF to ZIP
            batch_filename = f"Batch_{batch}.pdf"
            zip_file.writestr(batch_filename, pdf_buffer.read())

    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{team.name}_by_batch.zip"'
    return response


@login_required
def member_dashboard(request):
    teams = Team.objects.filter(membership__user=request.user, membership__active=True)
    return render(request, 'member_dashboard.html', {'teams': teams})




def team_detail(request, pk):
    team = get_object_or_404(Team, pk=pk)
    is_member = request.user.is_authenticated and Membership.objects.filter(user=request.user, team=team, active=True).exists()
    has_requested = request.user.is_authenticated and JoinRequest.objects.filter(user=request.user, team=team, approved=False).exists()

    if is_member:
        messages_list = Message.objects.filter(team=team).order_by('-created_at')
        return render(request, 'team_detail_member.html', {'team': team, 'messages': messages_list})

    if request.method == 'POST' and request.user.is_authenticated and not has_requested:
        JoinRequest.objects.create(user=request.user, team=team)
        messages.success(request, "Join request sent.")
        return redirect('team_detail', pk=team.pk)

    return render(request, 'team_detail.html', {'team': team, 'has_requested': has_requested})


