#!/bin/bash

usage () {
    cat <<__EOF__
usage: $(basename "$0") [-hlp] [-u user] [-X args] [-d args]
  -h        print this help text
  -l        print list of files to download
  -p        prompt for password
  -u user   download as a different user
  -X args   extra arguments to pass to xargs
  -d args   extra arguments to pass to the download program

__EOF__
}

hostname=dataportal.eso.org
username=anonymous
anonymous=
xargsopts=
download_opts="--"
prompt=
list=
while getopts hlpu:xX:d: option
do
    case $option in
	h) usage; exit ;;
	l) list=yes ;;
	p) prompt=yes ;;
	u) prompt=yes; username="$OPTARG" ;;
	X) xargsopts="$OPTARG" ;;
	d) download_opts="$OPTARG";;
	?) usage; exit 2 ;;
    esac
done

if [ "$username" = "anonymous" ]; then
    anonymous=yes
fi

if [ -z "$xargsopts" ]; then
    #no xargs option specified, we ensure that only one url
    #after the other will be used
    xargsopts='-L 1'
fi

netrc=$HOME/.netrc
if [ -z "$anonymous" ] && [ -z "$prompt" ]; then
    # take password (and user) from netrc if no -p option
    if [ -f "$netrc" ] && [ -r "$netrc" ]; then
	grep -ir "$hostname" "$netrc" > /dev/null
	if [ $? -ne 0 ]; then
            #no entry for $hostname, user is prompted for password
            echo "A .netrc is available but there is no entry for $hostname, add an entry as follows if you want to use it:"
            echo "machine $hostname login anonymous password _yourpassword_"
            prompt="yes"
	fi
    else
	prompt="yes"
    fi
fi

if [ -n "$prompt" ] && [ -z "$list" ]; then
    trap 'stty echo 2>/dev/null; echo "Cancelled."; exit 1' INT HUP TERM
    stty -echo 2>/dev/null
    printf 'Password: '
    read -r password
    echo ''
    stty echo 2>/dev/null
    escaped_password=${password//\%/\%25}
    auth_check=$(wget -O - --post-data "username=$username&password=$escaped_password" --server-response --no-check-certificate "https://www.eso.org/sso/oidc/accessToken?grant_type=password&client_id=clientid" 2>&1 | awk '/^  HTTP/{print $2}')
    if [ ! "$auth_check" -eq 200 ]
    then
        echo 'Invalid password!'
        exit 1
    fi
fi

# use a tempfile to which only user has access 
tempfile=$(mktemp /tmp/dl.XXXXXXXX 2>/dev/null)
test "$tempfile" -a -f "$tempfile" || {
    tempfile=/tmp/dl.$$
    ( umask 077 && : >$tempfile )
}
trap 'rm -f $tempfile' EXIT INT HUP TERM

echo "auth_no_challenge=on" > "$tempfile"
# older OSs do not seem to include the required CA certificates for ESO
echo "check_certificate=off" >> "$tempfile"
echo "content_disposition=on" >> "$tempfile"
if [ -z "$anonymous" ] && [ -n "$prompt" ]; then
    echo "http_user=$username" >> "$tempfile"
    echo "http_password=$password" >> "$tempfile"
fi
WGETRC=$tempfile; export WGETRC

unset password

if [ -n "$list" ]; then
    cat
else
    xargs "$xargsopts" wget "$download_opts"
fi <<'__EOF__'
https://archive.eso.org/downloadportalapi/readme/8da416fc-0450-448a-9219-45051ea72b56
https://archive.eso.org/downloadportalapi/calibrationxml/8da416fc-0450-448a-9219-45051ea72b56/GRAVI.2022-02-28T04:26:58.272_raw2raw.xml
https://archive.eso.org/downloadportalapi/calibrationxml/8da416fc-0450-448a-9219-45051ea72b56/GRAVI.2022-02-28T04:35:01.292_raw2raw.xml
https://dataportal.eso.org/dataPortal/file/GRAVI.2022-02-28T10:16:11.220
https://dataportal.eso.org/dataPortal/file/GRAVI.2022-02-28T12:38:21.655
https://dataportal.eso.org/dataPortal/file/M.GRAVITY.2020-06-10T12:25:23.506
https://dataportal.eso.org/dataPortal/file/GRAVI.2022-02-28T13:04:48.721
https://dataportal.eso.org/dataPortal/file/M.GRAVITY.2017-03-29T11:53:36.950
https://dataportal.eso.org/dataPortal/file/GRAVI.2022-02-28T04:26:58.272
https://dataportal.eso.org/dataPortal/file/M.GRAVITY.2020-06-10T12:25:40.913
https://dataportal.eso.org/dataPortal/file/GRAVI.2022-02-28T12:33:33.643
https://dataportal.eso.org/dataPortal/file/GRAVI.2022-02-28T12:54:30.695
https://dataportal.eso.org/dataPortal/file/GRAVI.2022-02-28T12:31:54.639
https://dataportal.eso.org/dataPortal/file/GRAVI.2022-02-28T12:47:45.679
https://dataportal.eso.org/dataPortal/file/GRAVI.2022-02-28T12:43:30.668
https://dataportal.eso.org/dataPortal/file/GRAVI.2022-02-28T04:36:55.297
https://dataportal.eso.org/dataPortal/file/M.GRAVITY.2020-06-10T12:25:42.416
https://dataportal.eso.org/dataPortal/file/GRAVI.2022-02-28T04:35:01.292
https://dataportal.eso.org/dataPortal/file/GRAVI.2022-02-28T12:57:57.705
https://dataportal.eso.org/dataPortal/file/GRAVI.2022-02-28T12:34:42.646
https://dataportal.eso.org/dataPortal/file/GRAVI.2022-02-28T12:37:00.651
https://dataportal.eso.org/dataPortal/file/M.GRAVITY.2026-01-27T09:58:00.133
https://dataportal.eso.org/dataPortal/file/GRAVI.2022-02-28T12:51:09.687
https://dataportal.eso.org/dataPortal/file/GRAVI.2022-02-28T13:01:21.713
https://dataportal.eso.org/dataPortal/file/GRAVI.2022-02-28T12:35:51.649
https://dataportal.eso.org/dataPortal/file/M.GRAVITY.2020-06-10T12:25:26.860
https://dataportal.eso.org/dataPortal/file/GRAVI.2022-02-28T04:28:52.277
__EOF__
