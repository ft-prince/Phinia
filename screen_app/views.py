from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Station, ProductMedia
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.db import transaction
from .forms import InspectionSheetForm, SubGroupFormSet, MeasurementSampleFormSet

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Count
from django.db.models.functions import ExtractHour  # Correct import for ExtractHour
def get_station_media(request, station_id):
    station = get_object_or_404(Station, pk=station_id)
    selected_media = station.selected_media.all()
    
    media_data = []
    for m in selected_media:
        media_type = m.file.name.split('.')[-1].lower()
        media_info = {
            'id': m.id,
            'url': m.file.url,
            'type': media_type,
            'duration': m.duration,
            'product_name': m.product.name,
            'product_code': m.product.code
        }
        
        # If it's an Excel file and has a PDF version, use that instead
        if media_type in ['xlsx', 'xls'] and m.pdf_version:
            media_info['url'] = m.pdf_version.url
            media_info['type'] = 'pdf'
        
        media_data.append(media_info)
    
    return JsonResponse({'media': media_data})


def station_media_slider(request, station_id):
    station = get_object_or_404(Station, pk=station_id)
    # Use the related_name from the M2M field
    selected_media = station.selected_media.all()
    return render(request, 'station_slider.html', {'station': station, 'selected_media': selected_media})






# ----------------------------------------------------------------
# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from .models import (
    InspectionSheet, 
    SubGroup, 
    MeasurementSample, 
    ConcernReport,
    Employee,
    PartNumber
)
from .forms import (
    InspectionSheetForm,
    SubGroupFormSet,
    MeasurementSampleFormSet,
    ConcernReportForm
)

# views.py
from django.views.generic.list import ListView
from django.db.models.functions import TruncHour

from django.utils import timezone

# views.py
from django.shortcuts import render
from django.utils import timezone
from django.views.generic import ListView
from .models import InspectionSheet

# views.py
from django.views.generic import ListView
from django.utils import timezone
from datetime import datetime, time, timedelta
from django.db.models import Count
from django.db.models.functions import ExtractHour

