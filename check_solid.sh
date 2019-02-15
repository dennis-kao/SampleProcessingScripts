for f in `ls *.bam`; do
	if [[ -z $(samtools view -H ${f} | grep -i "PL:solid") ]]; then
		echo "${f} not solid!"
	else
		echo "${f} SOLID :("
	fi
done
