import pandas as pd
from django.core.management.base import BaseCommand
from django.utils import timezone
from commander.models import Case
from datetime import datetime
import re

class Command(BaseCommand):
    help = 'Import SAPS crime cases from Excel file'

    def handle(self, *args, **kwargs):
        # Read the Excel file
        try:
            df = pd.read_excel('commander/data/mock_saps_crime_data.xlsx')
            self.stdout.write(self.style.SUCCESS(f'Found {len(df)} records in Excel file'))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR('Excel file not found at commander/data/mock_saps_crime_data.xlsx'))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error reading file: {e}'))
            return

        count_created = 0
        count_updated = 0
        count_errors = 0

        # Status mapping
        status_map = {
            'Under Investigation': 'ACTIVE',
            'Open': 'AT_RISK',
            'Closed': 'CASE_CLOSED'
        }

        for index, row in df.iterrows():
            try:
                # Parse CAS number (format: "CAS 143/05/2024" -> "CAS-143-05-2024")
                cas_raw = str(row['CAS_Number']).strip()
                # Convert to clean format
                cas_number = cas_raw.replace(' ', '-').replace('/', '-')
                
                # Get crime category
                crime = str(row['Crime_Category']).strip()
                
                # Map crime categories to your system's choices
                crime_map = {
                    'Robbery': 'Aggravated Robbery',
                    'Theft': 'Theft of Motor Vehicle',
                    'Fraud': 'Other',
                    'Assault': 'Assault GBH',
                    'Burglary': 'Business Robbery'
                }
                crime_category = crime_map.get(crime, 'Other')
                
                # Get status
                status_raw = str(row['Status']).strip()
                status = status_map.get(status_raw, 'ACTIVE')
                
                # Get complainant name
                first_name = str(row['Victim_First_Name']).strip() if pd.notna(row['Victim_First_Name']) else ''
                surname = str(row['Victim_Surname']).strip() if pd.notna(row['Victim_Surname']) else ''
                complainant_name = f"{first_name} {surname}".strip()
                
                # Get ID number
                id_number = str(row['Victim_ID_Number']).strip() if pd.notna(row['Victim_ID_Number']) else ''
                
                # Create or update case
                case, created = Case.objects.update_or_create(
                    case_number=cas_number,
                    defaults={
                        'crime_category': crime_category,
                        'complainant_name': complainant_name,
                        'complainant_id': id_number,
                        'status': status,
                        'reported_date': timezone.now() - timezone.timedelta(days=30),  # Approximate date
                        'last_activity_date': timezone.now() - timezone.timedelta(days=15),
                        'acknowledged': False,
                    }
                )
                
                if created:
                    count_created += 1
                else:
                    count_updated += 1
                    
                if count_created % 20 == 0:
                    self.stdout.write(f'  Imported {count_created} cases...')
                    
            except Exception as e:
                count_errors += 1
                self.stdout.write(self.style.WARNING(f'Error on row {index}: {e}'))

        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS(f'✅ Import complete!'))
        self.stdout.write(self.style.SUCCESS(f'   Created: {count_created} cases'))
        self.stdout.write(self.style.SUCCESS(f'   Updated: {count_updated} cases'))
        self.stdout.write(self.style.SUCCESS(f'   Errors: {count_errors}'))
        self.stdout.write(self.style.SUCCESS('=' * 50))