
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.urls import reverse

class Product(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.code} - {self.name}"

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.core.files import File
import os
import win32com.client
import pythoncom
from PIL import Image
import win32gui
import win32con
import win32api
import time
from django.db import transaction, OperationalError

# models.py
class ProductMedia(models.Model):
    product = models.ForeignKey(Product, related_name='media', on_delete=models.CASCADE)
    file = models.FileField(
        upload_to='product_media/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'mp4', 'mov', 'xlsx', 'xls'])]
    )
    pdf_version = models.FileField(upload_to='product_media/pdf_versions/', null=True, blank=True)
    duration = models.PositiveIntegerField(default=15, blank=True, help_text="Duration in seconds")

    def __str__(self):
        return f"{self.product.code} - {self.file.name}"

    def convert_excel_to_pdf(self):
        if not self.file.name.lower().endswith(('.xlsx', '.xls')):
            return

        try:
            import comtypes.client
            
            # Create PDF path
            pdf_path = os.path.join(
                os.path.dirname(self.file.path),
                f'{os.path.splitext(os.path.basename(self.file.name))[0]}.pdf'
            )

            # Initialize Excel
            excel = comtypes.client.CreateObject('Excel.Application')
            excel.Visible = False
            excel.DisplayAlerts = False

            # Open workbook
            wb = excel.Workbooks.Open(self.file.path)

            # Constants for PDF format
            xlTypePDF = 0
            xlQualityStandard = 0

            # Save as PDF
            wb.ExportAsFixedFormat(Type=xlTypePDF, Filename=pdf_path, Quality=xlQualityStandard)

            # Save to pdf_version field
            with open(pdf_path, 'rb') as pdf_file:
                self.pdf_version.save(
                    os.path.basename(pdf_path),
                    File(pdf_file),
                    save=False
                )

        except Exception as e:
            print(f"Error converting Excel to PDF: {e}")
            import traceback
            traceback.print_exc()

        finally:
            try:
                # Close workbook
                wb.Close(SaveChanges=False)
            except:
                pass

            try:
                # Quit Excel
                excel.Quit()
            except:
                pass

            # Clean up COM objects
            try:
                del wb
                del excel
            except:
                pass

            # Remove temporary PDF
            if 'pdf_path' in locals() and os.path.exists(pdf_path):
                try:
                    os.remove(pdf_path)
                except:
                    pass            
    def save(self, *args, **kwargs):
        max_attempts = 3
        attempt = 0
        
        while attempt < max_attempts:
            try:
                with transaction.atomic():
                    is_new = self.pk is None
                    super().save(*args, **kwargs)
                    
                    if self.file.name.lower().endswith(('.xlsx', '.xls')):
                        self.convert_excel_to_pdf()
                        if self.pdf_version:
                            super().save(*args, **kwargs)
                break  # Success, exit loop
            except OperationalError as e:
                if 'database is locked' in str(e):
                    attempt += 1
                    if attempt < max_attempts:
                        time.sleep(1)  # Wait before retrying
                        continue
                raise  # Re-raise if max attempts reached or different error

    def delete(self, *args, **kwargs):
        if self.pdf_version:
            if os.path.isfile(self.pdf_version.path):
                os.remove(self.pdf_version.path)
        super().delete(*args, **kwargs)
        
                
class Station(models.Model):
    name = models.CharField(max_length=100)
    products = models.ManyToManyField(Product, related_name='stations',blank=True)
    manager = models.ForeignKey(User, on_delete=models.CASCADE,blank=True)
    selected_media = models.ManyToManyField(ProductMedia, related_name='stations', blank=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('station_detail', kwargs={'pk': self.pk})
    
# ----------------------------------------------------------------

# 

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class PartNumber(models.Model):
    delphi_part = models.CharField(max_length=20, unique=True)
    model = models.CharField(max_length=50)
    customer_part = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.model} - {self.delphi_part}"

class Employee(models.Model):
    name = models.CharField(max_length=100)
    employee_id = models.CharField(max_length=20, unique=True)
    role = models.CharField(max_length=50, choices=[
        ('OPERATOR', 'Operator'),
        ('TEAM_LEADER', 'Team Leader'),
        ('SHIFT_SUPERVISOR', 'Shift Supervisor'),
        ('QUALITY_SUPERVISOR', 'Quality Supervisor'),
    ])

    def __str__(self):
        return f"{self.name} ({self.role})"

