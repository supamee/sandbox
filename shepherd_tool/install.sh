#!/bin/bash
FILE=$HOME/shepherd/data/device.json
if [ -f "$FILE" ]; then
    echo "$FILE exists."
    python3 install.py $FILE $HOME
    source $HOME/shepherd/env/bin/activate
    pip install -r requirements.txt
    pip install matplotlib
    pip install pytz
    echo "done with pip installs"
    rm $HOME/.oh-my-zsh/custom/strive.zsh
    cp goat.zsh $HOME/.oh-my-zsh/custom/goat.zsh
    echo "fixed zsh"
    cp -r ../shepherd_tool $HOME/shepherd
    echo "applying shepherd patches"
    cp update_files/tcp_server.py $HOME/shepherd/server/tcp_server.py # issue with a wifi key
    sudo cp update_files/run_boot $HOME/shepherd/bin/run_boot # missing ampersan 
    cp update_files/mesh_device_manager.py $HOME/shepherd/server/mesh_device_manager.py # update sentry with shepherd time
    cp update_files/bleet__init__.py $HOME/shepherd/bleet/__init__.py
    echo "copied data to shepherd folder"
    # sudo cp *cron /etc/cron.d/
    # echo "copied cron job"
    # rm *cron
    cd $HOME/shepherd/shepherd_tool
    rm requirements.txt
    rm install*
    rm -r update_files
    rm -r __pycache__
    rm fetch_cron_template
    rm sand.py
    rm goat.zsh
    
else 
    echo "$FILE does not exist."
    # python3 install.py test.json
fi