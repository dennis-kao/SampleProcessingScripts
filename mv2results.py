#!/usr/bin/env python3

#mv2results.py
#Dennis Kao
#CCM, 2019-01
#Description: Moves sample files produced from cre/crg/crt-bcbio pipeline to HPF storage
#Usage: mv2results.py -src=/path/to/bcbio/proj/1475N
#Args:
#	src - directory containing files to be moved

#Key features:
#	1. Circumvent issue of not being able to move directories from a personal largeprojects directory to dccforge storage by copying them
#	2. Determines results destination path from project id (folder name)
#	2. Copying over old vcfs from an old bcbio run if there is a folder in the old project named old_vcfs 
#	3. Setting appropriate permissions across all moved files
#	4. Prints path of input files to be deleted, path of moved bams and path of project directory
#	5. Moves old bcbio run in to the appropriate monthly trash directory
#	6. Copies over old reports from older bcbio runs

#System/Shell requirements:
#	df -b
#	chmod g+w -R

import os
import argparse
import shutil
import subprocess
import re
from datetime import datetime

def mkdir(dir_path, mode=0o775):
	if os.path.exists(dir_path):
		print('%s already exists, have you checked for this condition beforehand? Exiting.' % dir_path)
		exit(5)

	os.mkdir(dir_path) #mode parameter not interpreted correctly on HPC's centOS
	os.chmod(dir_path, mode) #so explicitly set permissions using this method call

def list_files(path, extension=""):
	files = {f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))}
	if extension:
		return {f for f in files if f.endswith(extension)}
	else:
		return files

def trash(project_dir):

	#Moves a bcbio run to the appropriate "monthly" trash

	trash_path = "/hpf/largeprojects/ccm_dccforge/dccforge/trash/"
	monthly_trash = os.path.join(trash_path, datetime.now().strftime("%Y-%m"))
	proj = os.path.basename(project_dir)

	if os.path.exists(os.path.join(monthly_trash, proj)):
		print("Cannot trash %s, it already exists in the trash directory: %s", (project_dir, monthly_trash))
		exit(4)

	if not os.path.exists(monthly_trash):
		mkdir(monthly_trash)

	shutil.move(project_dir, monthly_trash)

	print('Sucessfully moved old %s to trash directory: %s' % (proj, monthly_trash))

def safe_rm(path):
	
	# Deletes a directory such that the source of symlinks are not recursively removed

	def find_symlinks(path):
		symlinks = []

		for dirpath, dirnames, filenames in os.walk(path):
			for name in filenames:
				file_path = os.path.join(dirpath, name)
				if os.path.islink(file_path):
					symlinks.append(file_path)

			for name in dirnames:
				dir_path = os.path.join(dirpath, name)
				if os.path.islink(dir_path):
					symlinks.append(dir_path)

		return symlinks

	symlinks = find_symlinks(path)

	print('Delete these input files: ')

	for link in symlinks:
		print(os.path.abspath(link))
		os.unlink(link)

	shutil.rmtree(path)

	print('Safely deleted %s and it\'s symlinks: ' % path)
	for link in symlinks:
		print(link)

def print_excel_values(path):

	bams = list_files(path, ".bam")

	print('Enter these values in to the Excel sheet:')

	for bam in bams:
		print(path)
	
	for bam in bams:
		full_bam_path = os.path.join(path, bam)
		print(full_bam_path)

def move(src, dest, proj):

	#Make the directory for the project. Move files, copy folders.
	#Folders can only be copied and cannot be moved (from personal largeprojects directories to the largeprojects/ccm_dccforge/dccforge/results)
	#This is due to a limitation in our HPC systems, it involves the way quotas are calculated

	restricted_dirs = ["input", ]

	dest_dir = os.path.join(dest, proj)
	mkdir(dest_dir)

	#move src files/folders
	files = list_files(src)
	dirs = {f for f in os.listdir(src) if os.path.isdir(os.path.join(src, f))}

	for f in files:
		src_path = os.path.join(src, f)
		shutil.move(src_path, dest_dir)
	
	for f in dirs:
		if f not in restricted_dirs:
			src_path = os.path.join(src, f)
			new_dest_dir = os.path.join(dest_dir, f)
			shutil.copytree(src_path, new_dest_dir)

	chmod_out = subprocess.check_output(['chmod', 'g+w', '-R', dest_dir]).decode('utf-8')
	if chmod_out:
		print("Running chmod g+w -R on %s may not have run successfully. Check the subprocess output:" % dest_dir)
		print(chmod_out)
	else:
		print("chmod g+w -R ran successfully on %s" % dest_dir)

	print("Successfully moved Project %s from %s to %s" % (proj, src, dest_dir))

