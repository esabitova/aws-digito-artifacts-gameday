# Installing requirements on cloud desktop(pip is not allowed on cloud desktop)
* brazil-bootstrap --environmentRoot ~/python --environmentType runtime --flavor DEV.STD.PTHREAD --packages Coverage-4.x,Python-setuptools-default,Python-default,Boto3-1.x PATH=~/python/bin:$PATH --force
* export PATH=~/python/bin:$PATH
