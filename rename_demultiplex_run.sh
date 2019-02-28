cd Data/Intensities/BaseCalls

read_path=`find $(pwd) -name '*.fastq.gz' | grep -v Undetermined`
basecalls_dir=`pwd`

for f in $read_path; do
	sample_dir=`dirname $f`
	fam_id=`basename $(dirname ${sample_dir})`

	cd $sample_dir

	for fastq in `ls *.fastq.gz`; do

		#add family id
		#remove a single rightmost occurence of _S[0-9]+ 
		#rename extension to .fq.gz
		new_name=`echo ${fam_id}_${fastq} | rev | sed -E 's/[0-9]+S_//1' | rev \
		| sed 's/.fastq.gz/.fq.gz/1'`

		mv $fastq $new_name
	done

	cd $basecalls_dir
done