class SubGroup(models.Model):
    inspection = models.ForeignKey('InspectionSheet', on_delete=models.CASCADE)
    group_number = models.IntegerField(choices=[(1, 'Group 1'), (2, 'Group 2'), (3, 'Group 3'), (4, 'Group 4')])
    record_time = models.TimeField(default=timezone.now, blank=True)
    operator = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name='operated_subgroups')
    team_leader = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name='led_subgroups')
    supervisor = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name='supervised_subgroups')
    quality_supervisor = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name='quality_checked_subgroups')

    class Meta:
        unique_together = ['inspection', 'group_number']

class InspectionSheet(models.Model):
    SHIFT_CHOICES = [
        ('A', 'A Shift'),
        ('B', 'B Shift'),
        ('C', 'C Shift'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('complete', 'Complete'),
        ('rejected', 'Rejected')
    ]

    # Basic information
    document_date = models.DateField()
    shift = models.CharField(max_length=1, choices=SHIFT_CHOICES)
    line = models.CharField(max_length=50)
    part_number = models.ForeignKey(PartNumber, on_delete=models.PROTECT)
    dvis_number = models.CharField(max_length=50)
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Current status of the inspection",
        null=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True,null=True)
    # updated_at = models.DateTimeField(auto_now=True,null=True)
    created_at = models.DateTimeField(null=True,auto_now=True)  # Remove auto_now_add
    inspection_time = models.DateTimeField(null=True,auto_now=True)  # Add new field for explicit time control

    def __str__(self):
        return f"Inspection {self.dvis_number} - {self.document_date}"
    
    
    @property
    def is_day_shift(self):
        """Return True if the inspection is during day shift (08:00-20:00)"""
        if self.created_at:
            hour = self.created_at.hour
            return 8 <= hour < 20
        return False

    @property
    def shift_time(self):
        """
        Get the actual time period for the shift
        """
        if self.shift == 'A':
            return "06:00 - 14:00"
        elif self.shift == 'B':
            return "14:00 - 22:00"
        elif self.shift == 'C':
            return "22:00 - 06:00"
        return None

    def get_time_block(self):
        """
        Get the 2-hour time block this inspection belongs to
        """
        if self.created_at:
            hour = self.created_at.hour
            block_start = (hour // 2) * 2
            return f"{block_start:02d}:00 - {(block_start + 2):02d}:00"
        return None
    
    class Meta:
        ordering = ['-document_date', '-created_at']
        indexes = [
            models.Index(fields=['document_date', 'shift']),
            models.Index(fields=['status']),
        ]
        
class MeasurementSample(models.Model):
    PROGRAM_CHOICES = [
        ('P703', 'P703'),
        ('U704', 'U704'),
        ('FD', 'FD'),
        ('SA', 'SA'),
        ('Gnome', 'Gnome')
    ]
    
    STATUS_CHOICES = [
        ('OK', 'OK'),
        ('NG', 'NG')
    ]
    
    YES_NO_CHOICES = [
        ('YES', 'Yes'),
        ('NO', 'No')
    ]

    TOOL_ID_CHOICES = [
        ('FMA-03-35-T05', 'FMA-03-35-T05 (P703/U704/SA/FD/Gnome)'),
        ('FMA-03-35-T06', 'FMA-03-35-T06 (P703/U704/SA/FD)'),
        ('FMA-03-35-T08', 'FMA-03-35-T08 (Gnome)'),
    ]

    UV_ASSY_CHOICES = [
        ('FMA-03-35-T07', 'FMA-03-35-T07 (P703/U704/SA/FD)'),
        ('FMA-03-35-T09', 'FMA-03-35-T09 (Gnome)'),
    ]

    RETAINER_PART_CHOICES = [
        ('42001878', '42001878 (P703/U704/SA/FD)'),
        ('42050758', '42050758 (Gnome)'),
    ]

    UV_CLIP_PART_CHOICES = [
        ('42000829', '42000829 (P703/U704/SA/FD)'),
        ('42000829', '42000829 (Gnome)'),
    ]

    UMBRELLA_PART_CHOICES = [
        ('25094588', '25094588 (P703/U704/SA/FD/Gnome)'),
    ]

    # Base fields (keep these the same)
    subgroup = models.ForeignKey(SubGroup, on_delete=models.CASCADE)
    sample_number = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    # Program Selection
    program_selection = models.CharField(
        max_length=10,
        choices=PROGRAM_CHOICES
    )
    
    # Measurements (keep these the same)
    line_pressure = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(4.5), MaxValueValidator(5.5)],
        help_text="Line pressure (4.5 - 5.5 bar)"
    )
    
    oring_condition = models.CharField(
        max_length=2,
        choices=STATUS_CHOICES
    )
    
    uv_flow_test_pressure = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(11), MaxValueValidator(15)],
        help_text="UV Flow input Test Pressure (11-15 kPA)"
    )
    
    uv_vacuum_test = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(-43), MaxValueValidator(-35)],
        help_text="UV Vacuum Test range (-35 to -43 KPa)"
    )
    
    uv_flow_value = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(30), MaxValueValidator(40)],
        help_text="UV Flow Value (30~40 LPM)"
    )
    
    # Verifications
    lvdt_verification = models.CharField(
        max_length=2,
        choices=STATUS_CHOICES
    )
    
    master_verification = models.CharField(
        max_length=2,
        choices=STATUS_CHOICES
    )
    
    vacuum_test_pressure = models.DecimalField(
        max_digits=4,
        decimal_places=3,
        validators=[MinValueValidator(0.25), MaxValueValidator(0.3)],
        help_text="Test Pressure for Vacuum generation (0.25 ~ 0.3 Mpa)"
    )
    
    # Tool information
    top_tool_id = models.CharField(
        max_length=150,
        choices=TOOL_ID_CHOICES,
        help_text="Select Top Tool ID"
    )
    
    bottom_tool_id = models.CharField(
        max_length=150,
        choices=TOOL_ID_CHOICES,
        help_text="Select Bottom Tool ID"
    )
    
    uv_assy_stage_id = models.CharField(
        max_length=80,
        choices=UV_ASSY_CHOICES,
        help_text="Select UV Assembly Stage ID"
    )
    
    # Part Numbers
    retainer_part_number = models.CharField(
        max_length=90,
        choices=RETAINER_PART_CHOICES,
        help_text="Select Retainer Part Number"
    )

    # Adding the missing fields
