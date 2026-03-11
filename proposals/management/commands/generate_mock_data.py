import os
import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from users.models import CustomUser, UserRole
from proposals.models import Proposal, ProposalType, ProposalStatus
from research.models import ResearchRecord, ResearchStatus
from extension.models import ExtensionRecord, ExtensionStatus

class Command(BaseCommand):
    help = 'Populates the database with realistic mock data for proposals, research, and extension activities.'

    def generate_pdf(self, title):
        """Creates a minimal valid mock PDF file in memory."""
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Count 1\n/Kids [3 0 R]\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Resources <<\n/Font <<\n/F1 4 0 R\n>>\n>>\n/Contents 5 0 R\n>>\nendobj\n4 0 obj\n<<\n/Type /Font\n/Subtype /Type1\n/BaseFont /Helvetica\n>>\nendobj\n5 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 24 Tf\n100 700 Td\n(Mock Document) Tj\nET\nendstream\nendobj\nxref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000057 00000 n \n0000000114 00000 n \n0000000219 00000 n \n0000000305 00000 n \ntrailer\n<<\n/Size 6\n/Root 1 0 R\n>>\nstartxref\n399\n%%EOF"
        return SimpleUploadedFile(f"{title.replace(' ', '_').lower()}.pdf", pdf_content, content_type="application/pdf")
        
    def generate_image(self, name):
        """Creates a minimal valid mock Image file (1x1 pixel PNG) in memory."""
        # A tiny 1x1 transparent PNG
        img_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xfa\x0f\x00\x01\x05\x01\x02\xcf\xa0.\xcd\x00\x00\x00\x00IEND\xaeB`\x82'
        return SimpleUploadedFile(f"{name.replace(' ', '_').lower()}.png", img_content, content_type="image/png")

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting data populator...')
        
        # 1. Fetch Users
        faculty_users = list(CustomUser.objects.filter(role=UserRole.FACULTY))
        research_staff = list(CustomUser.objects.filter(role=UserRole.RESEARCH_STAFF))
        extension_staff = list(CustomUser.objects.filter(role=UserRole.EXTENSION_STAFF))
        admin_user = CustomUser.objects.filter(role=UserRole.ADMIN).first()

        if not faculty_users:
            self.stdout.write(self.style.ERROR('No faculty users found. Please create some users first.'))
            return
            
        proposals_data = [
            ("AI-Driven Crop Yield Prediction Model for Local Farmers", ProposalType.RESEARCH, ProposalStatus.APPROVED),
            ("Blockchain Integration in Municipal Record Keeping", ProposalType.RESEARCH, ProposalStatus.APPROVED),
            ("Renewable Energy Access for Off-Grid Communities", ProposalType.EXTENSION, ProposalStatus.APPROVED),
            ("Evaluating the Impact of Remote Learning on STEM Fields", ProposalType.RESEARCH, ProposalStatus.REJECTED),
            ("Digital Literacy Workshops for Senior Citizens", ProposalType.EXTENSION, ProposalStatus.APPROVED),
            ("Water Quality Monitoring using Low-Cost IoT Sensors", ProposalType.RESEARCH, ProposalStatus.APPROVED),
            ("Disaster Preparedness Training for Coastal Barangays", ProposalType.EXTENSION, ProposalStatus.APPROVED),
            ("Smart Traffic Management Algorithms for Urban Areas", ProposalType.RESEARCH, ProposalStatus.PENDING),
            ("Mental Health First Aid and Awareness Kampanya", ProposalType.EXTENSION, ProposalStatus.APPROVED),
            ("Development of Biodegradable Packaging Materials", ProposalType.RESEARCH, ProposalStatus.REJECTED),
            ("Micro-Business Financing Seminars and Clinics", ProposalType.EXTENSION, ProposalStatus.PENDING),
            ("Cybersecurity Protocols for Local E-Governance", ProposalType.RESEARCH, ProposalStatus.APPROVED),
            ("Agri-Tech Adoption Rates Among Smallholder Farmers", ProposalType.RESEARCH, ProposalStatus.APPROVED),
            ("Youth Code Camp: Introduction to Programming", ProposalType.EXTENSION, ProposalStatus.APPROVED),
        ]

        abstract_lorem = "This study aims to address significant gaps in the current landscape by deploying innovative methodologies to ensure sustainable development. We will be surveying participants, analyzing quantitative metrics, and publishing a comprehensive guideline designed to improve community outcomes and expand the boundaries of technical integration."
        desc_lorem = "The full implementation will span across 12 months, involving multiple phases including literature review, field testing, data aggregation, and peer-reviewed assessment. Our target demographics include marginalized sectors where access to these tools has historically been limited. By leveraging modern frameworks, we expect a 40% increase in operational efficiency, generating both academic value and undeniable societal impact."

        self.stdout.write('Generating Proposals...')
        created_proposals = []
        
        for idx, (title, p_type, p_status) in enumerate(proposals_data):
            faculty = random.choice(faculty_users)
            
            p = Proposal(
                title=title,
                faculty_author=faculty,
                proposal_type=p_type,
                abstract=abstract_lorem,
                full_description=desc_lorem + f"\n\nMilestone Phase {idx+1}: Complete data assimilation.",
                status=p_status,
                date_submitted=timezone.now() - timedelta(days=random.randint(5, 60)),
                reviewed_by=admin_user if p_status != ProposalStatus.PENDING else None,
                reviewed_at=timezone.now() - timedelta(days=random.randint(1, 4)) if p_status != ProposalStatus.PENDING else None,
                review_notes="Approved for development. Meets institutional standards." if p_status == ProposalStatus.APPROVED else ("Needs more budget clarification." if p_status == ProposalStatus.REJECTED else "")
            )
            
            # Add files to a few of them
            if random.random() > 0.3:
                p.proposal_document = self.generate_pdf(f"Proposal_{idx}")
            if random.random() > 0.4:
                p.budget_pdf = self.generate_pdf(f"Budget_{idx}")
            if random.random() > 0.5:
                p.supporting_image = self.generate_image(f"Support_{idx}")
                
            p.save()
            created_proposals.append(p)
            
        self.stdout.write(self.style.SUCCESS(f'Created {len(created_proposals)} Proposals.'))
        
        if not research_staff and not extension_staff:
            self.stdout.write(self.style.WARNING("No research or extension staff found. Skipping record generation."))
            return

        # Generate Research Records
        self.stdout.write('Generating Research Records...')
        research_proposals = [p for p in created_proposals if p.proposal_type == ProposalType.RESEARCH and p.status == ProposalStatus.APPROVED]
        
        res_count = 0
        for p in research_proposals:
            if not research_staff:
                break
                
            lead = random.choice(research_staff)
            status = random.choice([ResearchStatus.ONGOING, ResearchStatus.ONGOING, ResearchStatus.COMPLETED, ResearchStatus.PUBLISHED])
            
            start_date = p.date_submitted + timedelta(days=5)
            end_date = start_date + timedelta(days=random.randint(90, 365)) if status in [ResearchStatus.COMPLETED, ResearchStatus.PUBLISHED] else None
            
            r = ResearchRecord(
                proposal=p,
                lead_researcher=lead,
                status=status,
                start_date=start_date,
                end_date=end_date,
                funding_source=random.choice(["DOST", "CHED", "University Grant", "Private Tech Corp", ""]),
                funding_amount=random.choice([50000.00, 125000.00, 250000.00, 500000.00]) if random.random() > 0.5 else None,
                output_description="The model achieved an accuracy of 92% in preliminary tests. We are finalizing the documentation for journal submission." if status != ResearchStatus.ONGOING else "",
                publication_link="https://scholar.google.com/" if status == ResearchStatus.PUBLISHED else ""
            )
            r.save()
            
            # Co-researchers
            co_workers = [s for s in research_staff if s != lead]
            if co_workers and random.random() > 0.3:
                r.co_researchers.add(*random.sample(co_workers, k=random.randint(1, min(2, len(co_workers)))))
                
            res_count += 1
            
        self.stdout.write(self.style.SUCCESS(f'Created {res_count} Research Records.'))

        # Generate Extension Records
        self.stdout.write('Generating Extension Records...')
        extension_proposals = [p for p in created_proposals if p.proposal_type == ProposalType.EXTENSION and p.status == ProposalStatus.APPROVED]
        
        ext_count = 0
        from extension.models import ExtensionType
        for p in extension_proposals:
            if not extension_staff:
                break
                
            lead = random.choice(extension_staff)
            status = random.choice([ExtensionStatus.PLANNING, ExtensionStatus.ONGOING, ExtensionStatus.COMPLETED])
            
            start_date = p.date_submitted + timedelta(days=15)
            end_date = start_date + timedelta(days=random.randint(5, 30)) if status == ExtensionStatus.COMPLETED else None
            
            ext = ExtensionRecord(
                proposal=p,
                coordinator=lead,
                title=p.title,
                extension_type=random.choice(ExtensionType.choices)[0],
                partner_community=random.choice(["Barangay San Isidro", "Farmers Cooperative of Region 3", "Local Youth Council", "Coastal Fisherfolks Assocation"]),
                location=random.choice(["City Hall Auditorium", "Community Plaza", "Online Zoom", "Public School Campus"]),
                status=status,
                start_date=start_date,
                end_date=end_date,
                beneficiary_count=random.randint(20, 150) if status != ExtensionStatus.PLANNING else 0,
                description="We conducted a series of seminars focusing on practical application. The attendees were highly engaged and requested follow-up sessions.",
            )
            
            if status == ExtensionStatus.COMPLETED:
                ext.output_documents = self.generate_pdf(f"Extension_Report_{ext_count}")
                ext.photos = self.generate_image(f"Event_Photo_{ext_count}")
                
            ext.save()
            
            # Team members
            co_workers = [s for s in extension_staff if s != lead]
            if co_workers and random.random() > 0.3:
                ext.team_members.add(*random.sample(co_workers, k=random.randint(1, min(3, len(co_workers)))))
                
            ext_count += 1

        self.stdout.write(self.style.SUCCESS(f'Created {ext_count} Extension Records.'))
        self.stdout.write(self.style.SUCCESS('Successfully populated all mock data!'))
