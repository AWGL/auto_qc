cat SampleSheet.csv | sed 's/Name$ge/pipelineName=germline_enrichment_nextflow;pipelineVersion=master/' | sed 's/%/;/g' | sed 's/\$/=/g' > SampleSheet_fixed.csv

cat SampleSheet.csv | sed 's/Name$SA/pipelineName=SomaticAmplicon;pipelineVersion=master/' | sed 's/%/;/g' | sed 's/\$/=/g' | sed 's/panel=NGHS101X/panel=NGHS-101X/' | sed 's/NGHS102X/NGHS-102X/' | sed 's/ref=/referral=/' > SampleSheet_fixed2.csv

mv SampleSheet_fixed2.csv SampleSheet.csv

