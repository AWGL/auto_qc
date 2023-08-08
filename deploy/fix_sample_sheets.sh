cat SampleSheet.csv | sed 's/Name$ge/pipelineName=germline_enrichment_nextflow;pipelineVersion=master/' | sed 's/Name$SA/pipelineName=SomaticAmplicon;pipelineVersion=master/' | sed 's/NGHS101X/NGHS-101X/' | sed 's/NGHS102X/NGHS-102X/' | sed 's/ref/referral/' | sed 's/%/;/g' | sed 's/\$/=/g' > SampleSheet_fixed.csv

mv SampleSheet_fixed.csv SampleSheet.csv

