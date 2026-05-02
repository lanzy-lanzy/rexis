from proposals.models import Proposal, ProposalStatus, ProposalType

def user_notifications(request):
    notifications = []
    unread_count = 0

    if request.user.is_authenticated:
        user = request.user

        if user.is_admin:
            recommended_count = Proposal.objects.filter(status=ProposalStatus.RECOMMENDED_APPROVAL).count()
            if recommended_count > 0:
                notifications.append({
                    'title': 'Pending Final Review',
                    'message': f'There are {recommended_count} proposals recommended for approval waiting for your review.',
                    'url': '/proposals/?status=RECOMMENDED_APPROVAL',
                    'icon': 'document-text',
                    'color': 'amber'
                })
                unread_count += recommended_count

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

        elif user.is_research_extension_staff:
            pending_recommendations = Proposal.objects.filter(status=ProposalStatus.PENDING_RECOMMENDATION).count()
            if pending_recommendations > 0:
                notifications.append({
                    'title': 'Pending Recommendations',
                    'message': f'There are {pending_recommendations} proposals waiting for staff recommendation.',
                    'url': '/proposals/?status=PENDING_RECOMMENDATION',
                    'icon': 'document-text',
                    'color': 'amber'
                })
                unread_count += pending_recommendations

    return {
        'user_notifications': notifications,
        'notification_count': unread_count,
    }