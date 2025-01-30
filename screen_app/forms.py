# forms.py
from django import forms
from .models import (
    InspectionSheet,
    SubGroup,
    MeasurementSample,
    ConcernReport,
    Employee,
    PartNumber
)
from django.utils import timezone


class InspectionSheetForm(forms.ModelForm):
    class Meta:
        model = InspectionSheet
        fields = ['document_date', 'shift', 'line', 'part_number', 'dvis_number']
        widgets = {
            'document_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                    'required': True
                }
            ),
            'shift': forms.Select(
                attrs={
                    'class': 'form-select',
                    'required': True
                }
            ),
            'line': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'required': True,
                    'placeholder': 'Enter Line Number'
                }
            ),
            'part_number': forms.Select(
                attrs={
                    'class': 'form-select',
                    'required': True
                }
            ),
            'dvis_number': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'required': True,
                    'placeholder': 'Enter DVIS Number'
                }
            )
        }

class MeasurementSampleForm(forms.ModelForm):
    class Meta:
        model = MeasurementSample
        exclude = ['subgroup']
        widgets = {
            # Program Selection
            'program_selection': forms.Select(
                attrs={
                    'class': 'form-select',
                    'data-bs-toggle': 'tooltip',
                    'title': 'Select the program model'
                }
            ),
            
            # Measurements
            'line_pressure': forms.NumberInput(
                attrs={
                    'class': 'form-control measurement-input',
                    'step': '0.1',
                    'min': '4.5',
                    'max': '5.5',
                    'data-bs-toggle': 'tooltip',
                    'title': 'Enter pressure between 4.5 and 5.5 bar'
                }
            ),
            'oring_condition': forms.Select(
                attrs={
                    'class': 'form-select',
                    'data-bs-toggle': 'tooltip',
                    'title': 'Select O-ring condition'
                }
            ),
            'uv_flow_test_pressure': forms.NumberInput(
                attrs={
                    'class': 'form-control measurement-input',
                    'step': '0.1',
                    'min': '11',
                    'max': '15',
                    'data-bs-toggle': 'tooltip',
                    'title': 'Enter pressure between 11 and 15 kPA'
                }
            ),
            'uv_vacuum_test': forms.NumberInput(
                attrs={
                    'class': 'form-control measurement-input',
                    'step': '0.1',
                    'min': '-43',
                    'max': '-35',
                    'data-bs-toggle': 'tooltip',
                    'title': 'Enter vacuum test value between -35 and -43 KPa'
                }
            ),
            'uv_flow_value': forms.NumberInput(
                attrs={
                    'class': 'form-control measurement-input',
                    'step': '0.1',
                    'min': '30',
                    'max': '40',
                    'data-bs-toggle': 'tooltip',
                    'title': 'Enter flow value between 30 and 40 LPM'
                }
            ),

            # Verifications
            'lvdt_verification': forms.Select(
                attrs={
                    'class': 'form-select',
                    'data-bs-toggle': 'tooltip',
                    'title': 'Select LVDT verification status'
                }
            ),
            'master_verification': forms.Select(
                attrs={
                    'class': 'form-select',
                    'data-bs-toggle': 'tooltip',
                    'title': 'Select master verification status'
                }
            ),
            'vacuum_test_pressure': forms.NumberInput(
                attrs={
                    'class': 'form-control measurement-input',
                    'step': '0.01',
                    'min': '0.25',
                    'max': '0.3',
                    'data-bs-toggle': 'tooltip',
                    'title': 'Enter vacuum test pressure between 0.25 and 0.3 MPa'
                }
            ),

            # Tool IDs
            'top_tool_id': forms.Select(
                attrs={
                    'class': 'form-select',
                    'data-bs-toggle': 'tooltip',
                    'title': 'Select Top Tool ID'
                }
            ),
            'bottom_tool_id': forms.Select(
                attrs={
                    'class': 'form-select',
                    'data-bs-toggle': 'tooltip',
                    'title': 'Select Bottom Tool ID'
                }
            ),
            'uv_assy_stage_id': forms.Select(
                attrs={
                    'class': 'form-select',
                    'data-bs-toggle': 'tooltip',
                    'title': 'Select UV Assembly Stage ID'
                }
            ),

            # Part Numbers
            'retainer_part_number': forms.Select(
                attrs={
                    'class': 'form-select',
                    'data-bs-toggle': 'tooltip',
                    'title': 'Select Retainer Part Number'
                }
            ),
            'uv_clip_part_number': forms.Select(
                attrs={
                    'class': 'form-select',
                    'data-bs-toggle': 'tooltip',
                    'title': 'Select UV Clip Part Number'
                }
            ),
            'umbrella_part_number': forms.Select(
                attrs={
                    'class': 'form-select',
                    'data-bs-toggle': 'tooltip',
                    'title': 'Select Umbrella Part Number'
                }
            ),

            # Status Checks
            'retainer_lubrication': forms.Select(
                attrs={
                    'class': 'form-select',
                    'data-bs-toggle': 'tooltip',
                    'title': 'Select Retainer Lubrication Status'
                }
            ),
            'uv_clip_pressing': forms.Select(
                attrs={
                    'class': 'form-select',
                    'data-bs-toggle': 'tooltip',
                    'title': 'Select UV Clip Pressing Status'
                }
            ),
            'workstation_clean': forms.Select(
                attrs={
                    'class': 'form-select',
                    'data-bs-toggle': 'tooltip',
                    'title': 'Select Workstation Clean Status'
                }
            ),
            'error_proofing_verified': forms.Select(
                attrs={
                    'class': 'form-select',
                    'data-bs-toggle': 'tooltip',
                    'title': 'Select Error Proofing Verification Status'
                }
            ),
            'contamination_free': forms.Select(
                attrs={
                    'class': 'form-select',
                    'data-bs-toggle': 'tooltip',
                    'title': 'Select Contamination Free Status'
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add any custom field initialization here if needed
        for field in self.fields.values():
            field.required = True


class SubGroupForm(forms.ModelForm):
    group_number = forms.IntegerField(widget=forms.HiddenInput())
    
    class Meta:
        model = SubGroup
        fields = ['group_number', 'operator', 'team_leader', 'supervisor', 'quality_supervisor', 'record_time']
        widgets = {
            'record_time': forms.TimeInput(
                attrs={
                    'type': 'time',
                    'class': 'form-control',
                }
            ),
            'operator': forms.Select(
                attrs={
                    'class': 'form-select',
                }
            ),
            'team_leader': forms.Select(
                attrs={
                    'class': 'form-select',
                }
            ),
            'supervisor': forms.Select(
                attrs={
                    'class': 'form-select',
                }
            ),
            'quality_supervisor': forms.Select(
                attrs={
                    'class': 'form-select',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set current time for new instances
        if not self.instance.pk:
            current_time = timezone.localtime(timezone.now()).time()
            self.initial['record_time'] = current_time
            if 'record_time' in self.fields:
                self.fields['record_time'].initial = current_time
        
        # Get the index from the form prefix
        if self.prefix:
            try:
                index = int(self.prefix.split('-')[1])
                self.initial['group_number'] = index + 1
            except (IndexError, ValueError):
                pass
        
        # If instance already has a group number, use that
        if self.instance.pk and self.instance.group_number:
            self.initial['group_number'] = self.instance.group_number

    def clean(self):
        cleaned_data = super().clean()
        # Ensure record_time is set if not provided
        if not cleaned_data.get('record_time'):
            cleaned_data['record_time'] = timezone.localtime(timezone.now()).time()
        return cleaned_data
            


class ConcernReportForm(forms.ModelForm):
    class Meta:
        model = ConcernReport
        exclude = ['inspection', 'reported_at']
        widgets = {
            'concern_identified': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Describe the concern identified',
                    'required': True
                }
            ),
            'cause': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Describe the cause if known'
                }
            ),
            'action_taken': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Describe the action taken',
                    'required': True
                }
            ),
            'manufacturing_approval': forms.Select(
                attrs={
                    'class': 'form-select',
                    'required': True
                }
            ),
            'quality_approval': forms.Select(
                attrs={
                    'class': 'form-select',
                    'required': True
                }
            )
        }
# Form for multiple samples in a subgroup
MeasurementSampleFormSet = forms.inlineformset_factory(
    SubGroup,
    MeasurementSample,
    form=MeasurementSampleForm,
    extra=5,
    max_num=5,
    min_num=5,
    validate_min=True,
    can_delete=False,
)

# Form for multiple subgroups in an inspection
SubGroupFormSet = forms.inlineformset_factory(
    InspectionSheet,
    SubGroup,
    form=SubGroupForm,
    extra=4,
    max_num=4,
    min_num=4,
    validate_min=True,
    can_delete=False
)
