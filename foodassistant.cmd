universe = vanilla
getenv = true

executable = foodassistant.sh
#Requirements  = (GPUs_DeviceName == "NVIDIA RTX A6000")
#Requirements = (Machine == "isye-hpc0460.isye.gatech.edu")
log=logs/$(cluster).$(Process).log
output=logs/$(cluster).$(Process).out
error=logs/$(cluster).$(Process).error
notification=error
notification=complete
notify_user=mmoradi6@gatech.edu
request_cpus=1
periodic_release  = (ExitBySignal == False) && (ExitCode != 0)
queue