class InspectionListView(ListView):
    model = InspectionSheet
    template_name = 'inspection/inspection_list.html'
    context_object_name = 'inspections'
    ordering = ['-document_date', '-created_at']
    paginate_by = 40

    def get_time_block(self, hour):
        """Convert hour to time block label"""
        if hour is None:
            return "Unknown"
        
        try:
            hour = int(hour)
        except (ValueError, TypeError):
            return "Unknown"

        blocks = {
            8: "08:00 - 10:00",
            10: "10:00 - 12:00",
            12: "12:00 - 14:00",
            14: "14:00 - 16:00",
            16: "16:00 - 18:00",
            18: "18:00 - 20:00",
            20: "20:00 - 22:00",
            22: "22:00 - 00:00",
            0: "00:00 - 02:00",
            2: "02:00 - 04:00",
            4: "04:00 - 06:00",
            6: "06:00 - 08:00"
        }
        return blocks.get(hour, "Unknown")
    def get_queryset(self):
        queryset = super().get_queryset()

        # Get filter parameters
        shift = self.request.GET.get('shift')
        status = self.request.GET.get('status')
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        search = self.request.GET.get('search')
        time_block = self.request.GET.get('time_block')

        # Apply filters
        if shift:
            if shift == 'DAY':
                queryset = queryset.filter(created_at__hour__gte=8, created_at__hour__lt=20)
            elif shift == 'NIGHT':
                queryset = queryset.filter(
                    created_at__hour__lt=8) | queryset.filter(created_at__hour__gte=20)

        if status:
            queryset = queryset.filter(status=status)
        if start_date:
            queryset = queryset.filter(document_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(document_date__lte=end_date)
        if search:
            queryset = queryset.filter(dvis_number__icontains=search)

        if time_block:
            hour = int(time_block.split(':')[0])
            queryset = queryset.filter(
                created_at__hour__gte=hour,
                created_at__hour__lt=(hour + 2)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.localtime(timezone.now())
        today = now.date()
        current_hour = now.hour

        # Initialize all time blocks with zero counts
        day_blocks = {
            "08:00 - 10:00": 0,
            "10:00 - 12:00": 0,
            "12:00 - 14:00": 0,
            "14:00 - 16:00": 0,
            "16:00 - 18:00": 0,
            "18:00 - 20:00": 0
        }
        
        night_blocks = {
            "20:00 - 22:00": 0,
            "22:00 - 00:00": 0,
            "00:00 - 02:00": 0,
            "02:00 - 04:00": 0,
            "04:00 - 06:00": 0,
            "06:00 - 08:00": 0
        }

        # Determine current shift
        is_day_shift = 8 <= current_hour < 20
        current_shift = 'Day Shift' if is_day_shift else 'Night Shift'

        # Get current 2-hour block
        block_start = (current_hour // 2) * 2
        current_block = self.get_time_block(block_start)

        # Get today's inspections
        today_qs = InspectionSheet.objects.filter(document_date=today)

        # Get all inspections for today and annotate them with the hour
        inspections = today_qs.annotate(
            hour=ExtractHour('created_at')
        ).values('hour').annotate(
            count=Count('id')
        ).order_by('hour')

        # Process each inspection to put it in the correct time block
        for inspection in inspections:
            hour = inspection['hour']
            count = inspection['count']
            
            if hour is not None:
                if 8 <= hour < 10:
                    day_blocks["08:00 - 10:00"] += count
                elif 10 <= hour < 12:
                    day_blocks["10:00 - 12:00"] += count
                elif 12 <= hour < 14:
                    day_blocks["12:00 - 14:00"] += count
                elif 14 <= hour < 16:
                    day_blocks["14:00 - 16:00"] += count
                elif 16 <= hour < 18:
                    day_blocks["16:00 - 18:00"] += count
                elif 18 <= hour < 20:
                    day_blocks["18:00 - 20:00"] += count
                elif 20 <= hour < 22:
                    night_blocks["20:00 - 22:00"] += count
                elif 22 <= hour < 24:
                    night_blocks["22:00 - 00:00"] += count
                elif 0 <= hour < 2:
                    night_blocks["00:00 - 02:00"] += count
                elif 2 <= hour < 4:
                    night_blocks["02:00 - 04:00"] += count
                elif 4 <= hour < 6:
                    night_blocks["04:00 - 06:00"] += count
                elif 6 <= hour < 8:
                    night_blocks["06:00 - 08:00"] += count

        # Get current shift statistics
        if is_day_shift:
            shift_qs = today_qs.filter(created_at__hour__gte=8, created_at__hour__lt=20)
        else:
            shift_qs = today_qs.filter(
                Q(created_at__hour__lt=8) | Q(created_at__hour__gte=20)
            )

        # Get current block statistics
        block_qs = today_qs.filter(
            created_at__hour__gte=block_start,
            created_at__hour__lt=block_start + 2
        )

        # Convert to list format for template
        day_shift_stats = [
            {'time_block': block, 'count': count}
            for block, count in day_blocks.items()
        ]
        
        night_shift_stats = [
            {'time_block': block, 'count': count}
            for block, count in night_blocks.items()
        ]

        context.update({
            'total_inspections': InspectionSheet.objects.count(),
            'today_inspections': today_qs.count(),
            'shift_inspections': shift_qs.count(),
            'block_inspections': block_qs.count(),
            'current_shift': current_shift,
            'current_block': current_block,
            'day_shift_stats': day_shift_stats,
            'night_shift_stats': night_shift_stats,
        })

        return context    
        
    
from django.views.generic import DetailView
from django.http import HttpResponse
from django.template.loader import render_to_string
import xlsxwriter
from io import BytesIO
from datetime import datetime
from django.urls import path
from django.utils.text import slugify

class InspectionDetailView(DetailView):
    model = InspectionSheet
    template_name = 'inspection/inspection_detail.html'
    context_object_name = 'inspection'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['concern_reports'] = self.object.concernreport_set.all().select_related(
            'manufacturing_approval',
            'quality_approval'
        )
        context['employees'] = Employee.objects.all()
        
        # Get measurement statistics
        for subgroup in self.object.subgroup_set.all():
            samples = subgroup.measurementsample_set.all()
            subgroup.stats = {
                'avg_line_pressure': sum(s.line_pressure for s in samples) / len(samples),
                'avg_uv_flow': sum(s.uv_flow_value for s in samples) / len(samples),
                'avg_vacuum': sum(s.uv_vacuum_test for s in samples) / len(samples)
            }
        
        return context

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        # Handle export requests
        if 'export' in request.GET:
            export_type = request.GET.get('export')
            if export_type == 'excel':
                return self.export_excel()
            elif export_type == 'print':
                context['print_view'] = True
                return self.render_print_view(context)

        return self.render_to_response(context)

    def export_excel(self):
        try:
            output = BytesIO()
            workbook = xlsxwriter.Workbook(output)
            
            # Add formats
            title_format = workbook.add_format({
                'bold': True,
                'font_size': 14,
                'bg_color': '#1F4E78',
                'font_color': 'white',
                'border': 2,
                'align': 'center',
                'valign': 'vcenter',
                'text_wrap': True,
                'border_color': '#162F4C'
            })
            
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#2E75B6',
                'font_color': 'white',
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'text_wrap': True,
                'font_size': 11
            })
            
            subheader_format = workbook.add_format({
                'bold': True,
                'bg_color': '#9BC2E6',
                'font_color': '#1F4E78',
                'border': 1,
                'align': 'center',
                'text_wrap': True,
                'font_size': 10
            })
            
            param_format = workbook.add_format({
                'border': 1,
                'text_wrap': True,
                'valign': 'vcenter',
                'bg_color': '#F2F2F2',
                'font_size': 10,
                'indent': 1
            })
            
            param_format_alt = workbook.add_format({
                'border': 1,
                'text_wrap': True,
                'valign': 'vcenter',
                'bg_color': '#FFFFFF',
                'font_size': 10,
                'indent': 1
            })
            
            data_format = workbook.add_format({
                'border': 1,
                'align': 'center',
                'bg_color': '#F2F2F2',
                'font_size': 10
            })
            
            data_format_alt = workbook.add_format({
                'border': 1,
                'align': 'center',
                'bg_color': '#FFFFFF',
                'font_size': 10
            })

            # Format for OK/NG values
            ok_format = workbook.add_format({
                'border': 1,
                'align': 'center',
                'bg_color': '#C6EFCE',
                'font_color': '#006100',
                'font_size': 10,
                'bold': True
            })

            ng_format = workbook.add_format({
                'border': 1,
                'align': 'center',
                'bg_color': '#FFC7CE',
                'font_color': '#9C0006',
                'font_size': 10,
                'bold': True
            })

            # Personnel information format
            personnel_format = workbook.add_format({
                'border': 1,
                'align': 'left',
                'valign': 'vcenter',
                'bg_color': '#E2EFDA',
                'text_wrap': True,
                'font_size': 10,
                'indent': 1
            })

            # Create main worksheet
            worksheet = workbook.add_worksheet('Inspection Data')
            
            # Set column widths
            worksheet.set_column('A:A', 45)  # Parameter column
            worksheet.set_column('B:U', 15)  # Data columns
            worksheet.set_default_row(20)  # Default row height
            
            # Write document info with enhanced header
            row = 0
            worksheet.set_row(row, 30)  # Taller header row
            title_text = f'Inspection Report - DVIS#{self.object.dvis_number}'
            worksheet.merge_range('A1:U1', title_text, title_format)
            row += 1
            
            # Info row with better formatting
            worksheet.set_row(row, 25)
            info_format = workbook.add_format({
                'border': 1,
                'align': 'left',
                'bg_color': '#D9E1F2',
                'font_size': 10,
                'indent': 1
            })
            date_str = self.object.document_date.strftime('%d-%b-%Y')
            info_text = f'Date: {date_str}   |   Line: {self.object.line}   |   Part Number: {str(self.object.part_number)}'
            worksheet.merge_range(row, 0, row, 19, info_text, info_format)
            row += 2

            # Write subgroup headers
            col = 1
            for subgroup in self.object.subgroup_set.all():
                worksheet.merge_range(row, col, row, col + 4, f'Sub Group {subgroup.group_number}', header_format)
                
                # Record time
                worksheet.write(row + 1, col, 'Record Time:', subheader_format)
                time_str = subgroup.record_time.strftime('%H:%M') if subgroup.record_time else ''
                worksheet.merge_range(row + 1, col + 1, row + 1, col + 4, time_str, subheader_format)
                
                # Personnel information
                personnel_text = (
                    f'Operator: {subgroup.operator.name}\n'
                    f'Team Leader: {subgroup.team_leader.name}\n'
                    f'Supervisor: {subgroup.supervisor.name}\n'
                    f'Quality Supervisor: {subgroup.quality_supervisor.name}'
                )
                worksheet.merge_range(row + 2, col, row + 2, col + 4, personnel_text, personnel_format)
                
                # Sample numbers
                worksheet.write_row(row + 3, col, ['1', '2', '3', '4', '5'], subheader_format)
                col += 5
            row += 5

            # Parameters and their corresponding methods
            parameters = [
                ('Program Selection on HMI (HMI से Program select करना है)', 'program_selection', None, None, True),
                ('Line Pressure (4.5-5.5 bar)', 'line_pressure', 4.5, 5.5, False),
                ('O-ring Condition', 'oring_condition', None, None, True),
                ('UV Flow Test (11-15 kPA)', 'uv_flow_test_pressure', 11, 15, False),
                ('UV Vacuum Test (-35 to -43 KPa)', 'uv_vacuum_test', -43, -35, False),
                ('UV Flow Value (30-40 LPM)', 'uv_flow_value', 30, 40, False),
                ('LVDT Verification', 'lvdt_verification', None, None, True),
                ('Master Verification', 'master_verification', None, None, True),
                ('Vacuum Test Pressure (0.25-0.3 MPa)', 'vacuum_test_pressure', 0.25, 0.3, False),
                ('Top Tool ID', 'top_tool_id', None, None, True),
                ('Bottom Tool ID', 'bottom_tool_id', None, None, True),
                ('UV Assy Stage ID', 'uv_assy_stage_id', None, None, True),
                ('Retainer Part Number', 'retainer_part_number', None, None, True),
                ('UV Clip Part Number', 'uv_clip_part_number', None, None, True),
                ('Umbrella Part Number', 'umbrella_part_number', None, None, True),
                ('Retainer Lubrication', 'retainer_lubrication', None, None, True),
                ('UV Clip Pressing', 'uv_clip_pressing', None, None, True),
                ('Workstation Clean', 'workstation_clean', None, None, True),
                ('Error Proofing Verified', 'error_proofing_verified', None, None, True),
                ('Contamination Free', 'contamination_free', None, None, True),
            ]

            # Write parameters and values
            for index, (param_name, attr, min_val, max_val, is_choice) in enumerate(parameters):
                current_bg_color = '#F2F2F2' if index % 2 == 0 else '#FFFFFF'
                current_param_format = param_format if index % 2 == 0 else param_format_alt
                current_data_format = data_format if index % 2 == 0 else data_format_alt

                worksheet.write(row, 0, param_name, current_param_format)
                col = 1

                # Special format for long text fields
                long_text_format = workbook.add_format({
                    'border': 1,
                    'align': 'left',
                    'text_wrap': True,
                    'valign': 'vcenter',
                    'bg_color': current_bg_color,
                    'font_size': 9,
                    'indent': 1
                })

                # Determine if this is a long text field
                is_long_text = attr in ['top_tool_id', 'bottom_tool_id', 'uv_assy_stage_id', 
                                    'retainer_part_number', 'uv_clip_part_number', 'umbrella_part_number']

                # Set larger row height for long text fields
                if is_long_text:
                    worksheet.set_row(row, 35)

                for subgroup in self.object.subgroup_set.all():
                    samples = subgroup.measurementsample_set.all()
                    
                    for sample in samples:
                        try:
                            if attr.startswith('get_'):
                                value = getattr(sample, attr)()
                            else:
                                value = getattr(sample, attr)
                                if callable(value):
                                    value = value()

                            # Choose format based on field type
                            if is_long_text:
                                format_to_use = long_text_format
                            elif is_choice:
                                format_to_use = ok_format if str(value).upper() in ['OK', 'YES'] else \
                                            ng_format if str(value).upper() in ['NG', 'NO'] else \
                                            current_data_format
                            else:
                                if min_val is not None and max_val is not None:
                                    try:
                                        num_value = float(value)
                                        format_to_use = ok_format if min_val <= num_value <= max_val else ng_format
                                    except (ValueError, TypeError):
                                        format_to_use = current_data_format
                                else:
                                    format_to_use = current_data_format

                            worksheet.write(row, col, str(value), format_to_use)
                        except (AttributeError, TypeError) as e:
                            worksheet.write(row, col, "N/A", current_data_format)
                        col += 1
                
                row += 1

            # Add signature rows at the bottom
            row += 2
            signature_format = workbook.add_format({
                'bottom': 1,
                'align': 'center',
                'font_size': 10
            })
            
            label_format = workbook.add_format({
                'align': 'center',
                'font_size': 9,
                'font_color': '#666666'
            })

            # Add signature lines
            signatures = ['Operator', 'Team Leader', 'Supervisor', 'Quality Supervisor']
            col = 2
            for sig in signatures:
                worksheet.write(row, col, '', signature_format)
                worksheet.write(row + 1, col, sig, label_format)
                worksheet.merge_range(row, col + 1, row, col + 3, '', signature_format)
                col += 5

            workbook.close()
            output.seek(0)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'inspection_{self.object.dvis_number}_{timestamp}.xlsx'
            
            response = HttpResponse(
                output,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
        except Exception as e:
            print(f"Error in export_excel: {str(e)}")
            raise     
        
        
     
     
     
     
     
      
    
def inspection_create(request):
    if request.method == 'POST':
        post_data = request.POST.copy()  # Make POST data mutable
        
        # Set group numbers
        for i in range(4):
            post_data[f'subgroup_set-{i}-group_number'] = i + 1
        
        form = InspectionSheetForm(post_data)
        subgroup_formset = SubGroupFormSet(post_data)
        
        if form.is_valid() and subgroup_formset.is_valid():
            try:
                with transaction.atomic():
                    # Save main form
                    inspection = form.save()
                    
                    # Save subgroups
                    subgroups = subgroup_formset.save(commit=False)
                    for i, subgroup in enumerate(subgroups):
                        subgroup.inspection = inspection
                        subgroup.group_number = i + 1
                        subgroup.save()
                        
                        # Get values from first sample for this subgroup
                        prefix = f'measurements_{i+1}'
                        tool_info = {
                            'top_tool_id': post_data.get(f'{prefix}-0-top_tool_id', ''),
                            'bottom_tool_id': post_data.get(f'{prefix}-0-bottom_tool_id', ''),
                            'uv_assy_stage_id': post_data.get(f'{prefix}-0-uv_assy_stage_id', ''),
                            'retainer_part_number': post_data.get(f'{prefix}-0-retainer_part_number', ''),
                            'uv_clip_part_number': post_data.get(f'{prefix}-0-uv_clip_part_number', ''),
                            'umbrella_part_number': post_data.get(f'{prefix}-0-umbrella_part_number', '')
                        }
                        
                        # Set default values and copy tools to all samples
                        for j in range(5):  # 5 samples per subgroup
                            # Set sample number
                            post_data[f'{prefix}-{j}-sample_number'] = j + 1
                            
                            # Copy tool and part info from first sample
                            if j > 0:  # Skip first sample as it's the source
                                for field, value in tool_info.items():
                                    if value:  # Only copy if value exists
                                        post_data[f'{prefix}-{j}-{field}'] = value
                            
                            # Set default values for status fields
                            post_data.setdefault(f'{prefix}-{j}-workstation_clean', 'YES')
                            post_data.setdefault(f'{prefix}-{j}-error_proofing_verified', 'YES')
                            post_data.setdefault(f'{prefix}-{j}-contamination_free', 'YES')
                            post_data.setdefault(f'{prefix}-{j}-retainer_lubrication', 'OK')
                            post_data.setdefault(f'{prefix}-{j}-uv_clip_pressing', 'OK')
                            post_data.setdefault(f'{prefix}-{j}-lvdt_verification', 'OK')
                            post_data.setdefault(f'{prefix}-{j}-master_verification', 'OK')

                        # Create measurement formset with updated data
                        measurement_formset = MeasurementSampleFormSet(
                            post_data,
                            instance=subgroup,
                            prefix=prefix
                        )
                        
                        if measurement_formset.is_valid():
                            measurements = measurement_formset.save(commit=False)
                            for measurement in measurements:
                                measurement.save()
                        else:
                            print(f"Measurement formset errors for subgroup {i+1}:", measurement_formset.errors)
                            raise ValueError(f'Invalid measurement data for subgroup {i+1}')

                    messages.success(request, 'Inspection sheet created successfully.')
                    return redirect('inspection_detail', pk=inspection.pk)
                    
            except Exception as e:
                messages.error(request, f'Error creating inspection sheet: {str(e)}')
                print("Exception during save:", str(e))
                import traceback
                traceback.print_exc()
        else:
            if not form.is_valid():
                print("Form errors:", form.errors)
            if not subgroup_formset.is_valid():
                print("Subgroup formset errors:", subgroup_formset.errors)
            messages.error(request, 'Please correct the errors below.')
    
    else:
        form = InspectionSheetForm()
        subgroup_formset = SubGroupFormSet()
        
        # Initialize measurement formsets
        for i, subgroup_form in enumerate(subgroup_formset, 1):
            subgroup_form.initial['group_number'] = i
            measurement_formset = MeasurementSampleFormSet(
                prefix=f'measurements_{i}',
                initial=[{'sample_number': j} for j in range(1, 6)]  # Initialize 5 samples
            )
            subgroup_form.measurement_formset = measurement_formset

    context = {
        'form': form,
        'subgroup_formset': subgroup_formset,
        'employees': Employee.objects.all().order_by('role', 'name'),
        'part_numbers': PartNumber.objects.all()
    }
    
    return render(request, 'inspection/inspection_form.html', context)

def inspection_edit(request, pk):
    inspection = get_object_or_404(InspectionSheet, pk=pk)
    
    if request.method == 'POST':
        form = InspectionSheetForm(request.POST, instance=inspection)
        subgroup_formset = SubGroupFormSet(request.POST, instance=inspection)
        
        print("Main form valid:", form.is_valid())
        print("Subgroup formset valid:", subgroup_formset.is_valid())
        
        if form.is_valid() and subgroup_formset.is_valid():
            try:
                with transaction.atomic():
                    # Save main form
                    inspection = form.save()
                    
                    # Save subgroups
                    subgroups = subgroup_formset.save(commit=False)
                    for i, subgroup in enumerate(subgroups):
                        subgroup.group_number = i + 1
                        subgroup.inspection = inspection
                        subgroup.save()
                    
                    # Process measurement samples
                    for subgroup in inspection.subgroup_set.all():
                        post_data = request.POST.copy()
                        
                        # Get values from the first sample
                        prefix = f'measurements_{subgroup.id}-0'
                        tool_info = {
                            'top_tool_id': post_data.get(f'{prefix}-top_tool_id', ''),
                            'bottom_tool_id': post_data.get(f'{prefix}-bottom_tool_id', ''),
                            'uv_assy_stage_id': post_data.get(f'{prefix}-uv_assy_stage_id', ''),
                            'retainer_part_number': post_data.get(f'{prefix}-retainer_part_number', ''),
                            'uv_clip_part_number': post_data.get(f'{prefix}-uv_clip_part_number', ''),
                            'umbrella_part_number': post_data.get(f'{prefix}-umbrella_part_number', '')
                        }
                        
                        # Copy values to other samples
                        for i in range(1, 5):
                            other_prefix = f'measurements_{subgroup.id}-{i}'
                            for field, value in tool_info.items():
                                if value:  # Only copy if value exists
                                    post_data[f'{other_prefix}-{field}'] = value
                        
                        measurement_formset = MeasurementSampleFormSet(
                            post_data,
                            instance=subgroup,
                            prefix=f'measurements_{subgroup.id}'
                        )
                        
                        print(f"Processing measurements for subgroup {subgroup.id}")
                        if measurement_formset.is_valid():
                            measurements = measurement_formset.save(commit=False)
                            for i, measurement in enumerate(measurements, start=1):
                                measurement.sample_number = i
                                measurement.subgroup = subgroup
                                
                                # Set default values for status fields
                                for field in ['retainer_lubrication', 'uv_clip_pressing']:
                                    if not getattr(measurement, field):
                                        setattr(measurement, field, 'OK')
                                        
                                for field in ['workstation_clean', 'error_proofing_verified', 'contamination_free']:
                                    if not getattr(measurement, field):
                                        setattr(measurement, field, 'YES')
                                
                                measurement.save()
                        else:
                            print(f"Measurement formset errors for subgroup {subgroup.id}:", measurement_formset.errors)
                            raise ValueError(f'Invalid measurement data for subgroup {subgroup.id}')

                    messages.success(request, 'Inspection sheet updated successfully.')
                    return redirect('inspection_detail', pk=inspection.pk)
                    
            except Exception as e:
                messages.error(request, f'Error updating inspection sheet: {str(e)}')
                print("Exception during save:", str(e))
                import traceback
                traceback.print_exc()
    else:
        form = InspectionSheetForm(instance=inspection)
        subgroup_formset = SubGroupFormSet(instance=inspection)
        
        # Initialize measurement formsets
        for subgroup_form in subgroup_formset:
            subgroup = subgroup_form.instance
            if subgroup.id:
                measurement_formset = MeasurementSampleFormSet(
                    instance=subgroup,
                    prefix=f'measurements_{subgroup.id}'
                )
                subgroup_form.instance.measurement_formset = measurement_formset

    return render(request, 'inspection/inspection_edit.html', {
        'form': form,
        'subgroup_formset': subgroup_formset,
        'inspection': inspection,
    })




def inspection_delete(request, pk):
    inspection = get_object_or_404(InspectionSheet, pk=pk)
    try:
        if request.method == 'POST':
            with transaction.atomic():
                inspection.delete()
                messages.success(request, 'Inspection sheet deleted successfully.')
                return redirect('inspection_list')
    except Exception as e:
        messages.error(request, f'Error deleting inspection: {str(e)}')
        return redirect('inspection_detail', pk=pk)
        
    return render(request, 'inspection/inspection_confirm_delete.html', {
        'inspection': inspection
    })

class ConcernReportDetailView(DetailView):
    model = ConcernReport
    template_name = 'inspection/concern_report_detail.html'
    context_object_name = 'concern_report'

def concern_report_create(request, inspection_pk):
    inspection = get_object_or_404(InspectionSheet, pk=inspection_pk)
    
    if request.method == 'POST':
        form = ConcernReportForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    concern_report = form.save(commit=False)
                    concern_report.inspection = inspection
                    concern_report.save()
                    messages.success(request, 'Concern report added successfully.')
                    return redirect('inspection_detail', pk=inspection_pk)
            except Exception as e:
                messages.error(request, f'Error creating concern report: {str(e)}')
    else:
        form = ConcernReportForm()
    
    return render(request, 'inspection/concern_report_form.html', {
        'form': form,
        'inspection': inspection,
        'employees': Employee.objects.all()
    })

# AJAX views for dynamic form handling
# views.py
from django.http import JsonResponse

def get_tool_ids(request):
    model = request.GET.get('model')
    if not model:
        return JsonResponse({'error': 'Model parameter is required'}, status=400)

    tool_ids = {
        'P703': {
            'top_tool_id': 'FMA-03-35-T05',
            'bottom_tool_id': 'FMA-03-35-T06',
            'uv_assy_stage_id': 'FMA-03-35-T07',
        },
        'U704': {
            'top_tool_id': 'FMA-03-35-T05',
            'bottom_tool_id': 'FMA-03-35-T06',
            'uv_assy_stage_id': 'FMA-03-35-T07',
        },
        'FD': {
            'top_tool_id': 'FMA-03-35-T05',
            'bottom_tool_id': 'FMA-03-35-T06',
            'uv_assy_stage_id': 'FMA-03-35-T07',
        },
        'SA': {
            'top_tool_id': 'FMA-03-35-T05',
            'bottom_tool_id': 'FMA-03-35-T06',
            'uv_assy_stage_id': 'FMA-03-35-T07',
        },
        'Gnome': {
            'top_tool_id': 'FMA-03-35-T05',
            'bottom_tool_id': 'FMA-03-35-T08',
            'uv_assy_stage_id': 'FMA-03-35-T09',
        }
    }

    if model not in tool_ids:
        return JsonResponse({'error': 'Invalid model'}, status=400)

    return JsonResponse(tool_ids[model])





from django.http import JsonResponse

def get_part_numbers(request):
    model = request.GET.get('model')
    if not model:
        return JsonResponse({'error': 'Model parameter is required'}, status=400)

    part_numbers = {
        'P703': {
            'retainer_part_number': '42001878',
            'uv_clip_part_number': '42000829',
            'umbrella_part_number': '25094588'
        },
        'U704': {
            'retainer_part_number': '42001878',
            'uv_clip_part_number': '42000829',
            'umbrella_part_number': '25094588'
        },
        'FD': {
            'retainer_part_number': '42001878',
            'uv_clip_part_number': '42000829',
            'umbrella_part_number': '25094588'
        },
        'SA': {
            'retainer_part_number': '42001878',
            'uv_clip_part_number': '42000829',
            'umbrella_part_number': '25094588'
        },
        'Gnome': {
            'retainer_part_number': '42050758',
            'uv_clip_part_number': '42000829',
            'umbrella_part_number': '25094588'
        }
    }

    if model not in part_numbers:
        return JsonResponse({'error': 'Invalid model'}, status=400)

    return JsonResponse(part_numbers[model])