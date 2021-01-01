#Given a variable name and year-month-day-run as environmental variables download and merges the variable
################################################
listurls() {
	filename="$1"
	url="$2"
	wget -qO- $url | grep -Eoi '<a [^>]+>' | \
	grep -Eo 'href="[^\"]+"' | \
	grep -Eo $filename | \
	xargs -I {} echo "$url"{}
}
export -f listurls
#
get_and_extract_one() {
  url="$1"
  file=`basename $url | sed 's/\.bz2//g'`
  if [ ! -f "$file" ]; then
  	wget -t 2 -q -O - "$url" | bzip2 -dc > "$file"
  fi
}
export -f get_and_extract_one
##############################################
download_merge_2d_variable_ewam()
{
	filename="EWAM_${1}_${year}${month}${day}${run}_*.grib2"
	filename_grep="EWAM_${1}_${year}${month}${day}${run}_(.*).grib2.bz2"
	url="https://opendata.dwd.de/weather/maritime/wave_models/ewam/grib/${run}/${1,,}/"
	echo "folder: ${url}"
	echo "files: ${filename}"
	#
	if [ ! -f "${1}_${year}${month}${day}${run}_eur.nc" ]; then
		listurls $filename_grep $url | parallel -j 10 get_and_extract_one {}
		find ${filename} -empty -type f -delete # Remove empty files
		sleep 1
		cdo -f nc copy -mergetime ${filename} ${1}_${year}${month}${day}${run}_eur.nc
		rm ${filename}
	fi
}
export -f download_merge_2d_variable_ewam