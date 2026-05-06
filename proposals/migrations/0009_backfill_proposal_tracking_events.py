from django.db import migrations


def create_event(ProposalTrackingEvent, proposal, event_type, title, when, actor_id=None, description='', status=''):
    event = ProposalTrackingEvent.objects.create(
        proposal_id=proposal.id,
        event_type=event_type,
        title=title,
        description=description,
        status=status or proposal.status,
        actor_id=actor_id,
    )
    if when:
        ProposalTrackingEvent.objects.filter(pk=event.pk).update(created_at=when)


def backfill_tracking_events(apps, schema_editor):
    Proposal = apps.get_model('proposals', 'Proposal')
    ProposalTrackingEvent = apps.get_model('proposals', 'ProposalTrackingEvent')

    for proposal in Proposal.objects.all().iterator():
        if ProposalTrackingEvent.objects.filter(proposal_id=proposal.id).exists():
            continue

        submitter_id = proposal.submitted_by_id or proposal.faculty_author_id
        create_event(
            ProposalTrackingEvent,
            proposal,
            'SUBMITTED',
            'Proposal submitted',
            proposal.date_submitted,
            actor_id=submitter_id,
            description='Proposal was submitted for Research & Extension staff recommendation.',
            status='PENDING_RECOMMENDATION',
        )

        if proposal.recommended_at:
            if proposal.status == 'RECOMMENDED_REVISION':
                event_type = 'REVISION_REQUESTED'
                title = 'Revision requested by Research & Extension Staff'
                description = proposal.recommendation_notes or 'Additional proposal requirements were requested.'
            else:
                event_type = 'RECOMMENDED_APPROVAL'
                title = 'Recommended for admin approval'
                description = proposal.recommendation_notes or 'Proposal was recommended for administrator approval.'
            create_event(
                ProposalTrackingEvent,
                proposal,
                event_type,
                title,
                proposal.recommended_at,
                actor_id=proposal.recommended_by_id,
                description=description,
                status=proposal.status if proposal.status.startswith('RECOMMENDED') else 'RECOMMENDED_APPROVAL',
            )

        if proposal.reviewed_at:
            if proposal.status == 'APPROVED':
                event_type = 'ADMIN_APPROVED'
                title = 'Approved by admin'
                description = proposal.review_notes or 'Proposal was approved by the administrator.'
            elif proposal.status == 'REJECTED':
                event_type = 'ADMIN_REJECTED'
                title = 'Rejected by admin'
                description = proposal.review_notes or 'Proposal was rejected and requires resubmission.'
            else:
                continue
            create_event(
                ProposalTrackingEvent,
                proposal,
                event_type,
                title,
                proposal.reviewed_at,
                actor_id=proposal.reviewed_by_id,
                description=description,
                status=proposal.status,
            )


class Migration(migrations.Migration):

    dependencies = [
        ('proposals', '0008_proposaltrackingevent'),
    ]

    operations = [
        migrations.RunPython(backfill_tracking_events, migrations.RunPython.noop),
    ]
