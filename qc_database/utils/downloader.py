import csv
from ..models import *
from django.db.models import Avg, Min, FloatField, IntegerField, DecimalField

# List of assays to show in form - current ones only
assays_to_show = [
    'FastWGS', 
    'IlluminaTruSightCancer', 
    'NGHS-101X', 
    'NGHS-102X', 
    'NonacusFH', 
    'NonocusWES38', 
    'TSO500_DNA', 
    'TSO500_RNA', 
    'WGS', 
    'ctDNA'
    ]

data_models_dict = {
    # "ModelName": [ModelName, per_sample_metrics_boolean] 
    "InteropRunQuality": [InteropRunQuality, False],
    "DragenAlignmentMetrics": [DragenAlignmentMetrics, True],
    "DragenVariantCallingMetrics": [DragenVariantCallingMetrics, True],
    "DragenRegionCoverageMetrics": [DragenRegionCoverageMetrics, True],
    "SampleHsMetrics": [SampleHsMetrics, True],
    "SampleFastqcData": [SampleFastqcData, True],
    "SampleDragenFastqcData": [SampleDragenFastqcData, True],
    "SampleDepthofCoverageMetrics": [SampleDepthofCoverageMetrics, True],
    "RunAnalysis": [RunAnalysis, False],
    "RelatednessQuality": [RelatednessQuality, False],
    "SampleAnalysis": [SampleAnalysis, True],
    "DuplicationMetrics": [DuplicationMetrics, True],
    "ContaminationMetrics": [ContaminationMetrics, True],
    "CalculatedSexMetrics": [CalculatedSexMetrics, True],
    "AlignmentMetrics": [AlignmentMetrics, True],
    "VariantCallingMetrics": [VariantCallingMetrics, True],
    "InsertMetrics": [InsertMetrics, True],
    "VCFVariantCount": [VCFVariantCount, True],
    "InteropIndexMetrics": [InteropIndexMetrics, True],
    "FusionContamination": [FusionContamination, True],
    "FusionAlignmentMetrics": [FusionAlignmentMetrics, True],
    "Tso500Reads": [Tso500Reads, True],
    "ctDNAReads": [ctDNAReads, True],
    "DragenPloidyMetrics": [DragenPloidyMetrics, True],
    "CustomCoverageMetrics": [CustomCoverageMetrics, True],
    "CNVMetrics": [CNVMetrics, True],
    "DragenCNVMetrics": [DragenCNVMetrics, True],
}


def get_all_field_averages(queryset):
    """
    Use on a queryset to return a dictionary with field names as keys 
    and average across all numeric fields as values. Min is returned
    for non-numeric fields
    Example usage : metrics = get_all_field_averages(<django_query>)
    """
    # Get the model class from the queryset
    model_class = queryset.model
    print(f"model class : {model_class}")

    # Get all numeric fields
    numeric_fields = [field.name for field in model_class._meta.get_fields() 
                     if isinstance(field, (IntegerField, FloatField, DecimalField))]
    # Get all non-numeric fields
    non_numeric_fields = [field.name for field in model_class._meta.get_fields() 
                     if not isinstance(field, (IntegerField, FloatField, DecimalField))]

    # Build the aggregate dictionaries dynamically
    aggregates_num = {f"{field}_avg": Avg(field) for field in numeric_fields}
    aggregates_non = {f"{field}_avg": Min(field) for field in non_numeric_fields}

    # Combine dictionaries
    aggregates_num.update(aggregates_non)

    # Return the averages for the specific queryset
    return queryset.aggregate(**aggregates_num)


def return_data_models(samples):
    """
    Determine which data models are available for the given samples
    Returns a set of model names that have data for at least one sample
    """
    data_models = set()
    
    for sample in samples:
        for label, model_info in data_models_dict.items():
            model_class, is_per_sample = model_info
            # print(f"  Checking model: {label}, is_per_sample: {is_per_sample}")

            try:
                if is_per_sample:
                    # Try different ways to query for per-sample metrics
                    try:
                        # First attempt with sample_analysis
                        model_objs = model_class.objects.filter(sample_analysis__sample__sample_id=sample.sample.sample_id)
                        if model_objs.exists():
                            # print(f"        Found data for {label} using sample_analysis_id")
                            data_models.add(label)
                        # else: 
                            # print(f"        Data not found for {label} using sample_analysis_id")
                        continue
                    except Exception as e:
                        pass
                        # print(f"        Error checking sample_analysis_id: {str(e)}")
                        
                    try:
                        # Second attempt with sample
                        model_objs = model_class.objects.filter(sample__sample_id=sample.sample.sample_id)
                        if model_objs.exists():
                            # print(f"        Found data for {label} using sample.sample_id")
                            data_models.add(label)
                        # else: 
                        #     print(f"        Data not found for {label} using sample.sample_id")
                        continue
                    except Exception as e:
                        pass
                        # print(f"        Error checking sample_id: {str(e)}")

                else:
                    # Try different ways to query for run-level metrics
                    try:
                        # First attempt with run
                        model_objs = model_class.objects.filter(run__run_id=sample.run.run_id)
                        if model_objs.exists():
                            # print(f"        Found data for {label} using run_id")
                            data_models.add(label)
                        # else:
                        #     print(f"        Data not found for {label} using run_id")
                        continue
                    except Exception as e:
                        pass
                        # print(f"        Error checking run: {str(e)}")
                        
                    try:
                        # Second attempt with run_analysis
                        model_objs = model_class.objects.filter(run_analysis__run__run_id=sample.run.run_id)
                        if model_objs.exists():
                            # print(f"        Found data for {label} using run_analysis")
                            data_models.add(label)
                        # else:
                        #     print(f"        Data not found for {label} using run_analysis")
                        continue
                    except Exception as e:
                        pass
                        # print(f"        Error checking run_analysis: {str(e)}")
                
            except Exception as e:
                # Just continue to the next model
                continue
    # print(f"Found available data models {data_models}")
    return data_models


