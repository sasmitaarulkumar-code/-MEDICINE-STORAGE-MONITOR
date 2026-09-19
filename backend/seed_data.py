from datetime import datetime, timedelta, date
import bcrypt
from app.database import engine, Base, SessionLocal
from app.models import User, StorageUnit, Medicine, MedicineBatch, SensorReading, Alert, AuditLog

def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")

def seed():
    print("[MEDGUARD SEED] Creating database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(User).first():
            print("[MEDGUARD SEED] Database already contains records. Skipping initial seed.")
            return

        print("[MEDGUARD SEED] Seeding default users (Admin, Staff, Viewer)...")
        admin = User(
            username="admin",
            email="admin@medguard.health",
            hashed_password=hash_password("Admin@123"),
            full_name="Dr. Eleanor Vance (Chief Pharmacist)",
            role="admin"
        )
        staff = User(
            username="staff",
            email="staff@medguard.health",
            hashed_password=hash_password("Staff@123"),
            full_name="Marcus Reed (Duty Staff Nurse)",
            role="staff"
        )
        viewer = User(
            username="viewer",
            email="auditor@medguard.health",
            hashed_password=hash_password("Viewer@123"),
            full_name="Sarah Jenkins (Regulatory Inspector)",
            role="viewer"
        )
        db.add_all([admin, staff, viewer])
        db.commit()

        print("[MEDGUARD SEED] Seeding 3 Multi-Storage Units...")
        unit_a = StorageUnit(
            unit_code="UNIT-A-FRIDGE",
            name="Pharmacy Refrigerator A",
            unit_type="refrigerator",
            location="Room 102 - Outpatient Pharmacy",
            default_min_temp=2.0,
            default_max_temp=8.0,
            default_min_humidity=30.0,
            default_max_humidity=65.0,
            power_status=True,
            status="SAFE",
            current_risk_score=12.5,
            door_open_state=False
        )
        unit_b = StorageUnit(
            unit_code="UNIT-B-FREEZER",
            name="Vaccine Ultra Freezer B",
            unit_type="vaccine_freezer",
            location="Immunization Clinic - Ward 3",
            default_min_temp=-25.0,
            default_max_temp=-15.0,
            default_min_humidity=20.0,
            default_max_humidity=60.0,
            power_status=True,
            status="SAFE",
            current_risk_score=8.0,
            door_open_state=False
        )
        unit_c = StorageUnit(
            unit_code="UNIT-C-CABINET",
            name="Controlled Room Storage C",
            unit_type="ambient_cabinet",
            location="Central Medical Warehouse - Bay 4",
            default_min_temp=15.0,
            default_max_temp=25.0,
            default_min_humidity=25.0,
            default_max_humidity=60.0,
            power_status=True,
            status="SAFE",
            current_risk_score=15.0,
            door_open_state=False
        )
        db.add_all([unit_a, unit_b, unit_c])
        db.commit()

        print("[MEDGUARD SEED] Seeding 8 Critical Medicines & Batches...")
        # Medicines for Unit A (2°C - 8°C)
        m1 = Medicine(
            storage_unit_id=unit_a.id,
            medicine_name="Insulin Glargine (Lantus)",
            generic_name="Insulin Glargine",
            category="Biologics / Insulin",
            required_min_temp=2.0,
            required_max_temp=8.0,
            required_min_humidity=30.0,
            required_max_humidity=65.0,
            light_sensitive=True,
            storage_instructions="Store between 2°C and 8°C. Protect from light. Do not freeze."
        )
        m2 = Medicine(
            storage_unit_id=unit_a.id,
            medicine_name="Hepatitis B Recombinant Vaccine",
            generic_name="Hep B Vaccine",
            category="Vaccine",
            required_min_temp=2.0,
            required_max_temp=8.0,
            required_min_humidity=30.0,
            required_max_humidity=70.0,
            light_sensitive=False,
            storage_instructions="Maintain cold chain. Freezing irreversibly destroys potency."
        )
        m3 = Medicine(
            storage_unit_id=unit_a.id,
            medicine_name="Adalimumab (Humira)",
            generic_name="Adalimumab",
            category="Biologics / Monoclonal Antibody",
            required_min_temp=2.0,
            required_max_temp=8.0,
            required_min_humidity=30.0,
            required_max_humidity=60.0,
            light_sensitive=True,
            storage_instructions="Keep prefilled pens in carton to protect from light."
        )
        m4 = Medicine(
            storage_unit_id=unit_a.id,
            medicine_name="Tetanus Toxoid Vaccine",
            generic_name="Tetanus Vaccine",
            category="Vaccine",
            required_min_temp=2.0,
            required_max_temp=8.0,
            required_min_humidity=30.0,
            required_max_humidity=65.0,
            light_sensitive=False,
            storage_instructions="Shake well before use. Do not freeze."
        )

        # Medicines for Unit B (-25°C to -15°C)
        m5 = Medicine(
            storage_unit_id=unit_b.id,
            medicine_name="Varicella Virus Vaccine (Varivax)",
            generic_name="Varicella Live",
            category="Frozen Vaccine",
            required_min_temp=-25.0,
            required_max_temp=-15.0,
            required_min_humidity=20.0,
            required_max_humidity=60.0,
            light_sensitive=True,
            storage_instructions="Store frozen between -25°C and -15°C. Discard if thawed."
        )
        m6 = Medicine(
            storage_unit_id=unit_b.id,
            medicine_name="Zoster Vaccine Live (Zostavax)",
            generic_name="Zoster Live",
            category="Frozen Vaccine",
            required_min_temp=-25.0,
            required_max_temp=-15.0,
            required_min_humidity=20.0,
            required_max_humidity=60.0,
            light_sensitive=True,
            storage_instructions="Keep continuously frozen until reconstitution."
        )

        # Medicines for Unit C (15°C to 25°C)
        m7 = Medicine(
            storage_unit_id=unit_c.id,
            medicine_name="EpiPen (Epinephrine Auto-Injector)",
            generic_name="Epinephrine",
            category="Emergency Injectable",
            required_min_temp=15.0,
            required_max_temp=25.0,
            required_min_humidity=25.0,
            required_max_humidity=60.0,
            light_sensitive=True,
            storage_instructions="Store at 20°C to 25°C. Do not refrigerate. Protect from light."
        )
        m8 = Medicine(
            storage_unit_id=unit_c.id,
            medicine_name="Amoxicillin Oral Suspension",
            generic_name="Amoxicillin",
            category="Antibiotic",
            required_min_temp=15.0,
            required_max_temp=25.0,
            required_min_humidity=25.0,
            required_max_humidity=65.0,
            light_sensitive=False,
            storage_instructions="Store dry powder at room temperature."
        )

        db.add_all([m1, m2, m3, m4, m5, m6, m7, m8])
        db.commit()

        # Seed Batches
        batches = [
            MedicineBatch(medicine_id=m1.id, batch_number="LANT-2026-X8", quantity=80, expiry_date=date(2027, 8, 15), supplier="Sanofi Aventis"),
            MedicineBatch(medicine_id=m1.id, batch_number="LANT-2026-X9", quantity=40, expiry_date=date(2027, 11, 20), supplier="Sanofi Aventis"),
            MedicineBatch(medicine_id=m2.id, batch_number="HEPB-2026-V1", quantity=150, expiry_date=date(2027, 4, 10), supplier="Serum Institute"),
            MedicineBatch(medicine_id=m3.id, batch_number="HUM-2026-A2", quantity=35, expiry_date=date(2026, 12, 31), supplier="AbbVie"),
            MedicineBatch(medicine_id=m4.id, batch_number="TET-2026-T5", quantity=200, expiry_date=date(2028, 1, 1), supplier="Biological E"),
            MedicineBatch(medicine_id=m5.id, batch_number="VAR-2026-F9", quantity=65, expiry_date=date(2027, 6, 15), supplier="Merck & Co"),
            MedicineBatch(medicine_id=m6.id, batch_number="ZOS-2026-Z3", quantity=50, expiry_date=date(2027, 5, 20), supplier="Merck & Co"),
            MedicineBatch(medicine_id=m7.id, batch_number="EPI-2026-E1", quantity=45, expiry_date=date(2027, 9, 30), supplier="Mylan Specialty"),
            MedicineBatch(medicine_id=m8.id, batch_number="AMX-2026-B7", quantity=120, expiry_date=date(2028, 3, 15), supplier="GlaxoSmithKline"),
        ]
        db.add_all(batches)
        db.commit()

        print("[MEDGUARD SEED] Generating 24-hour Historical Sensor Telemetry...")
        now = datetime.utcnow()
        # Seed 30 readings for Unit A
        for i in range(30):
            ts = now - timedelta(minutes=(30 - i) * 5)
            # Gentle fluctuation around 4.2°C
            t = round(4.2 + (i % 5 - 2) * 0.15, 2)
            h = round(48.0 + (i % 4 - 2) * 0.8, 1)
            reading = SensorReading(
                storage_unit_id=unit_a.id,
                temperature=t,
                humidity=h,
                light_lux=12.0,
                door_open=False,
                power_connected=True,
                battery_level=3.3,
                is_offline_sync=False,
                timestamp=ts
            )
            db.add(reading)

        # Seed initial audit log
        audit = AuditLog(
            user_id=admin.id,
            action="SYSTEM_INITIALIZED",
            entity_type="SYSTEM",
            entity_id=1,
            details_json='{"version": "1.0.0", "units_seeded": 3, "medicines_seeded": 8}',
            ip_address="127.0.0.1",
            timestamp=now
        )
        db.add(audit)
        db.commit()
        print("[MEDGUARD SEED] Database successfully populated with initial dataset!")

    except Exception as e:
        db.rollback()
        print(f"[MEDGUARD SEED ERROR] {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed()
