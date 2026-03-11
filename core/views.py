from django.shortcuts import render
from research.models import ResearchRecord
from extension.models import ExtensionRecord
from users.models import CustomUser, UserRole

def home(request):
    research_count = ResearchRecord.objects.count()
    extension_count = ExtensionRecord.objects.count()
    faculty_count = CustomUser.objects.filter(role=UserRole.FACULTY).count()
    
    # Get unique partner communities
    communities_count = ExtensionRecord.objects.exclude(partner_community='').values('partner_community').distinct().count()

    context = {
        'research_count': research_count,
        'extension_count': extension_count,
        'faculty_count': faculty_count,
        'communities_count': communities_count,
    }
    return render(request, 'home.html', context)
