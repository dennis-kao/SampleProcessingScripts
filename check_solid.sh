for f in `ls *.bam`; do
	if [[ -z $(samtools view -H ${f} | grep -i "solid") ]]; then
		echo "${f} not solid!"
	else
		echo "${f} SOLID :("
	fi
done
