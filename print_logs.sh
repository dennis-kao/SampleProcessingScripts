LOG_REGEX="bcbio*"

if [ "$1" == "array" ]; then
	LOG_REGEX="bcbio.array.pbs.o*-*"
fi

for f in `ls ${LOG_REGEX}`; do
	echo ${f};
	head -n10 ${f} | grep "Using input YAML configuration" | awk -F' ' '{print $NF}' | awk -F'/' '{print $(NF-2)}';
	tail ${f};
	echo -e "";
done
