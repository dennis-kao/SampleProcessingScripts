#!/usr/bin/env python3

'''
	Rename FASTQ files for a cre/crg/crt-bcbio run given a tab delimited plain-text file with the following format:

	familyID	sampleID	path/to/fastq_paired_R1_XXX.fastq.gz
'''

import sys
import os

mapping = sys.argv[1]
rename_flag = True if len(sys.argv) == 3 and sys.argv[2] == "rename" else False

def rename_fastq_files(read1, read2, sampleID):
	os.rename(read1, "%s_1.fq.gz" % sampleID)
	os.rename(read2, "%s_2.fq.gz" % sampleID)

if __name__ == "__main__":
	names = []
	with open(mapping, "r") as f:
		for line in f:
			familyID, individualID, read = line.strip("\n").split("\t")
			names.append((familyID, individualID, read))

	for familyID, individualID, read in names:
		familyID = familyID.replace("_", "-")
		individualID = individualID.replace("_", "-")
		sampleID = "%s_%s" % (familyID, individualID)
		
		if "_R1_" in read:
			read1 = read
			read2 = read.replace("_R1_", "_R2_", 1)	
		elif "_R2_" in read:
			read2 = read
			read1 = read.replace("_R2_", "_R1_", 1)
		else:
			raise ValueError("Could not detect a read number in the FASTQ file. Exiting.")

		print("\t".join([sampleID, read1, read2]))

		if rename_flag:
			rename_fastq_files(read1, read2, sampleID)