import csv
from ..models import *
from django.db.models import Avg, Min, FloatField, IntegerField, DecimalField
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime

# Assays and colours dict - current ones only
assay_colours = {
        'FastWGS': 'orange', 
        'IlluminaTruSightCancer':'olive', 
        'NGHS-101X': 'cyan', 
        'NGHS-102X':'coral', 
        'NonacusFH': 'violet', 
        'NonocusWES38': 'green', 
        'TSO500_DNA': 'lavender', 
        'TSO500_RNA': 'lime', 
        'WGS':'sienna', 
        'ctDNA': 'yellow',
    }

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

            try:
                if is_per_sample:
                    # Try different ways to query for per-sample metrics
                    try:
                        # First attempt with sample_analysis
                        model_objs = model_class.objects.filter(sample_analysis__sample__sample_id=sample.sample.sample_id)
                        if model_objs.exists():
                            data_models.add((label, model_class))
                        continue
                    except Exception as e:
                        pass
                        
                    try:
                        # Second attempt with sample
                        model_objs = model_class.objects.filter(sample__sample_id=sample.sample.sample_id)
                        if model_objs.exists():
                            data_models.add((label, model_class))
                        continue
                    except Exception as e:
                        pass

                else:
                    # Try different ways to query for run-level metrics
                    try:
                        # First attempt with run
                        model_objs = model_class.objects.filter(run__run_id=sample.run.run_id)
                        if model_objs.exists():
                            data_models.add((label, model_class))
                        continue
                    except Exception as e:
                        pass
                        
                    try:
                        # Second attempt with run_analysis
                        model_objs = model_class.objects.filter(run_analysis__run__run_id=sample.run.run_id)
                        if model_objs.exists():
                            data_models.add((label, model_class))
                        continue
                    except Exception as e:
                        pass
                
            except Exception as e:
                # Just continue to the next model
                continue
    return data_models


def return_data_fields(models):
    fields_to_remove = ['id', 'run', 'sample_analysis', 'sample', 'pipeline', 'analysis_type', 'worksheet']

    numeric_field_names = [
        "signoff_date",
    ]

    for model_name, value in models.items():
        model, is_per_sample = value
        for field in model._meta.get_fields():
            if field.name not in fields_to_remove:
                if isinstance(field, (IntegerField, FloatField, DecimalField)):
                    if is_per_sample:
                        model_field = f"{model_name}_{field.name}"
                    else:
                        model_field = f"{model_name}_{field.name}_run_avg"
                    numeric_field_names.append(model_field)
    
    return numeric_field_names


def write_wgs_data(writer, samples, data_models):
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
    if writer:
        writer.writerow(header_fields)

    data = []

    # Write data rows for each sample
    for sample in samples:
        try:
            # Base sample information
            try:
                run_analysis = RunAnalysis.objects.filter(run=sample.run).first()

            except Exception as e:
                pass        

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
                        except Exception as e:
                            pass
                        try:
                            metrics = model_class.objects.filter(sample=sample.sample).first()
                        except Exception as e:
                            pass

                    else:
                        try:
                            metrics = get_all_field_averages(model_class.objects.filter(run=sample.run))
                        except Exception as e:
                            pass
                        try:
                            metrics = get_all_field_averages(model_class.objects.filter(run_analysis__run=sample.run))
                        except Exception as e:
                            pass

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
                    # Add empty values for this model's fields
                    row_data.extend([''] * len(model_fields))
            
            # Write the complete row
            if writer:
                writer.writerow(row_data)
            
            data.append(row_data)

        except Exception as e:
            print(f"Error processing sample {sample.sample.sample_id}: {str(e)}")
            continue
    
    df = pd.DataFrame(data, columns=header_fields)
    return df


def get_plottable_cols(df):
    # drop NTC for plotting purposes
    df = df[~df['sample_id'].str.contains('NTC', na=False)]
    
    df = df.apply(pd.to_numeric, errors='ignore').astype('float64', errors='ignore')
    
    #convert sign-off date to datetime
    df['signoff_date'] = pd.to_datetime(df['signoff_date'])

    print(f"column dtypes: {df.dtypes}")
    print(f"df {df}")
    
    # Get numeric columns only
    numeric_cols = df.select_dtypes(include=[np.number, 'datetime']).columns.tolist()
    print(f"numeric cols: {numeric_cols}")
    
    if len(numeric_cols) < 2:
        raise ValueError("DataFrame must have at least 2 numeric columns for plotting")

    return numeric_cols


def trim_field_name(field_name):
    """
    Input:
    The name of a field tagged with a data model name (e.g. "DragenCNVMetrics_number_of_deletions")

    Returns:
    The name of the data field with the model name removed (e.g. "number of delections")
    
    """
    for key in data_models_dict:
        if field_name and field_name.startswith(f"{key}_"):
            return field_name.replace(f"{key}_", "")
    return "signoff_date"


def plotly_dashboard(df, selected_x, selected_y):
    """
    Interactive plot that take 
    
    Returns:
    plotly.graph_objects.Figure: Interactive plotly figure
    """
    assay_colour = df["assay_type"].map(assay_colours)
    
    trimmed_x = trim_field_name(selected_x)
    trimmed_y = trim_field_name(selected_y)
    
    title = f"{trimmed_y} vs {trimmed_x} for {len(df)} samples"
    
    # Create figure
    fig = go.Figure()
    
    for assay, group in df.groupby("assay_type"):
        fig.add_trace(go.Scatter(
            x=group[selected_x],
            y=group[selected_y],
            text=group['sample_id'],
            hovertemplate=
            "<b>Sample ID:</b> %{text}<br>"+
            "<b>%{xaxis.title.text}:</b> %{x}<br>"+
            "<b>%{yaxis.title.text}:</b> %{y}",
            name=assay,
            mode='markers',
            ))
    
    fig.update_layout(
        legend_title_text="Assay",
        title=title,
        height=700,
        )
    
    fig.update_xaxes(title_text=trimmed_x)
    fig.update_yaxes(title_text=trimmed_y)
    
    return fig