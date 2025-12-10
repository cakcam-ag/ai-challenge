# Sample Meeting Notes for Testing

## Meeting 1: Team Standup - Sprint Planning

**Title:** Team Standup - Sprint Planning
**Date:** 2024-01-15

**Notes:**
We had our weekly team standup today. Sarah reported that she finished the authentication module and it's ready for review. John mentioned he's blocked on the database migration because he needs access to the staging environment. We decided to escalate this to DevOps.

Mike shared that he's working on the API documentation and expects to finish by Wednesday. Lisa brought up that we need to discuss the new feature requirements from the product team - they want to add a notification system.

Action items:
- Sarah: Create PR for authentication module (due: today)
- John: Contact DevOps for staging access (due: tomorrow)
- Mike: Complete API documentation (due: Wednesday)
- Lisa: Schedule meeting with product team about notifications (due: Friday)
- Team Lead: Review authentication PR by end of day

We also discussed the upcoming sprint goals. We're aiming to complete the user dashboard by end of month. Everyone agreed we need to prioritize the database migration first since it's blocking other work.

---

## Meeting 2: Client Presentation - Q4 Roadmap

**Title:** Client Presentation - Q4 Roadmap
**Date:** 2024-01-16

**Notes:**
Met with Acme Corp today to present our Q4 roadmap. Attendees: David (CEO), Maria (CTO), and their team of 5 engineers. We presented our plans for the new analytics dashboard, mobile app improvements, and integration with their CRM system.

David was very interested in the analytics dashboard and asked if we could accelerate the timeline. Maria raised concerns about data security and compliance requirements. We discussed GDPR compliance and agreed to have a dedicated security review session.

Key decisions:
- Analytics dashboard moved to priority 1
- Security review scheduled for next week
- Mobile app improvements pushed to Q1 next year
- CRM integration timeline confirmed for March

Action items:
- Project Manager: Prepare security review documentation (due: Friday)
- Engineering Lead: Create detailed analytics dashboard spec (due: Monday)
- Sales Team: Follow up with David about budget approval (due: Thursday)
- Security Team: Schedule compliance review meeting (due: next week)

David mentioned they're planning a major product launch in April, so we need to ensure everything is ready by then. Maria wants weekly status updates moving forward.

---

## Meeting 3: Technical Architecture Review

**Title:** Technical Architecture Review
**Date:** 2024-01-17

**Notes:**
Architecture review meeting with the engineering team. Participants: Alex (Senior Engineer), Emma (Backend Lead), Tom (Frontend Lead), and Rachel (DevOps).

We discussed the current microservices architecture and identified several pain points:
1. Service communication is getting complex with 15+ services
2. Database queries are slow due to lack of proper indexing
3. Deployment pipeline takes too long (45 minutes average)

Alex proposed implementing a service mesh to handle inter-service communication. Emma suggested we need to audit all database queries and add indexes. Tom mentioned the frontend build process could be optimized.

Rachel brought up infrastructure costs - we're spending too much on cloud resources. She suggested moving some services to reserved instances.

Decisions made:
- Approved service mesh implementation (Istio) - start next sprint
- Database audit and optimization - assign to backend team
- Frontend build optimization - Tom to investigate
- Infrastructure cost review - Rachel to prepare report

Action items:
- Alex: Research Istio implementation and create POC (due: next Friday)
- Emma: Audit database queries and create optimization plan (due: Wednesday)
- Tom: Profile frontend build and identify bottlenecks (due: Monday)
- Rachel: Prepare infrastructure cost analysis report (due: Thursday)
- Engineering Manager: Review all proposals and prioritize (due: Friday)

We also discussed the upcoming system migration. Everyone agreed we need a detailed migration plan with rollback procedures. Next architecture review scheduled for two weeks from now.

---

## How to Use These

1. Copy each meeting's title, date, and notes
2. Paste into the "Meetings" tab in the UI
3. Click "Process Meeting Notes"
4. See the AI extract:
   - Summary
   - Action items (auto-created as tasks)
   - Participants
5. Check the "Tasks" tab to see auto-created tasks
6. Try generating email drafts for follow-ups
7. Generate daily summary to see all meetings

