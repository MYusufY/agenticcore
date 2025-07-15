#!/bin/sh
sudo echo -e "sleep 2\necho -e \"i: /usr/local/share/pixmaps/acore.png\nt: Agent\nc: sudo python3 /ace/LocalAgent/gui/main.py\" >> /usr/local/tce.icons\npkill wbar; wbar --bpress --pos top-right --zoomf 2 --isize 45 --idist 8&" > /home/tc/.X.d/appconf
sudo chmod +x /home/tc/.X.d/appconf
