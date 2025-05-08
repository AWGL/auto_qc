import csv
from ..models import *
from django.db.models import Avg, FloatField, IntegerField, DecimalField


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
}


def get_all_field_averages(queryset):
    # Get the model class from the queryset
    model_class = queryset.model
    
    # Get all numeric fields
    numeric_fields = [field.name for field in model_class._meta.get_fields() 
                     if isinstance(field, (IntegerField, FloatField, DecimalField))]
    
    # Build the aggregate dictionary dynamically
    aggregates = {f"{field}_avg": Avg(field) for field in numeric_fields}
    
    # Return the averages for the specific queryset
    return queryset.aggregate(**aggregates)


def return_data_models(samples):
    """
    Determine which data models are available for the given samples
    Returns a set of model names that have data for at least one sample
    """
    data_models = set()
    
    for sample in samples:
        for label, model_info in data_models_dict.items():
            model_class, is_per_sample = model_info
            
            try:
                if is_per_sample:
                    model_objs = model_class.objects.filter(sample_analysis=sample)
                else:
                    model_objs = model_class.objects.filter(run=sample.run)
                
                if model_objs.exists():
                    print(f'INFO: We have {label} for {sample.sample.sample_id}')
                    data_models.add(label)
                    
            except Exception as e:
                # Log error and continue with next sample
                print(f"Error checking {label} for sample {sample.sample.sample_id}: {str(e)}")
                continue
    
    print(f"Data present for these models: {data_models}")
    return data_models


def write_wgs_data(writer, samples, assay_types, data_models):
    """
    Write a CSV with all available data for the selected samples
    """
    # Fields to exclude from models
    fields_to_remove = ['id', 'run', 'sample_analysis']
    
    # Start with base fields for each row
    base_fields = [
        'run_id',
        'instrument',
        'pipeline',
        'assay_type',
        'sample_id',
        'pass_fail'
    ]
    
    # Build complete header row with fields from all available data models
    header_fields = base_fields.copy()
    model_fields_map = {}  # Store fields for each model for later use
    
    for model_name in data_models:
        model_class = data_models_dict[model_name][0]
        model_fields = []
        
        for field in model_class._meta.fields:
            if field.name not in fields_to_remove:
                field_label = f"{model_name}_{field.name}"
                model_fields.append(field.name)
                header_fields.append(field_label)
        
        model_fields_map[model_name] = model_fields
    
    # Write the header row
    writer.writerow(header_fields)
    
    # Write data rows for each sample
    for sample in samples:
        try:
            # Base sample information
            row_data = [
                sample.run.run_id,
                sample.run.instrument.instrument_id if hasattr(sample.run, 'instrument') else '',
                sample.pipeline if hasattr(sample, 'pipeline') else '',
                sample.analysis_type.analysis_type_id,
                str(sample.sample.sample_id),
                getattr(sample, 'pass_fail', '') if hasattr(sample, 'pass_fail') else ''
            ]
            
            # Add data from each model
            for model_name in data_models:
                model_class, is_per_sample = data_models_dict[model_name]
                model_fields = model_fields_map[model_name]
                
                try:
                    if is_per_sample:
                        metrics = model_class.objects.filter(sample_analysis=sample).first()
                    else:
                        metrics = model_class.objects.filter(run=sample.run).first()
                        # metrics = get_all_field_averages(query)
                    # Add each field value to the row
                    if metrics:
                        for field_name in model_fields:
                            field_value = getattr(metrics, field_name, '')
                            row_data.append(field_value)
                    else:
                        # Add empty values for this model's fields
                        row_data.extend([''] * len(model_fields))
                        
                except Exception as e:
                    print(f"Error getting {model_name} data for sample {sample.sample.sample_id}: {str(e)}")
                    # Add empty values for this model's fields
                    row_data.extend([''] * len(model_fields))
            
            # Write the complete row
            writer.writerow(row_data)
            
        except Exception as e:
            print(f"Error processing sample {sample.sample.sample_id}: {str(e)}")
            continue
    
    return samples