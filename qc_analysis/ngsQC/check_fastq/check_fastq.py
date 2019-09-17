import sys
import glob
import os
import pandas
import openpyxl
from xml.etree.ElementTree import ElementTree
import subprocess
import numpy

runid=sys.argv[1]




'''
check number of sample folders match number of samples in samplesheet
'''

#find the number of folders /data/archive/fastq/runid/Data folder
num_folders=0
sample_folders=glob.glob("/data/archive/fastq/"+runid+"/Data/*")
for i in sample_folders:
    num_folders=num_folders+1


#Find the number of samples in the sample sheet
worksheet= pandas.read_csv("/data/archive/fastq/"+runid+"/"+"SampleSheet.csv", sep=",",header=5, skiprows=range(1,13))
worksheet_2=worksheet["Sample_ID"]
num_of_samples=0
for i in worksheet_2:
    if (numpy.isnan(i)):
        print("is nan")
    else:
        num_of_samples=num_of_samples+1
        print(i)

#Does the number of sample folders equal the number of samples in the sample sheet
if num_folders!=num_of_samples:
    print("Fastq folders missing")
print(num_folders)
print(num_of_samples)



'''
check number of fastq.gz in each sample folder equals the number of lanes used multiplied by 2
'''


#Find the number of lanes used from RunParameters xml file
tree=ElementTree()
tree.parse("/data/archive/fastq/"+runid+"/RunParameters.xml")
root=tree.getroot()
num_lanes=root[1][5].text
predicted_num_fastq=int(num_lanes)*2


for i in sample_folders:
    sampleid=os.path.basename(i)


    #Find the number of fastq.gz in the sample folder
    fastq_list=glob.glob("/data/archive/fastq/"+runid+"/Data/"+sampleid+"/*.fastq.gz")
    num_fastq=0
    for i in fastq_list:
        out=os.path.basename(i)
        num_fastq=num_fastq+1
        
    #Does the number of fastq.gz equal the number of lanes used multiplied by 2
    if (num_fastq!= predicted_num_fastq):
        print("number of fastqs doesn't equal number of lanes*2")


    #check that the fastqs are not empty
    file_list= glob.glob("/data/archive/fastq/"+runid+"/Data/"+sampleid+"/*.fastq.gz")
    for file in file_list:
        if(os.stat(file).st_size==0):
            print(file + "is empty")



#check the validity of the fastQ file using validateFastQ script
subprocess.call(["./validateFastQ.sh"])
