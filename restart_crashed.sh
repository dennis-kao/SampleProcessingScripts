for f in `ls bcbio.array.pbs.o*-*`; do
	echo ${f};
	yaml=`head -n10 ${f} | grep "Using input YAML configuration" | awk -F' ' '{print $NF}'`
	familyID=`dirname "$(dirname "${yaml}")"`;
	if tail $f | grep --quiet -i "error"; then
		echo "${familyID} crashed. Relaunching ${f} with $(qsub ~/cre/bcbio.pbs -v project=${familyID})";
		mv ${f} error_${f}; #rename log file so it doesn't get picked up in successive restart_crashed.sh calls
	fi;
done
