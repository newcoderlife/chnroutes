# Add download script and run daily
/system script
add dont-require-permissions=no name=noncn owner=admin policy=ftp,reboot,read,write,policy,test,password,sniff,sensitive,romon source="{\
    \n    /tool fetch url=\\\"https://raw.githubusercontent.com/newcoderlife/chnroutes/refs/heads/master/noncn.rsc\\\" mode=http dst-path=/noncn.rsc;\
    \n    /import file-name=noncn.rsc;\
    \n}"
/system scheduler
add interval=12h name=noncn on-event=noncn policy=ftp,reboot,read,write,policy,test,password,sniff,sensitive,romon start-date=2024-10-01 start-time=01:00:00
