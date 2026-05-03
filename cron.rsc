# Fetch the generated route script and import it every 12 hours.
/system script
add dont-require-permissions=no name=noncn owner=admin policy=ftp,read,write,policy,test source="{\
    \n    /tool fetch url=https://github.com/newcoderlife/chnroutes/releases/latest/download/noncn.rsc check-certificate=yes-without-crl dst-path=noncn.rsc.tmp;\
    \n    /import file-name=noncn.rsc.tmp;\
    \n    /file remove noncn.rsc.tmp;\
    \n}"
/system scheduler
add interval=12h name=noncn on-event=noncn policy=ftp,read,write,policy,test start-date=2024-10-01 start-time=01:00:00
