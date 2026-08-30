"""
Seeds the local sandbox stub with a demo org, 5 demo users (one per role, including
the Unit Owner role and its dedicated portal), sample units, unit-resident links,
one sample maintenance request, sample bills (recurring dues + a one-time utility
charge), and one recorded payment.

Run after creating tables:
    python -m scripts.seed_db
"""
import sys
import os
import uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine, Base
from app.models._local_stub_platform_tables import LocalStubOrganization, LocalStubUser
from app.models.condo_units import CondoUnit
from app.models.condo_unit_residents import CondoUnitResident
from app.models.condo_maintenance_requests import CondoMaintenanceRequest
from app.models.condo_bills import CondoBill
from app.models.condo_payments import CondoPayment
from app.core.security import hash_password
from datetime import datetime, timedelta


def seed():
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        org = db.query(LocalStubOrganization).filter_by(name='Utrera Condos Corporation').first()
        if org is None:
            org = LocalStubOrganization(id=uuid.uuid4(), name='Utrera Condos Corporation')
            db.add(org)
            db.commit()
            print(f'Created organization: {org.id}')

        demo_users = [
            ('Alice Administrator', 'admin@condo.test', 'admin'),
            ('Peter Manager', 'manager@condo.test', 'manager'),
            ('Fiona FrontDesk', 'staff@condo.test', 'staff'),
            ('Ramon Resident', 'resident@condo.test', 'resident'),
            ('Olivia Owner', 'owner@condo.test', 'unit_owner'),
        ]
        created = {}
        for full_name, email, role in demo_users:
            user = db.query(LocalStubUser).filter_by(email=email).first()
            if user is None:
                user = LocalStubUser(
                    id=uuid.uuid4(), organization_id=org.id, full_name=full_name,
                    email=email, password_hash=hash_password('Password123!'), role=role,
                )
                db.add(user)
                db.commit()
                print(f'Created user: {email} ({role})')
            created[role] = user

        unit = db.query(CondoUnit).filter_by(organization_id=org.id, unit_number='101', building='Tower A').first()
        if unit is None:
            unit = CondoUnit(id=uuid.uuid4(), organization_id=org.id, unit_number='101',
                              building='Tower A', floor=1, status='occupied', created_by=created['admin'].id)
            db.add(unit)
            db.commit()
            print(f'Created unit: {unit.id}')

        for number, building, floor, status_ in [
            ('102', 'Tower A', 1, 'vacant'),
            ('201', 'Tower A', 2, 'under_maintenance'),
            ('301', 'Tower B', 3, 'vacant'),
        ]:
            existing = db.query(CondoUnit).filter_by(organization_id=org.id, unit_number=number, building=building).first()
            if existing is None:
                db.add(CondoUnit(id=uuid.uuid4(), organization_id=org.id, unit_number=number,
                                  building=building, floor=floor, status=status_, created_by=created['admin'].id))
        db.commit()

        # Unit Owner holds title to unit 101 and is its primary contact; the Resident
        # (tenant) also lives there but is not the primary contact — this mirrors a
        # real owner-leases-to-tenant scenario and is what the Owner Portal / Payments
        # section scoping is built to demonstrate.
        owner_link = db.query(CondoUnitResident).filter_by(unit_id=unit.id, user_id=created['unit_owner'].id).first()
        if owner_link is None:
            owner_link = CondoUnitResident(
                id=uuid.uuid4(), organization_id=org.id, unit_id=unit.id, user_id=created['unit_owner'].id,
                relationship_type='owner', is_primary_contact=True, moved_in_at=datetime.utcnow(),
                created_by=created['admin'].id,
            )
            db.add(owner_link)
            db.commit()
            print('Linked unit owner to unit 101.')

        tenant_link = db.query(CondoUnitResident).filter_by(unit_id=unit.id, user_id=created['resident'].id).first()
        if tenant_link is None:
            tenant_link = CondoUnitResident(
                id=uuid.uuid4(), organization_id=org.id, unit_id=unit.id, user_id=created['resident'].id,
                relationship_type='tenant', is_primary_contact=False, moved_in_at=datetime.utcnow(),
                created_by=created['admin'].id,
            )
            db.add(tenant_link)
            db.commit()
            print('Linked resident (tenant) to unit 101.')

        sample = db.query(CondoMaintenanceRequest).filter_by(unit_id=unit.id, category='plumbing').first()
        if sample is None:
            sample = CondoMaintenanceRequest(
                id=uuid.uuid4(), organization_id=org.id, unit_id=unit.id, requested_by=created['resident'].id,
                assigned_to=created['staff'].id, category='plumbing',
                description='Kitchen faucet has been leaking for two days.',
                priority='medium', status='assigned',
                created_by=created['resident'].id, updated_by=created['staff'].id,
            )
            db.add(sample)
            db.commit()
            print('Created sample maintenance request.')

        # ── Bills: one recurring (monthly association dues, still pending) and one
        # one-time utility charge (already paid) ──
        dues_bill = db.query(CondoBill).filter_by(unit_id=unit.id, bill_type='association_dues').first()
        if dues_bill is None:
            today = datetime.utcnow().date()
            dues_bill = CondoBill(
                id=uuid.uuid4(), organization_id=org.id, unit_id=unit.id,
                bill_type='association_dues', description='Monthly association dues — Tower A 101',
                amount=2500.00, billing_cycle='monthly', is_recurring_template=True,
                period_start=today.replace(day=1), period_end=today,
                due_date=today + timedelta(days=10), status='pending', amount_paid=0,
                created_by=created['manager'].id, updated_by=created['manager'].id,
            )
            db.add(dues_bill)
            db.commit()
            print('Created recurring association dues bill for unit 101.')

        utility_bill = db.query(CondoBill).filter_by(unit_id=unit.id, bill_type='utility').first()
        if utility_bill is None:
            today = datetime.utcnow().date()
            utility_bill = CondoBill(
                id=uuid.uuid4(), organization_id=org.id, unit_id=unit.id,
                bill_type='utility', description='Water utility — previous cycle',
                amount=450.00, billing_cycle='one_time', is_recurring_template=False,
                due_date=today - timedelta(days=5), status='paid', amount_paid=450.00,
                created_by=created['manager'].id, updated_by=created['manager'].id,
            )
            db.add(utility_bill)
            db.commit()
            print('Created one-time utility bill for unit 101.')

            payment = CondoPayment(
                id=uuid.uuid4(), organization_id=org.id, bill_id=utility_bill.id, unit_id=unit.id,
                paid_by=created['unit_owner'].id, amount=450.00, method='online',
                reference_number='DEMO-PAY-0001', status='completed', paid_at=datetime.utcnow(),
                notes='Seeded demo payment.', created_by=created['unit_owner'].id,
                updated_by=created['unit_owner'].id,
            )
            db.add(payment)
            db.commit()
            print('Recorded sample payment against the utility bill.')

        print('\nSeeding complete. Demo accounts (password: Password123!):')
        for _, email, role in demo_users:
            print(f'  {email:25s} -> {role}')
        print(f'\nOrganization ID: {org.id}')
        for role, user in created.items():
            print(f'  {role} user id: {user.id}')
    finally:
        db.close()


if __name__ == '__main__':
    seed()