# Adding these fields with default values
    uv_clip_part_number = models.CharField(
        max_length=90,
        choices=UV_CLIP_PART_CHOICES,
        help_text="Select UV Clip Part Number",
        default='42000829'  # Adding default value
    )

    umbrella_part_number = models.CharField(
        max_length=90,
        choices=UMBRELLA_PART_CHOICES,
        help_text="Select Umbrella Part Number",
        default='25094588'  # Adding default value
    )

    retainer_lubrication = models.CharField(
        max_length=2,
        choices=STATUS_CHOICES,
        help_text="Retainer ID lubrication status",
        default='OK'  # Adding default value
    )

    uv_clip_pressing = models.CharField(
        max_length=2,
        choices=STATUS_CHOICES,
        help_text="UV Clip pressing status",
        default='OK'  # Adding default value
    )    
    # Status fields
    workstation_clean = models.CharField(
        max_length=3,
        choices=YES_NO_CHOICES
    )
    
    error_proofing_verified = models.CharField(
        max_length=3,
        choices=YES_NO_CHOICES
    )
    
    contamination_free = models.CharField(
        max_length=3,
        choices=YES_NO_CHOICES
    )

    class Meta:
        unique_together = ['subgroup', 'sample_number']
        ordering = ['sample_number']
        
class ConcernReport(models.Model):
    inspection = models.ForeignKey(InspectionSheet, on_delete=models.CASCADE)
    concern_identified = models.TextField()
    cause = models.TextField(blank=True)
    action_taken = models.TextField()
    manufacturing_approval = models.ForeignKey(
        Employee, 
        on_delete=models.PROTECT, 
        related_name='manufacturing_approvals',
        null=True,
        blank=True
    )
    quality_approval = models.ForeignKey(
        Employee, 
        on_delete=models.PROTECT,
        related_name='quality_approvals',
        null=True,
        blank=True
    )
    reported_at = models.DateTimeField(auto_now_add=True)