def write_wgs_data(writer, samples, assay_types, data_models):
    """
    Write a CSV with all available data for the selected samples
    """
    # Fields to exclude from models
    fields_to_remove = ['id', 'run', 'sample_analysis', 'sample', 'pipeline', 'analysis_type', 'worksheet']
    
    # Start with base fields for each row
    base_fields = [
        'run_id',
        'instrument',
        'pipeline',
        'assay_type',
        'sample_id',
        'worksheet',
        'manual_approval',
        'signoff_date'
    ]
    
    # Build complete header row with fields from all available data models
    header_fields = base_fields.copy()
    model_fields_map = {}  # Store fields for each model for later use
    
    
    for model_name in data_models:
        model_class, is_per_sample = data_models_dict[model_name]
        model_fields_list = []
        
        for field in model_class._meta.fields:
            if field.name not in fields_to_remove:
                if is_per_sample:
                    field_label = f"{model_name}_{field.name}"
                else:
                    field_label = f"{model_name}_{field.name}_run_avg"
                model_fields_list.append(field.name)
                header_fields.append(field_label)
        
        model_fields_map[model_name] = model_fields_list
    
    # Write the header row
    writer.writerow(header_fields)
    
    # Write data rows for each sample
    for sample in samples:
        try:
            # Base sample information
            try:
                run_analysis = RunAnalysis.objects.filter(run=sample.run).first()
            except Exception as e:
                pass        
                # print(f"Error checking run_analysis: {str(e)}")
            row_data = [
                sample.run.run_id,
                sample.run.instrument.instrument_id if hasattr(sample.run, 'instrument') else '',
                sample.pipeline if hasattr(sample, 'pipeline') else '',
                sample.analysis_type.analysis_type_id,
                str(sample.sample.sample_id),
                sample.worksheet,
                run_analysis.manual_approval if hasattr(run_analysis, 'manual_approval') else '',
                run_analysis.signoff_date if hasattr(run_analysis, 'signoff_date') else ''
            ]
            
            # Add data from each model
            for model_name in data_models:
                model_class, is_per_sample = data_models_dict[model_name]
                model_fields = model_fields_map[model_name]
                
                try:
                    if is_per_sample:
                        try:
                            metrics = model_class.objects.filter(sample_analysis=sample).first()
                            # print(f"sample analysis metrics {metrics}")
                        except Exception as e:
                            pass
                            # print(f"Error checking sample_analysis: {str(e)}")
                        try:
                            metrics = model_class.objects.filter(sample=sample.sample).first()
                            # print(f"sample metrics {metrics}")
                        except Exception as e:
                            pass
                            # print(f"Error checking sample_id: {str(e)}")

                    else:
                        try:
                            metrics = get_all_field_averages(model_class.objects.filter(run=sample.run))
                            # print(f"run metrics = {metrics}")
                        except Exception as e:
                            pass
                            # print(f"Error checking sample_analysis_id: {str(e)}")
                        try:
                            metrics = get_all_field_averages(model_class.objects.filter(run_analysis__run=sample.run))
                            # print(f"run metrics = {metrics}")
                        except Exception as e:
                            pass
                            # print(f"Error checking sample_analysis_id: {str(e)}")
                        # metrics = get_all_field_averages(query)
                    # Add each field value to the row
                    
                    if metrics:
                        for field_name in model_fields:
                            if isinstance(metrics, dict):
                                field_value = metrics.get(f"{field_name}_avg", '')
                            else:
                                field_value = getattr(metrics, field_name, '')
                            row_data.append(field_value)
                    else:
                        # Add empty values for this model's fields
                        row_data.extend([''] * len(model_fields))
                        
                except Exception as e:
                    # print(f"Error getting {model_name} data for sample {sample.sample.sample_id}: {str(e)}")
                    # Add empty values for this model's fields
                    row_data.extend([''] * len(model_fields))
            
            # Write the complete row
            
            writer.writerow(row_data)
            # print(f"Sample {sample.sample.sample_id} data written to table")
        except Exception as e:
            print(f"Error processing sample {sample.sample.sample_id}: {str(e)}")
            continue
    
    return samples