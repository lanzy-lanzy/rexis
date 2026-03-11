from proposals.models import Proposal, ProposalStatus, ProposalType

def user_notifications(request):
    notifications = []
    unread_count = 0
    
    if request.user.is_authenticated:
        user = request.user
        
        if user.is_admin:
            pending_count = Proposal.objects.filter(status=ProposalStatus.PENDING).count()
            if pending_count > 0:
                notifications.append({
                    'title': 'Pending Proposals',
                    'message': f'There are {pending_count} proposals waiting for your review.',
                    'url': '/proposals/?status=PENDING',
                    'icon': 'document-text',
                    'color': 'amber'
                })
                unread_count += pending_count
                
        elif user.is_faculty:
            approved_count = Proposal.objects.filter(faculty_author=user, status=ProposalStatus.APPROVED).count()
            rejected_count = Proposal.objects.filter(faculty_author=user, status=ProposalStatus.REJECTED).count()
            
            if approved_count > 0:
                notifications.append({
                    'title': 'Approved Proposals',
                    'message': f'You have {approved_count} approved proposals.',
                    'url': '/proposals/?status=APPROVED',
                    'icon': 'check-circle',
                    'color': 'emerald'
                })
                unread_count += approved_count
                
            if rejected_count > 0:
                notifications.append({
                    'title': 'Rejected Proposals',
                    'message': f'You have {rejected_count} rejected proposals.',
                    'url': '/proposals/?status=REJECTED',
                    'icon': 'x-circle',
                    'color': 'red'
                })
                unread_count += rejected_count
                
        elif user.is_research_staff:
            approved_research = Proposal.objects.filter(proposal_type=ProposalType.RESEARCH, status=ProposalStatus.APPROVED).count()
            if approved_research > 0:
                notifications.append({
                    'title': 'Approved Research Projects',
                    'message': f'There are {approved_research} approved research proposals ready for implementation.',
                    'url': '/proposals/?status=APPROVED&proposal_type=RESEARCH',
                    'icon': 'academic-cap',
                    'color': 'blue'
                })
                unread_count += approved_research
                
        elif user.is_extension_staff:
            approved_extension = Proposal.objects.filter(proposal_type=ProposalType.EXTENSION, status=ProposalStatus.APPROVED).count()
            if approved_extension > 0:
                notifications.append({
                    'title': 'Approved Extension Projects',
                    'message': f'There are {approved_extension} approved extension proposals ready for implementation.',
                    'url': '/proposals/?status=APPROVED&proposal_type=EXTENSION',
                    'icon': 'globe-alt',
                    'color': 'orange'
                })
                unread_count += approved_extension

    return {
        'user_notifications': notifications,
        'notification_count': unread_count,
    }
