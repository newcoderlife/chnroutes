/system script
add name=noncn policy=ftp,reboot,read,write,policy,test,winbox,password,sniff,sensitive source="{
    /tool fetch url=\"https://raw.githubusercontent.com/newcoderlife/chnroutes/refs/heads/master/noncn.rsc\" mode=http dst-path=/noncn.rsc;
    /import file-name=noncn.rsc;
}"

/system scheduler
add name=noncn start-time=01:00:00 interval=1d on-event=noncn