def determine_dest_parent_path(src, results_path="/hpf/largeprojects/ccm_dccforge/dccforge/results/"):
	proj = os.path.basename(src)
	first_char = proj[0]
	last_char = proj[-1]

	if first_char.isnumeric() and last_char.isalpha():
		#get the numeric substring
		proj = re.split('[a-zA-Z]+', proj)[0]
	
	if first_char.isnumeric():
		dest_dir = "0x" if len(proj) <= 2 else "%sx" % proj[:-2]
	else:
		dest_dir =  "%cx" % first_char.upper()

	return os.path.join(results_path, dest_dir)

def check_and_move(src, explicit_dest, skip_sample_check=False):

	#Checks for sufficient space, old bcbio runs
	#If there is an old bcbio run, check that the samples are a subset of the new bcbio run before moving
	#If there is an old bcbio run, copy over reports and the old_vcfs folder is there is one
	
	def enough_space(src, dest):
		def get_size(path):
			#Returns size in bytes
			return int(subprocess.check_output(['du', '-sb', path]).split()[0].decode('utf-8')) 

		src_size = get_size(src)
		dest_free_space = shutil.disk_usage(dest)[2]
		return src_size < dest_free_space

	if not os.path.isdir(src):
		print("%s is not a valid directory." % src)
		exit(1)
    
	real_src = os.path.realpath(src)
	proj = os.path.basename(real_src)
	dest_parent_path = determine_dest_parent_path(real_src) if not explicit_dest else explicit_dest
	dest_dir = os.path.join(dest_parent_path, proj)

	if not enough_space(real_src, dest_parent_path):
		print("Storage directory has insufficent space. Check using du and df.")
		exit(2)

	if os.path.exists(dest_dir):
		print("Project %s already exists in the results directory. Attempting to resolve." % proj)

		dest_vcfs = list_files(dest_dir, ".vcf")
		dest_bams = list_files(dest_dir, ".bam")
		src_vcfs = list_files(real_src, ".vcf")
		src_bams = list_files(real_src, ".bam")

		src_is_superset = src_bams.issuperset(dest_bams) and src_vcfs.issuperset(dest_vcfs)

		if skip_sample_check or src_is_superset:

			if src_is_superset:
				print("src vcf\'s and bam\'s are a superset of the existing project\'s. Attempting to store the old project's old_vcfs folder and reports.")
			else:
				print('--skip_sample_check parameter applied and src vcf\'s and bam\'s are NOT a superset of the existing project\'s. I hope you know what you are doing!')

			old_vcfs = os.path.join(dest_dir, "old_vcfs")
			old_reports = list_files(dest_dir, ".csv")
			new_reports = list_files(real_src, ".csv")

			if os.path.exists(old_vcfs):
				print('Detected an old_vcfs folder in the previous bcbio run. Copying folder to new project.')
				src_old_vcfs_path = os.path.join(real_src, "old_vcfs")
				if not os.path.exists(src_old_vcfs_path):
					shutil.copytree(old_vcfs, src_old_vcfs_path)
				else:
					print('There is already an old_vcfs folder in the source directory. Please manually copy over the vcf files and re-run the script.')
					exit(6)

			for f in old_reports:
				if f not in new_reports:
					print('Copying over old report %s to src' % f)
					report_path = os.path.join(dest_dir, f)
					shutil.copy2(report_path, real_src)
				else:
					print('Detected a report in the old run with the same name as a report in the new run: %s. Not copying this over.' % f)

			trash(dest_dir)

		else:
			print('Project on results directory contains samples (vcfs & bams) which are either named differently from src and/or are not present in the new project at all. Move over the files manually and resolve this issue.')
			print("Results bams: %s" % str(dest_bams))
			print("Results vcfs: %s" % str(dest_vcfs))
			print("Source bams: %s" % str(src_bams))
			print("Source vcfs: %s" % str(src_vcfs))
			exit(3)

	move(real_src, dest_parent_path, proj)
	safe_rm(real_src)

	print_excel_values(dest_dir)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Moves a cre/crg/crt-bcbio run to the HPC results directory')
	parser.add_argument('-src', required=True, help='Source directory containing files from a finished bcbio run')
	parser.add_argument('-dest', type=str, help='Explicity move the src files into this directory, don\'t use the built in function to automatically determine this. E.g. /results/4x/')
	parser.add_argument('--skip_sample_check', action='store_true', help='Override checks for an older bcbio run')
	args = parser.parse_args()
	
	check_and_move(args.src, args.dest, args.skip_sample_check)
